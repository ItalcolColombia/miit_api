import uuid
from decimal import Decimal
from typing import List, Optional

from fastapi_pagination import Page, Params
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from core.exceptions.base_exception import BasedException
from core.exceptions.db_exception import DatabaseSQLAlchemyException
from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
from database.connection import DatabaseConfiguration
from database.models import Pesadas, Transacciones, SaldoSnapshotScada, VAlmMateriales
from repositories.pesadas_corte_repository import PesadasCorteRepository
from repositories.pesadas_repository import PesadasRepository
from repositories.transacciones_repository import TransaccionesRepository
from schemas.pesadas_corte_schema import PesadasCalculate, PesadasCorteCreate, PesadasRange, \
    PesadaCorteRetrieve
from schemas.pesadas_schema import PesadaResponse, PesadaCreate, PesadaUpdate, VPesadasAcumResponse
from schemas.transacciones_schema import TransaccionUpdate
from utils.logger_util import LoggerUtil
from utils.any_utils import AnyUtils
from core.config.context import current_user_id
from schemas.logs_auditoria_schema import LogsAuditoriaCreate
from utils.time_util import now_local

log = LoggerUtil()


async def _crear_snapshots_pesada(
    session: AsyncSession,
    pesada_id: int,
    tran_obj,
    saldo_anterior_origen: Decimal,
    saldo_nuevo_origen: Decimal,
    auditor=None
) -> List[SaldoSnapshotScada]:
    """
    Crea snapshots de saldo para una pesada.

    Para transacciones tipo Traslado, crea DOS snapshots:
    - Uno de SALIDA del origen (con los saldos recibidos de SCADA)
    - Uno de ENTRADA al destino (calculado internamente)

    Para Recibo y Despacho, crea UN solo snapshot (comportamiento original).

    Args:
        session: Sesión de base de datos
        pesada_id: ID de la pesada
        tran_obj: Objeto transacción ORM
        saldo_anterior_origen: Saldo anterior del origen (recibido de SCADA)
        saldo_nuevo_origen: Saldo nuevo del origen (recibido de SCADA)
        auditor: Auditor para registrar logs (opcional)

    Returns:
        Lista de objetos SaldoSnapshotScada creados
    """
    snapshots_creados = []
    material_id = getattr(tran_obj, 'material_id', None)
    tipo_tran = str(getattr(tran_obj, 'tipo', '') or '').strip().lower()

    # Snapshot del origen (siempre se crea)
    origen_id = getattr(tran_obj, 'origen_id', None)
    destino_id = getattr(tran_obj, 'destino_id', None)

    # Determinar almacenamiento para snapshot según tipo
    if tipo_tran == 'traslado':
        # Para traslado, el snapshot de origen usa origen_id
        almacenamiento_origen = origen_id
    elif tipo_tran == 'recibo':
        # Para recibo, el almacenamiento afectado es destino (o origen si no hay destino)
        almacenamiento_origen = destino_id or origen_id
    else:
        # Para despacho u otros, usar origen_id
        almacenamiento_origen = origen_id or destino_id

    # Crear snapshot de origen
    if almacenamiento_origen is not None:
        s_origen = SaldoSnapshotScada(
            pesada_id=int(pesada_id),
            almacenamiento_id=int(almacenamiento_origen),
            material_id=int(material_id) if material_id is not None else None,
            saldo_anterior=saldo_anterior_origen,
            saldo_nuevo=saldo_nuevo_origen,
            tipo_almacenamiento='ORIGEN'
        )
        session.add(s_origen)
        await session.flush()
        snapshots_creados.append(s_origen)

        # Auditoría del snapshot de origen
        if auditor is not None:
            try:
                audit_snap = LogsAuditoriaCreate(
                    entidad='saldo_snapshot_scada',
                    entidad_id=str(getattr(s_origen, 'id', None)),
                    accion='CREATE',
                    valor_anterior=None,
                    valor_nuevo=AnyUtils.serialize_orm_object(s_origen),
                    usuario_id=current_user_id.get()
                )
                await auditor.log_audit(audit_log_data=audit_snap)
            except Exception as e_aud:
                log.error(f"No se pudo registrar auditoría para snapshot origen: {e_aud}")

    # Para Traslado, crear también snapshot de destino (calculado)
    if tipo_tran == 'traslado' and destino_id is not None and origen_id is not None:
        try:
            # Calcular delta (lo que sale del origen)
            delta = saldo_anterior_origen - saldo_nuevo_origen  # positivo = salida

            # Obtener saldo actual del destino desde VAlmMateriales
            saldo_anterior_destino = Decimal('0')
            try:
                res = await session.execute(
                    select(VAlmMateriales).where(
                        VAlmMateriales.almacenamiento_id == int(destino_id),
                        VAlmMateriales.material_id == int(material_id) if material_id else True
                    )
                )
                vrow = res.scalar_one_or_none()
                if vrow is not None:
                    saldo_anterior_destino = Decimal(str(getattr(vrow, 'saldo', 0) or 0))
            except Exception as e_saldo:
                log.warning(f"No se pudo obtener saldo anterior del destino {destino_id}: {e_saldo}")

            # Saldo nuevo del destino = saldo anterior + lo que sale del origen
            saldo_nuevo_destino = saldo_anterior_destino + delta

            # Crear snapshot de destino
            s_destino = SaldoSnapshotScada(
                pesada_id=int(pesada_id),
                almacenamiento_id=int(destino_id),
                material_id=int(material_id) if material_id is not None else None,
                saldo_anterior=saldo_anterior_destino,
                saldo_nuevo=saldo_nuevo_destino,
                tipo_almacenamiento='DESTINO'
            )
            session.add(s_destino)
            await session.flush()
            snapshots_creados.append(s_destino)

            log.info(f"Snapshot destino creado para traslado: destino_id={destino_id}, saldo_anterior={saldo_anterior_destino}, saldo_nuevo={saldo_nuevo_destino}")

            # Auditoría del snapshot de destino
            if auditor is not None:
                try:
                    audit_snap_dest = LogsAuditoriaCreate(
                        entidad='saldo_snapshot_scada',
                        entidad_id=str(getattr(s_destino, 'id', None)),
                        accion='CREATE',
                        valor_anterior=None,
                        valor_nuevo=AnyUtils.serialize_orm_object(s_destino),
                        usuario_id=current_user_id.get()
                    )
                    await auditor.log_audit(audit_log_data=audit_snap_dest)
                except Exception as e_aud:
                    log.error(f"No se pudo registrar auditoría para snapshot destino: {e_aud}")

        except Exception as e_destino:
            log.error(f"Error creando snapshot de destino para traslado: {e_destino}", exc_info=True)

    return snapshots_creados

class PesadasService:

    def __init__(self, pesada_repository: PesadasRepository, pesadas_corte_repository: PesadasCorteRepository, transacciones_repository: Optional[TransaccionesRepository] = None) -> None:
        self._repo = pesada_repository
        self._repo_corte = pesadas_corte_repository
        # Repositorio de transacciones (opcional, inyectado por DI). Se usa para actualizar el estado a 'Proceso' cuando se crea una pesada.
        self._trans_repo = transacciones_repository

    async def create_pesada(self, pesada_data: PesadaCreate) -> PesadaResponse:
        """
        Create a new pesada in the database.

        Args:
            pesada_data (PesadaCreate): The data for the pesada to be created.

        Returns:
            PesadaResponse: The created pesada object.

        Raises:
            BasedException: For unexpected errors during the creation process.
            EntityAlreadyRegisteredException: If a pesada with the same transaction ID and consecutivo already exists.
        """
        # Validar que venga la transacción asociada: sin transacción no se puede crear la pesada
        trans_id = getattr(pesada_data, 'transaccion_id', None)
        if trans_id is None:
            raise BasedException(
                message="Para crear una pesada se requiere 'transaccion_id'.",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Calcular consecutivo automáticamente si no viene en el request
            consecutivo = getattr(pesada_data, 'consecutivo', None)
            if consecutivo is None:
                existing_count = await self._repo.count_by_transaccion(int(trans_id))
                consecutivo = float(existing_count + 1)
                log.info(f"Consecutivo calculado automáticamente para transacción {trans_id}: {consecutivo}")

            # Verificar existencia previa: mismo transaccion_id y consecutivo
            if await self._repo.find_one(transaccion_id=trans_id, consecutivo=consecutivo):
                raise EntityAlreadyRegisteredException(f"En la transacción {trans_id} ya existe una pesada con ese consecutivo '{consecutivo}'")

            # Excluir campos de snapshot que no forman parte del modelo ORM Pesadas
            pesada_payload = pesada_data.model_dump(exclude={'saldo_anterior', 'saldo_nuevo'})

            # Asignar consecutivo calculado al payload
            pesada_payload['consecutivo'] = consecutivo

            # Obtener usuario_id de la sesión actual
            pesada_payload['usuario_id'] = current_user_id.get()

            pesada_model = Pesadas(**pesada_payload)

            # Si el repositorio tiene una sesión DB (runtime), realizar ambas operaciones en una transacción
            session = getattr(self._repo, 'db', None)
            # Detectar si la propiedad `db` del repo es una AsyncSession real. En tests
            # los mocks pueden exponer `.db` como un Mock (truthy) y esto hacía que el
            # flujo intentara usar una sesión real contra la DB. Comprobar instancia evita eso.
            if isinstance(session, AsyncSession) and hasattr(session, 'begin'):
                try:
                    # Si ya existe una transacción activa en la sesión, no intentar crear otra
                    if getattr(session, 'in_transaction', None) and session.in_transaction():
                        # La sesión ya tiene transacción activa. Para asegurar que la pesada se persista
                        # (no depender del commit de la transacción exterior) abrimos una sesión
                        # independiente y realizamos la creación y actualización allí (commit inmediato).
                        log.info(f"create_pesada: session ya tiene transacción activa; usando sesión independiente para commit inmediato de transaccion {trans_id}.")
                        async with DatabaseConfiguration._async_session() as new_s:
                            async with new_s.begin():
                                new_s.add(pesada_model)
                                await new_s.flush()
                                await new_s.refresh(pesada_model)
                                # Registrar auditoría de creación de pesada (sesión independiente)
                                try:
                                    audit_pes = LogsAuditoriaCreate(
                                        entidad='pesadas',
                                        entidad_id=str(getattr(pesada_model, 'id', None)),
                                        accion='CREATE',
                                        valor_anterior=None,
                                        valor_nuevo=AnyUtils.serialize_orm_object(pesada_model),
                                        usuario_id=current_user_id.get()
                                    )
                                    # usar auditor del repositorio si está disponible
                                    if getattr(self._repo, 'auditor', None) is not None:
                                        await self._repo.auditor.log_audit(audit_log_data=audit_pes)
                                except Exception as e_aud:
                                    log.error(f"No se pudo registrar auditoría para pesada (sesión independiente): {e_aud}")

                                from sqlalchemy import select as _select
                                result = await new_s.execute(_select(Transacciones).filter(Transacciones.id == int(trans_id)))
                                tran_obj = result.scalar_one_or_none()
                                if tran_obj is None:
                                    raise EntityNotFoundException(f"Transacción con ID {trans_id} no encontrada para actualizar a 'Proceso'.")
                                tran_obj.estado = 'Proceso'
                                await new_s.flush()

                                # Si vienen saldos en la petición, crear snapshot(s) en la misma transacción
                                try:
                                    sa = getattr(pesada_data, 'saldo_anterior', None)
                                    sn = getattr(pesada_data, 'saldo_nuevo', None)
                                    if sa is not None and sn is not None:
                                        # Usar función auxiliar que maneja Traslados (crea 2 snapshots)
                                        auditor = getattr(self._repo, 'auditor', None)
                                        await _crear_snapshots_pesada(
                                            session=new_s,
                                            pesada_id=int(pesada_model.id),
                                            tran_obj=tran_obj,
                                            saldo_anterior_origen=Decimal(str(sa)),
                                            saldo_nuevo_origen=Decimal(str(sn)),
                                            auditor=auditor
                                        )
                                except Exception as e_snap:
                                    log.error(f"No se pudo crear snapshot en transacción independiente: {e_snap}", exc_info=True)

                        log.info(f"create_pesada: sesión independiente commit completado para transaccion {trans_id}.")
                        return PesadaResponse.model_validate(pesada_model)
                    else:
                        async with session.begin():
                            # Crear pesada
                            session.add(pesada_model)
                            await session.flush()
                            await session.refresh(pesada_model)
                            # Registrar auditoría de creación de pesada (sesión principal)
                            try:
                                audit_pes = LogsAuditoriaCreate(
                                    entidad='pesadas',
                                    entidad_id=str(getattr(pesada_model, 'id', None)),
                                    accion='CREATE',
                                    valor_anterior=None,
                                    valor_nuevo=AnyUtils.serialize_orm_object(pesada_model),
                                    usuario_id=current_user_id.get()
                                )
                                if getattr(self._repo, 'auditor', None) is not None:
                                    await self._repo.auditor.log_audit(audit_log_data=audit_pes)
                            except Exception as e_aud:
                                log.error(f"No se pudo registrar auditoría para pesada (sesión principal): {e_aud}")

                            # Actualizar transacción: debe existir y se actualiza a 'Proceso'
                            from sqlalchemy import select
                            result = await session.execute(select(Transacciones).filter(Transacciones.id == int(trans_id)))
                            tran_obj = result.scalar_one_or_none()
                            if tran_obj is None:
                                # Forzar rollback
                                raise EntityNotFoundException(f"Transacción con ID {trans_id} no encontrada para actualizar a 'Proceso'.")
                            tran_obj.estado = 'Proceso'
                            # flush cambios
                            await session.flush()

                            # Si vienen saldos en la petición, crear snapshot(s) usando la misma sesión
                            try:
                                sa = getattr(pesada_data, 'saldo_anterior', None)
                                sn = getattr(pesada_data, 'saldo_nuevo', None)
                                if sa is not None and sn is not None:
                                    # Usar función auxiliar que maneja Traslados (crea 2 snapshots)
                                    auditor = getattr(self._repo, 'auditor', None)
                                    await _crear_snapshots_pesada(
                                        session=session,
                                        pesada_id=int(pesada_model.id),
                                        tran_obj=tran_obj,
                                        saldo_anterior_origen=Decimal(str(sa)),
                                        saldo_nuevo_origen=Decimal(str(sn)),
                                        auditor=auditor
                                    )
                            except Exception as e_snap:
                                log.error(f"No se pudo crear snapshot en transacción principal: {e_snap}", exc_info=True)

                        log.info(f"Pesada creada con referencia: {getattr(pesada_model, 'referencia', None)} y transacción {trans_id} actualizada a 'Proceso' (transaccional).")
                        return PesadaResponse.model_validate(pesada_model)

                except Exception as e_transact:
                    log.error(f"Error transaccional creando pesada y actualizando transacción {trans_id}: {e_transact}", exc_info=True)
                    # normalizar error
                    if isinstance(e_transact, EntityNotFoundException):
                        raise e_transact
                    raise BasedException(
                        message=f"Error inesperado al crear la pesada y actualizar la transacción: {str(e_transact)}",
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )

            # Fallback (por ejemplo durante tests donde repositorio es un mock): usar comportamiento anterior
            created_pesada = await self._repo.create(pesada_model)
            log.info(f"Pesada creada con referencia: {getattr(created_pesada, 'referencia', None)} (fallback no transaccional)")

            # Intentar crear snapshot(s) en fallback si vienen campos de saldo
            try:
                sa = getattr(pesada_data, 'saldo_anterior', None)
                sn = getattr(pesada_data, 'saldo_nuevo', None)
                if sa is not None and sn is not None:
                    # Intentar crear snapshot en una sesión nueva (no crítico)
                    async with DatabaseConfiguration._async_session() as s:
                        async with s.begin():
                            # Obtener transacción para relacionar almacenamiento/material
                            from sqlalchemy import select as _sel
                            result = await s.execute(_sel(Transacciones).filter(Transacciones.id == int(trans_id)))
                            tran_obj = result.scalar_one_or_none()
                            if tran_obj is not None:
                                # Usar función auxiliar que maneja Traslados (crea 2 snapshots)
                                auditor = getattr(self._repo, 'auditor', None)
                                await _crear_snapshots_pesada(
                                    session=s,
                                    pesada_id=int(created_pesada.id),
                                    tran_obj=tran_obj,
                                    saldo_anterior_origen=Decimal(str(sa)),
                                    saldo_nuevo_origen=Decimal(str(sn)),
                                    auditor=auditor
                                )
            except Exception as e_snap:
                log.error(f"No fue posible crear snapshot de saldo en fallback: {e_snap}", exc_info=True)

            try:
                if self._trans_repo is not None:
                    # Rellenar explícitamente campos opcionales para evitar advertencias estáticas
                    update_data = TransaccionUpdate(estado='Proceso') ##TODO actualizar el peso cada vez que se cree una pesada
                    await self._trans_repo.update(int(trans_id), update_data)
                    log.info(f"Transacción {trans_id} actualizada a 'Proceso' después de crear pesada (fallback).")
            except Exception as e_trans:
                log.error(f"No fue posible actualizar estado de transacción {trans_id} a 'Proceso' en fallback: {e_trans}", exc_info=True)

            return PesadaResponse.model_validate(created_pesada)
        except EntityAlreadyRegisteredException:
            # Propagar tal cual para capa superior
            raise
        except Exception as e:
            log.error(f"Error al crear pesada: {e}")
            raise BasedException(
                message="Error inesperado al crear la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def update_pesada(self, pesada_id: int, pesada: PesadaUpdate) -> Optional[PesadaResponse]:
        """
        Update an existing pesada in the database.

        Args:
            pesada_id (int): The ID of the pesada to update.
            pesada (PesadaUpdate): The updated pesada data.

        Returns:
            Optional[PesadaResponse]: The updated pesada object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            pesada_payload = pesada.model_dump(exclude={'saldo_anterior', 'saldo_nuevo'})
            pesada_model = Pesadas(**pesada_payload)
            updated_pesada = await self._repo.update(pesada_id, pesada_model)
            log.info(f"Pesada actualizada con ID: {pesada_id}")
            return PesadaResponse.model_validate(updated_pesada) if updated_pesada else None
        except Exception as e:
            log.error(f"Error al actualizar pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete_pesada(self, pesada_id: int) -> bool:
        """
        Delete a pesada from the database.

        Args:
            pesada_id (int): The ID of the pesada to delete.

        Returns:
            bool: True if the pesada was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(pesada_id)
            log.info(f"Pesada eliminada con ID: {pesada_id}")
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_pesada(self, pesada_id: int) -> Optional[PesadaResponse]:
        """
        Retrieve a pesada by its ID.

        Args:
            pesada_id (int): The ID of the pesada to retrieve.

        Returns:
            Optional[PesadaResponse]: The pesada object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            pesada = await self._repo.get_by_id(pesada_id)
            return PesadaResponse.model_validate(pesada) if pesada else None
        except Exception as e:
            log.error(f"Error al obtener pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la pesada.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pag_pesadas(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[PesadaResponse]:
        """
        Retrieve paginated pesadas, optionally filtered by transaction ID.

        Args:
            tran_id (Optional[int]): The ID of the transaction to filter by, if provided.
            params (Params): Pagination parameters.

        Returns:
            Page[PesadaResponse]: A paginated list of pesada objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            query = select(Pesadas)

            if tran_id is not None:
                query = query.where(Pesadas.transaccion_id == tran_id)

            return await self._repo.get_all_paginated(query=query, params=params)
        except Exception as e:
            log.error(f"Error al obtener pesadas paginadas con tran_id {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener las pesadas paginadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_pesadas(self) -> List[PesadaResponse]:
        """
        Retrieve all pesadas from the database.

        Returns:
            List[PesadaResponse]: A list of all pesada objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            pesadas = await self._repo.get_all()
            return [PesadaResponse.model_validate(p) for p in pesadas]
        except Exception as e:
            log.error(f"Error al obtener todas las pesadas: {e}")
            raise BasedException(
                message="Error inesperado al obtener las pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_pesada_if_not_exists(self, pesada_data: PesadaCreate) -> PesadaResponse:
        """
        Wrapper kept for backward compatibility: delegates to `create_pesada`.
        Previous implementation lived here; now the canonical method is
        `create_pesada` which already enforces the "if not exists" behaviour.
        """
        # Delegar a la implementación unificada
        return await self.create_pesada(pesada_data)

    async def create_pesadas_corte_if_not_exists(self, acum_data: List[PesadasCalculate]) -> List[PesadasCorteCreate]:
        """
        Check if a pesadas_corte record with the same transaction ID and consecutivo already exists. If not, create a new one.

        Args:
            acum_data(PesadasCalculate): The data of accumulated weight.

        Returns:
            List[PesadasCorteCreate]: The list of existing or newly created pesadas_corte records.

        Raises:
            EntityAlreadyRegisteredException: If pesadas_corte already exists.
            BasedException: For unexpected errors during creation or retrieval.
        """
        try:
            if not acum_data:
                raise ValueError("No hay pesaje por procesar")

            log.info(f"create_pesadas_corte_if_not_exists: recibidos {len(acum_data)} acumulados")

            # STEP 1: Preparar cortes calculando el siguiente consecutivo por transacción
            pesadas_corte_data = []
            # next_map mantiene el siguiente consecutivo esperado por transacción durante la preparación del batch
            next_map: dict[int, int] = {}
            for item in acum_data:
                try:
                    tran = getattr(item, 'transaccion', None)
                    # Calcular el siguiente consecutivo por transacción usando conteo de registros existentes
                    next_consec = 1
                    if tran is not None:
                        try:
                            tkey = int(tran)
                            if tkey not in next_map:
                                existing_count = await self._repo_corte.count_by_transaccion(tkey)
                                next_map[tkey] = int(existing_count)
                            # el siguiente consecutivo es el contador actual + 1
                            next_consec = next_map[tkey] + 1
                            # reservar/incrementar para próximos items del mismo tran en este batch
                            next_map[tkey] = next_map[tkey] + 1
                        except Exception:
                            next_consec = 1

                    puerto_prefix = (item.puerto_id.split('-')[0] if getattr(item, 'puerto_id', None) else 'REF')
                    # Generar ref definitivo usando consecutivo por transacción
                    # Usar uuid5 determinístico por transacción para que la parte intermedia sea constante entre registros de la misma transacción
                    if tran is not None:
                        try:
                            token_mid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(int(tran)))).replace('-', '')[:8].upper()
                        except Exception:
                            token_mid = str(uuid.uuid4())[:8].upper()
                    else:
                        token_mid = str(uuid.uuid4())[:8].upper()
                    new_ref = f"{puerto_prefix}-{token_mid}-{next_consec}"

                    # Preparar campos con conversiones explícitas para evitar problemas de tipo
                    puerto_val = getattr(item, 'puerto_id', None) or ''
                    trans_val = getattr(item, 'transaccion', None)
                    pit_val = getattr(item, 'pit', None)
                    material_val = getattr(item, 'material', '') or ''
                    peso_val = getattr(item, 'peso', None)
                    fecha_val = getattr(item, 'fecha_hora', None)
                    usuario_val = getattr(item, 'usuario_id', None)

                    from decimal import Decimal
                    try:
                        peso_dec = Decimal(str(peso_val)) if peso_val is not None else None
                    except Exception:
                        peso_dec = None

                    # El campo 'consecutivo' en la respuesta representa viaje_id (no es un contador).
                    viaje_id_val = getattr(item, 'consecutivo', None)
                    pesadas_corte_data.append(
                        PesadasCorteCreate(
                            puerto_id=puerto_val,
                            transaccion=int(trans_val) if trans_val is not None else None,
                            # usar viaje_id en el campo consecutivo
                            consecutivo=int(viaje_id_val) if viaje_id_val is not None else None,
                            pit=int(pit_val) if pit_val is not None else None,
                            material=material_val,
                            peso=peso_dec,
                            ref=new_ref,
                            enviado=True,
                            fecha_hora=fecha_val,
                            usuario_id=int(usuario_val) if usuario_val is not None else None,
                        )
                    )
                    log.info(f"Prepared pesadas_corte_data item: puerto={puerto_val} transaccion={trans_val} consecutivo={next_consec} peso={peso_dec} fecha_hora={fecha_val}")
                except Exception as inner_e:
                    log.error(f"Error preparando pesadas_corte para item {item}: {inner_e}", exc_info=True)

            if not pesadas_corte_data:
                try:
                    preview_acum = [
                        (a.model_dump() if hasattr(a, 'model_dump') else dict(a))
                        for a in acum_data[:5]
                    ]
                except Exception:
                    preview_acum = [str(a) for a in acum_data[:5]]
                log.warning(f"create_pesadas_corte_if_not_exists: no se prepararon registros para crear en pesadas_corte. preview acum_data={preview_acum}")

            try:
                # Antes de lanzar create_bulk, registrar cantidad y ejemplos para diagnóstico
                try:
                    preview = [
                        {"puerto_id": getattr(p, 'puerto_id', None), "transaccion": getattr(p, 'transaccion', None), "consecutivo": getattr(p, 'consecutivo', None)}
                        for p in pesadas_corte_data[:5]
                    ]
                except Exception:
                    preview = []
                log.info(f"create_pesadas_corte_if_not_exists: intentando create_bulk con {len(pesadas_corte_data)} items; ejemplos={preview}")

                # Crear registros y obtener sus IDs (ya vienen con ref y consecutivo correctos)
                creada_intermedia = await self._repo_corte.create_bulk(pesadas_corte_data)

                created_count = len(creada_intermedia) if creada_intermedia else 0
                log.info(f"create_pesadas_corte_if_not_exists: create_bulk devolvió {created_count} registros")

                # Si create_bulk no creó todos los registros esperados, intentar creación individual
                if not creada_intermedia or (isinstance(creada_intermedia, list) and len(creada_intermedia) < len(pesadas_corte_data)):
                    log.warning("create_pesadas_corte_if_not_exists: create_bulk no creó todos los registros, intentando crear individualmente")
                    created_individual = []
                    for idx, item_to_create in enumerate(pesadas_corte_data):
                        try:
                            created_single = await self._repo_corte.create(item_to_create)
                            created_individual.append(created_single)
                            log.info(f"create_pesadas_corte_if_not_exists: creado individual {idx+1}/{len(pesadas_corte_data)} -> transaccion={getattr(item_to_create,'transaccion',None)} consecutivo={getattr(item_to_create,'consecutivo',None)}")
                        except Exception as ex_single:
                            log.error(f"Error creando pesadas_corte individual para transaccion={getattr(item_to_create,'transaccion',None)}: {ex_single}", exc_info=True)

                    if created_individual:
                        log.info(f"create_pesadas_corte_if_not_exists: creación individual devolvió {len(created_individual)} registros")
                        return created_individual
                    else:
                        log.warning("create_pesadas_corte_if_not_exists: creación individual no produjo registros")

                return creada_intermedia
            except Exception as e:
                # Si la creación falla, intentamos recuperar los cortes existentes (fallback)
                log.error(f"create_bulk falló para pesadas_corte: {e}", exc_info=True)
                recovered = []
                for item in acum_data:
                    try:
                        existing = await self._repo_corte.find_many(puerto_id=item.puerto_id, transaccion=item.transaccion)
                        if existing:
                            recovered.extend(existing)
                    except Exception as ex_inner:
                        log.error(f"Error al recuperar pesadas_corte existentes para puerto {item.puerto_id} transaccion {item.transaccion}: {ex_inner}", exc_info=True)

                if recovered:
                    log.info(f"Se recuperaron {len(recovered)} pesadas_corte existentes tras fallo de creación.")
                    return recovered
                else:
                    # No pudimos recuperar nada: volver a elevar excepción para que sea tratado arriba
                    raise

        except ValueError as e:
            log.error(f"Validation error for pesadas_corte: {e}")
            raise BasedException(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            log.error(f"Error al registrar pesadas_corte : {e}", exc_info=True)
            raise BasedException(
                message=f"Error inesperado al registrar pesadas_corte: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def gen_pesada_identificador(self, pesada_data: PesadaCorteRetrieve) -> str:
        """
            Generate a unique identifier for a pesada_corte record.

            Args:
                pesada_data (PesadaCorteRetrieve): The data used to generate the identifier.

            Returns:
                str: The generated pesada identifier.

            Raises:
                BasedException: For validation or unexpected errors.
        """

        try:
            pesada_id: str

            # 1. Calcular siguiente consecutivo por transacción usando count_by_transaccion
            tran = getattr(pesada_data, 'transaccion', None)
            next_consec = 1
            if tran is not None:
                try:
                    existing_count = await self._repo_corte.count_by_transaccion(int(tran))
                    next_consec = int(existing_count) + 1
                except Exception:
                    next_consec = 1

            puerto_prefix = pesada_data.puerto_id.split('-')[0] if pesada_data.puerto_id else 'REF'
            # usar uuid5 para que sea estable por transacción
            if tran is not None:
                try:
                    token_mid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(int(tran)))).replace('-', '')[:8].upper()
                except Exception:
                    token_mid = str(uuid.uuid4())[:8].upper()
            else:
                token_mid = str(uuid.uuid4())[:8].upper()
            pesada_id = f"{puerto_prefix}-{token_mid}-{next_consec}"

            return pesada_id

        except Exception as e:
            log.error(f"Error al generar identificador para pesada_corte: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al generar el identificador de la pesada.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pesadas_acumuladas(self, puerto_id: str) -> List[VPesadasAcumResponse]:
        """
        Obtener y procesar pesadas acumuladas para un puerto (y opcionalmente una transacción).

        Flujo:
        1) Obtener la transacción en estado 'Proceso' (o la más reciente) para el puerto dado.
        2) Consultar el acumulado de pesadas nuevas desde la última transacción.
        3) Construir rangos de pesadas para marcar como leídas.
        4) Intentar crear registros en pesadas_corte (no crítico).
        5) Marcar las pesadas como leídas.
        6) Construir y devolver la respuesta, prefiriendo datos de pesadas_corte
        """
        try:
            # 1. Obtener transacciones candidate para el puerto_id: preferir estado 'Proceso' ordenadas por fecha, luego el resto por fecha
            tran_candidates = None
            try:
                if self._trans_repo is not None:
                    trans_list = await self._trans_repo.find_many(ref1=puerto_id)
                    if trans_list:
                        from datetime import datetime
                        proceso = [t for t in trans_list if getattr(t, 'estado', None) == 'Proceso']
                        # ordenar por fecha_hora desc dentro de cada grupo
                        proceso_sorted = sorted(proceso, key=lambda t: getattr(t, 'fecha_hora') or datetime.min, reverse=True)
                        others = [t for t in trans_list if getattr(t, 'estado', None) != 'Proceso']
                        others_sorted = sorted(others, key=lambda t: getattr(t, 'fecha_hora') or datetime.min, reverse=True)
                        tran_candidates = proceso_sorted + others_sorted
                else:
                    log.warning("get_pesadas_acumuladas: no hay repositorio de transacciones disponible para buscar ref1 por puerto.")
            except Exception as e_tran:
                log.error(f"Error buscando transacciones por ref1={puerto_id}: {e_tran}", exc_info=True)
                tran_candidates = None

            # Si no hay candidatos (no trans_repo o trans_list vacía), se utiliza el comportamiento actual (tran_id=None)
            # Intentamos primero con la transaccion más reciente (si hay candidates) y si no, con tran_id=None
            acumulado = None
            selected_tran_id = None

            if tran_candidates:
                # Iterar candidatos y usar fetch_and_mark_sumatoria_pesadas para obtener y marcar de forma atómica
                for t in tran_candidates:
                    try:
                        t_id = getattr(t, 'id', None)
                        if t_id is None:
                            continue
                        acumulado_tmp = await self._repo.fetch_and_mark_sumatoria_pesadas(puerto_id, int(t_id))
                        if acumulado_tmp:
                            acumulado = acumulado_tmp
                            selected_tran_id = int(t_id)
                            break
                    except Exception as e_iter:
                        log.error(f"Error obteniendo/ marcando pesadas para transaccion {getattr(t,'id',None)}: {e_iter}", exc_info=True)
                        continue

            if acumulado is None:
                # fallback: intentar como antes con tran_id=None (buscar acumulado global)
                try:
                    acumulado = await self._repo.get_sumatoria_pesadas(puerto_id, None)
                except Exception as e_acum:
                    log.error(f"Error al obtener acumulado fallback para puerto {puerto_id}: {e_acum}", exc_info=True)
                    acumulado = None

            if not acumulado:
                raise EntityNotFoundException("No hay pesadas nuevas por reportar.")

            # 3. Construir rangos para marcar como leídas (solo donde existan ids válidos)
            pesada_range = [
                PesadasRange(primera=acum.primera, ultima=acum.ultima, transaccion=acum.transaccion)
                for acum in acumulado
                if getattr(acum, 'primera', None) is not None and getattr(acum, 'ultima', None) is not None and getattr(acum, 'transaccion', None) is not None
            ]

            # Si usamos fetch_and_mark_sumatoria_pesadas, ya fueron marcadas; solo marcar si vino del fallback get_sumatoria_pesadas
            pesadas_corte_records = None
            try:
                pesadas_corte_records = await self.create_pesadas_corte_if_not_exists(acumulado)
            except Exception as e_create:
                log.error(f"No fue posible crear pesadas_corte (no crítico): {e_create}", exc_info=True)

            # Si pesada_range no está vacío y no marcamos previamente (fallback), marcar
            if pesada_range and selected_tran_id is None:
                ids_marcados = await self._repo.mark_pesadas(pesada_range)
                log.info(f"{len(ids_marcados)} Pesadas marcadas como leído.")

            # 6. Construir la respuesta: preferir registros de pesadas_corte (tienen la ref con el consecutivo por transacción)
            response: List[VPesadasAcumResponse] = []
            from decimal import Decimal
            from datetime import datetime

            # Mapear acumulado por transaccion para poder mantener 'consecutivo' (viaje) en la respuesta
            acum_map = {int(getattr(a, 'transaccion')): a for a in acumulado}

            if pesadas_corte_records:
                # pesadas_corte_records pueden ser Pydantic models o listas de dicts/schemas
                for corte in pesadas_corte_records:
                    try:
                        # obtener atributos del corte
                        ref = getattr(corte, 'ref', None) or (corte.get('ref') if isinstance(corte, dict) else None)
                        trans = getattr(corte, 'transaccion', None) or (corte.get('transaccion') if isinstance(corte, dict) else None)
                        pit = getattr(corte, 'pit', None) or (corte.get('pit') if isinstance(corte, dict) else None)
                        material = getattr(corte, 'material', None) or (corte.get('material') if isinstance(corte, dict) else None) or ''
                        peso_val = getattr(corte, 'peso', None) or (corte.get('peso') if isinstance(corte, dict) else None)
                        puerto = getattr(corte, 'puerto_id', None) or (corte.get('puerto_id') if isinstance(corte, dict) else None) or puerto_id
                        fecha_hora = getattr(corte, 'fecha_hora', None) or (corte.get('fecha_hora') if isinstance(corte, dict) else None) or now_local()
                        usuario_id = getattr(corte, 'usuario_id', None) or (corte.get('usuario_id') if isinstance(corte, dict) else None) or 0

                        # Mantener 'consecutivo' del acumulado (viaje)
                        viaje_consec = None
                        if trans is not None and int(trans) in acum_map:
                            viaje_consec = int(getattr(acum_map[int(trans)], 'consecutivo', 0) or 0)
                            usuario = getattr(acum_map[int(trans)], 'usuario', "") or ""
                        else:
                            viaje_consec = 0
                            usuario = ""

                        try:
                            peso = Decimal(peso_val) if peso_val is not None else Decimal('0')
                        except Exception:
                            peso = Decimal('0')

                        resp = VPesadasAcumResponse(
                            referencia=ref,
                            consecutivo=int(viaje_consec),
                            transaccion=int(trans) if trans is not None else 0,
                            pit=int(pit) if pit is not None else 0,
                            material=material,
                            peso=peso,
                            puerto_id=puerto,
                            fecha_hora=fecha_hora,
                            usuario_id=int(usuario_id),
                            usuario=usuario,
                        )
                        response.append(resp)
                    except Exception as e_map:
                        log.error(f"Error mapeando pesadas_corte a VPesadasAcumResponse: {e_map} - corte: {corte}", exc_info=True)

                log.info(f"Se han procesado {len(response)} pesadas cortes a partir de registros en pesadas_corte.")
                return response

            # Si no se generaron registros en pesadas_corte, construir desde acumulado y generar una ref por transaccion
            for acum in acumulado:
                try:
                    transaccion = int(getattr(acum, 'transaccion', 0) or 0)
                    viaje_consec = int(getattr(acum, 'consecutivo', 0) or 0)
                    pit = int(getattr(acum, 'pit', 0) or 0)
                    material = getattr(acum, 'material', '') or ''
                    peso_val = getattr(acum, 'peso', None)
                    try:
                        peso = Decimal(peso_val) if peso_val is not None else Decimal('0')
                    except Exception:
                        peso = Decimal('0')
                    puerto = getattr(acum, 'puerto_id', None) or puerto_id
                    fecha_hora = getattr(acum, 'fecha_hora', None) or now_local()
                    usuario_id = int(getattr(acum, 'usuario_id', 0) or 0)

                    # generar referencia por transacción (serie 1,2,3...) usando gen_pesada_identificador
                    try:
                        gen_req = PesadaCorteRetrieve(puerto_id=puerto, transaccion=transaccion)
                        ref_gen = await self.gen_pesada_identificador(gen_req)
                    except Exception as e_ref:
                        log.error(f"No fue posible generar referencia para transaccion {transaccion}: {e_ref}", exc_info=True)
                        ref_gen = None

                    resp = VPesadasAcumResponse(
                        referencia=ref_gen,
                        consecutivo=viaje_consec,
                        transaccion=transaccion,
                        pit=pit,
                        material=material,
                        peso=peso,
                        puerto_id=puerto,
                        fecha_hora=fecha_hora,
                        usuario_id=usuario_id,
                        usuario=getattr(acum, 'usuario', "") or "",
                    )
                    response.append(resp)
                except Exception as e_map:
                    log.error(f"Error mapeando acumulado a VPesadasAcumResponse (fallback): {e_map} - acum: {acum}", exc_info=True)

            log.info(f"Se han procesado {len(response)} pesadas cortes de un total de {len(acumulado)} registros acumulados (fallback desde acumulado).")
            return response

        except EntityNotFoundException:
            raise
        except Exception as e:
            log.error(f"Error al obtener suma de pesadas para puerto_id {puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al obtener la suma de pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_envio_final(self, puerto_id: Optional[str] = None) -> List[VPesadasAcumResponse]:
        """
        Retorna una lista con un elemento por cada transacción (BL) asociada al mismo `puerto_id`.
        La referencia final se genera a partir de la última pesada global; sólo la transacción
        de la última pesada mantiene su peso real, las demás transacciones tendrán peso = 0.
        """
        try:
            from sqlalchemy import select
            from decimal import Decimal
            from datetime import datetime

            # Obtener todas las pesadas_corte para el puerto ordenadas por fecha desc (la primera es la última global)
            query = (select(self._repo_corte.model)
                     .where(self._repo_corte.model.puerto_id == puerto_id)
                     .order_by(self._repo_corte.model.fecha_hora.desc()))
            result = await self._repo_corte.db.execute(query)
            cortes = result.scalars().all()

            if not cortes:
                raise EntityNotFoundException("No hay pesadas nuevas por reportar. no encontrada.")

            # Última pesada global (más reciente)
            last_corte = cortes[0]

            # Construir referencia final a partir de la última pesada global
            ref = getattr(last_corte, 'ref', None)
            corte_id = getattr(last_corte, 'id', None)
            referencia_final = f"{ref}F" if ref else (f"{corte_id}F" if corte_id is not None else None)

            # Determinar qué transacción corresponde a la última pesada global (mantendrá el peso real)
            try:
                transacion_con_peso = int(getattr(last_corte, 'transaccion')) if getattr(last_corte, 'transaccion', None) is not None else None
            except Exception:
                transacion_con_peso = None

            # Agrupar el último registro por transacción (primer aparición al iterar cortes ordenados desc)
            per_tran: dict[int, object] = {}
            for corte in cortes:
                try:
                    trans_attr = getattr(corte, 'transaccion', None)
                    # convertir transaccion a entero seguro (si es None, usar 0)
                    try:
                        tkey = int(trans_attr) if trans_attr is not None else 0
                    except Exception:
                        tkey = 0
                    if tkey not in per_tran:
                        per_tran[tkey] = corte
                except Exception:
                    # Ignorar cortes mal formados
                    continue

            # Construir la lista de respuestas: una entrada por cada transacción encontrada
            response: List[VPesadasAcumResponse] = []

            for tkey, corte in per_tran.items():
                try:
                    pit = getattr(corte, 'pit', None) or 0
                    material = getattr(corte, 'material', None) or ""
                    peso_val = getattr(corte, 'peso', None)
                    puerto = getattr(corte, 'puerto_id', None) or puerto_id
                    fecha_hora = getattr(corte, 'fecha_hora', None) or now_local()
                    usuario_id = getattr(corte, 'usuario_id', None) or 0
                    usuario = getattr(corte, 'usuario', None) or ""

                    # El campo 'consecutivo' en pesadas_corte ya contiene el viaje_id cuando se creó
                    consecutivo = getattr(corte, 'consecutivo', None) or 0

                    # Solo la transacción que coincide con la última pesada global mantiene su peso real
                    if transacion_con_peso is not None and int(tkey) == int(transacion_con_peso):
                        try:
                            peso = Decimal(peso_val) if peso_val is not None else Decimal('0')
                        except Exception:
                            peso = Decimal('0')
                    else:
                        peso = Decimal('0')

                    resp = VPesadasAcumResponse(
                        referencia=referencia_final,
                        consecutivo=int(consecutivo),
                        transaccion= 0,
                        pit=int(pit),
                        material=material,
                        peso=peso,
                        puerto_id=puerto,
                        fecha_hora=fecha_hora,
                        usuario_id=int(usuario_id),
                        usuario=usuario,
                    )
                    response.append(resp)
                except Exception as e_map:
                    log.error(f"Error mapeando pesadas_corte a VPesadasAcumResponse en envio final: {e_map} - corte: {corte}", exc_info=True)

            if not response:
                raise EntityNotFoundException("No hay pesadas por transacción encontradas para el envío final.")

            return response

        except EntityNotFoundException:
            raise
        except Exception as e:
            log.error(f"Error al obtener envio final para puerto_id {puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al obtener envio final.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_pesadas_corte(self, acum_data: List[PesadasCalculate]) -> List[PesadasCorteCreate]:
        """
        Crea registros en pesadas_corte a partir de datos acumulados, manejando referencias y errores de forma robusta.

        Flujo:
        1. Para cada registro en acum_data, intenta crear un nuevo registro en pesadas_corte.
        2. Si la creación es exitosa, genera una referencia única y actualiza el registro.
        3. Si la creación falla por clave duplicada, intenta recuperar el registro existente.
        4. Devuelve la lista de registros creados o recuperados.

        Args:
            acum_data (List[PesadasCalculate]): Lista de datos acumulados para crear registros en pesadas_corte.

        Returns:
            List[PesadasCorteCreate]: Lista de registros creados o recuperados en pesadas_corte.

        Raises:
            BasedException: Para errores inesperados durante el proceso de creación.
        """
        try:
            if not acum_data:
                raise ValueError("No hay datos acumulados para procesar.")

            registros_creados = []

            for data in acum_data:
                try:
                    # Calcular siguiente consecutivo para la transacción
                    tran = getattr(data, 'transaccion', None)
                    next_consec = 1
                    if tran is not None:
                        try:
                            existing_count = await self._repo_corte.count_by_transaccion(int(tran))
                            next_consec = int(existing_count) + 1
                        except Exception:
                            next_consec = 1

                    puerto_prefix = (data.puerto_id.split('-')[0] if getattr(data, 'puerto_id', None) else 'REF')
                    # generar token determinístico por transacción para mantener la parte intermedia constante
                    if tran is not None:
                        try:
                            token_mid = str(uuid.uuid5(uuid.NAMESPACE_DNS, str(int(tran)))).replace('-', '')[:8].upper()
                        except Exception:
                            token_mid = str(uuid.uuid4())[:8].upper()
                    else:
                        token_mid = str(uuid.uuid4())[:8].upper()
                    referencia_unica = f"{puerto_prefix}-{token_mid}-{next_consec}"

                    # 1. Intentar crear un nuevo registro en pesadas_corte con ref calculado y usar viaje_id como 'consecutivo'
                    viaje_id_val = getattr(data, 'consecutivo', None)
                    nuevo_registro = PesadasCorteCreate(
                        **data.model_dump(exclude={'primera', 'ultima', 'referencia'}),
                        ref=referencia_unica,
                        consecutivo=int(viaje_id_val) if viaje_id_val is not None else None,
                        enviado=True,
                    )
                    creado = await self._repo_corte.create(nuevo_registro)

                    registros_creados.append(creado)
                    log.info(f"Registro creado y referencia asignada: {referencia_unica}")
                except Exception as e:
                    log.error(f"Error al crear registro en pesadas_corte: {e}", exc_info=True)
                    # 3. Intentar recuperar el registro existente en caso de error
                    try:
                        existentes = await self._repo_corte.find_many(puerto_id=data.puerto_id, transaccion=data.transaccion)
                        if existentes:
                            registros_creados.extend(existentes)
                            log.info(f"Registros recuperados existentes: {len(existentes)}")
                    except Exception as ex_recuperar:
                        log.error(f"Error al recuperar registros existentes: {ex_recuperar}", exc_info=True)

            return registros_creados

        except ValueError as e:
            log.error(f"Error de validación: {e}")
            raise BasedException(
                message=str(e),
                status_code=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            log.error(f"Error inesperado en create_pesadas_corte: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al crear registros en pesadas_corte.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pesada_acumulada(self, puerto_id: Optional[str] = None,
                                   tran_id: Optional[int] = None) -> VPesadasAcumResponse:
        """
        Retrieve the sum of pesadas related to a puerto_id.

        Args:
            puerto_id (str): The optional ID of the puerto to filter pesadas by.
            tran_id (int): The optional ID of the transaction to filter pesadas by.

        Returns:
            VPesadasAcumResponse: An object containing the accumulated pesada data.

        Raises:
            EntityNotFoundException: If no pesadas are found for the given puerto_id.
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            return await self._repo.get_sumatoria_pesada(puerto_id, tran_id)
        except EntityNotFoundException as e:
            raise e
        except DatabaseSQLAlchemyException:
            raise
        except Exception as e:
            log.error(f"Error al obtener suma de pesadas para puerto_id {puerto_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la suma de pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pending_for_last_transaccion(self, puerto_id: str) -> List[VPesadasAcumResponse]:
        """
        Obtener la sumatoria de pesadas NO leídas (leido=False) únicamente para la última
        transacción asociada con `puerto_id`.

        Flujo:
        1. Determinar la última transacción (preferir estado 'Proceso', sino la más reciente) para el puerto.
        2. Solicitar al repositorio la sumatoria de pesadas no leídas para esa transacción.
        3. Generar una referencia para el envío final y devolver la lista de VPesadasAcumResponse.
        """
        try:
            # 1. Obtener lista de transacciones candidatas ordenadas por 'Proceso' y fecha
            tran_candidates = None
            try:
                if self._trans_repo is not None:
                    trans_list = await self._trans_repo.find_many(ref1=puerto_id)
                    if trans_list:
                        from datetime import datetime
                        proceso = [t for t in trans_list if getattr(t, 'estado', None) == 'Proceso']
                        proceso_sorted = sorted(proceso, key=lambda t: getattr(t, 'fecha_hora') or datetime.min, reverse=True)
                        others = [t for t in trans_list if getattr(t, 'estado', None) != 'Proceso']
                        others_sorted = sorted(others, key=lambda t: getattr(t, 'fecha_hora') or datetime.min, reverse=True)
                        tran_candidates = proceso_sorted + others_sorted
                else:
                    log.warning("get_pending_for_last_transaccion: no hay repositorio de transacciones disponible para buscar ref1 por puerto.")
            except Exception as e_tran:
                log.error(f"Error buscando transacciones por ref1={puerto_id}: {e_tran}", exc_info=True)
                tran_candidates = None

            if not tran_candidates:
                raise EntityNotFoundException("No se encontró transacción asociada al puerto especificado.")

            # 2. Iterar candidatos hasta encontrar uno con pesadas pendientes
            acumulado = None
            selected_tran = None
            for t in tran_candidates:
                try:
                    t_id = getattr(t, 'id', None)
                    if t_id is None:
                        continue
                    acumulado_tmp = await self._repo.fetch_and_mark_sumatoria_pesadas(puerto_id, int(t_id))
                    if acumulado_tmp:
                        acumulado = acumulado_tmp
                        selected_tran = int(t_id)
                        break
                except Exception as e_iter:
                    log.error(f"Error obteniendo/ marcando pesadas para transaccion {getattr(t,'id',None)}: {e_iter}", exc_info=True)
                    continue

            if not acumulado:
                raise EntityNotFoundException("No hay pesadas pendientes de enviar para la última transacción.")

            # 3. Generar referencia final (usar gen_pesada_identificador para mantener consistencia) y mapear al esquema de respuesta
            response: List[VPesadasAcumResponse] = []
            from decimal import Decimal
            from datetime import datetime

            # generar referencia base usando gen_pesada_identificador
            try:
                gen_req = PesadaCorteRetrieve(puerto_id=puerto_id, transaccion=int(selected_tran))
                ref_gen = await self.gen_pesada_identificador(gen_req)
                referencia_final = f"{ref_gen}F" if ref_gen else None
            except Exception as e_ref:
                log.error(f"No fue posible generar referencia para transaccion {selected_tran}: {e_ref}", exc_info=True)
                referencia_final = None

            for acum in acumulado:
                try:
                    transaccion = int(getattr(acum, 'transaccion', 0) or 0)
                    viaje_consec = int(getattr(acum, 'consecutivo', 0) or 0)
                    pit = int(getattr(acum, 'pit', 0) or 0)
                    material = getattr(acum, 'material', '') or ''
                    peso_val = getattr(acum, 'peso', None)
                    try:
                        peso = Decimal(peso_val) if peso_val is not None else Decimal('0')
                    except Exception:
                        peso = Decimal('0')
                    puerto = getattr(acum, 'puerto_id', None) or puerto_id
                    fecha_hora = getattr(acum, 'fecha_hora', None) or now_local()
                    usuario_id = int(getattr(acum, 'usuario_id', 0) or 0)

                    resp = VPesadasAcumResponse(
                        referencia=referencia_final,
                        consecutivo=viaje_consec,
                        transaccion=0,
                        pit=pit,
                        material=material,
                        peso=peso,
                        puerto_id=puerto,
                        fecha_hora=fecha_hora,
                        usuario_id=usuario_id,
                        usuario=getattr(acum, 'usuario', "") or "",
                    )
                    response.append(resp)
                except Exception as e_map:
                    log.error(f"Error mapeando acumulado a VPesadasAcumResponse en pending last: {e_map} - acum: {acum}", exc_info=True)

            return response

        except EntityNotFoundException:
            raise
        except Exception as e:
            log.error(f"Error al obtener pesadas pendientes para la última transacción del puerto_id {puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message="Error inesperado al obtener pesadas pendientes.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_suma_peso_by_transaccion(self, tran_id: int) -> Optional[dict]:
        """
        Obtener la suma total de peso_real de pesadas asociadas a una transacción.
        Este método funciona para cualquier tipo de transacción incluyendo Traslados.

        Args:
            tran_id: ID de la transacción.

        Returns:
            dict con 'peso_total' (Decimal) y 'cantidad_pesadas' (int), o None si no hay pesadas.
        """
        try:
            return await self._repo.get_suma_peso_by_transaccion(tran_id)
        except Exception as e:
            log.error(f"Error al obtener suma de peso para transaccion {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la suma de peso de pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


from typing import List, Optional
from decimal import Decimal

from fastapi_pagination import Page, Params
from sqlalchemy import select
from sqlalchemy import update as sqlalchemy_update
from starlette import status

from core.config.context import current_user_id
from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
from database.connection import DatabaseConfiguration
from database.models import Transacciones
from repositories.transacciones_repository import TransaccionesRepository
from schemas.transacciones_schema import TransaccionResponse, TransaccionCreate, TransaccionUpdate
from services.movimientos_service import MovimientosService
from services.pesadas_service import PesadasService
from utils.any_utils import AnyUtils
from utils.logger_util import LoggerUtil
from utils.time_util import now_local

log = LoggerUtil()

class TransaccionesService:

    def __init__(self, tran_repository: TransaccionesRepository, pesadas_service : PesadasService, mov_service : MovimientosService) -> None:
        self._repo = tran_repository
        self.pesadas_service = pesadas_service
        self.mov_service = mov_service

    async def create_transaccion(self, tran: TransaccionCreate) -> TransaccionResponse:
        """
        Create a new transaction in the database.

        Args:
            tran (TransaccionCreate): The data for the transaction to be created.

        Returns:
            TransaccionResponse: The created transaction object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            return await self._repo.create(tran)
        except Exception as e:
            log.error(f"Error al crear transacción: {e}")
            raise BasedException(
                message="Error inesperado al crear la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_transaccion(self, tran_id: int, tran: TransaccionUpdate) -> Optional[TransaccionResponse]:
        """
        Update an existing transaction in the database.

        Args:
            tran_id (int): The ID of the transaction to update.
            tran (TransaccionUpdate): The updated transaction data.

        Returns:
            Optional[TransaccionResponse]: The updated transaction object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            return await self._repo.update(tran_id, tran)
        except Exception as e:
            log.error(f"Error al actualizar transacción con ID {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete_transaccion(self, tran_id: int) -> bool:
        """
        Delete a transaction from the database.

        Args:
            tran_id (int): The ID of the transaction to delete.

        Returns:
            bool: True if the transaction was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            return await self._repo.delete(tran_id)
        except Exception as e:
            log.error(f"Error al eliminar transacción con ID {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_transaccion(self, tran_id: int) -> Optional[TransaccionResponse]:
        """
        Retrieve a transaction by its ID.

        Args:
            tran_id (int): The ID of the transaction to retrieve.

        Returns:
            Optional[TransaccionResponse]: The transaction object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            return await self._repo.get_by_id(tran_id)
        except Exception as e:
            log.error(f"Error al obtener transacción con ID {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_tran_by_viaje(self, viaje: int, bl_id: Optional[int] = None) -> Optional[TransaccionResponse]:
        """
        Retrieve a transaction record by its viaje ID.

        Args:
            viaje (int): The ID of the voyage to retrieve.
            bl_id (Optional[int]): Optional BL ID to filter the transaction.

        Returns:
            Optional[TransaccionResponse]: The transaction object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            # If bl_id is provided, try to match transacciones.bl_id == bl_id (new column)
            if bl_id is not None:
                tran = await self._repo.find_one_ordered(viaje_id=viaje, bl_id=bl_id)
                if tran:
                    return tran

            # Fallback: return the most recent transaccion for the viaje
            return await self._repo.find_one_ordered(viaje_id=viaje)
        except Exception as e:
            log.error(f"Error al obtener transacción con viaje {viaje}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_transacciones(self) -> List[TransaccionResponse]:
        """
        Retrieve all transactions from the database.

        Returns:
            List[TransaccionResponse]: A list of all transaction objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            return await self._repo.get_all()
        except Exception as e:
            log.error(f"Error al obtener todas las transacciones: {e}")
            raise BasedException(
                message="Error inesperado al obtener las transacciones.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pag_transacciones(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[TransaccionResponse]:
        """
        Retrieve paginated transactions, optionally filtered by transaction ID.

        Args:
            tran_id (Optional[int]): The ID of the transaction to filter by, if provided.
            params (Params): Pagination parameters.

        Returns:
            Page[TransaccionResponse]: A paginated list of transaction objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            query = select(Transacciones)

            if tran_id is not None:
                query = query.where(Transacciones.id == tran_id)

            return await self._repo.get_all_paginated(query=query, params=params)
        except Exception as e:
            log.error(f"Error al obtener transacciones paginadas con tran_id {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener las transacciones paginadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_transaccion_if_not_exists(self, tran_data: TransaccionCreate) -> TransaccionResponse:
        """
        Check if a transaction with the same Viaje ID already exists. If not, create a new one.

        Args:
            tran_data (TransaccionCreate): The data for the transaction to be created.

        Returns:
            TransaccionResponse: The existing or newly created transaction object.

        Raises:
            EntityAlreadyRegisteredException: If a transaction with the same Viaje ID already exists.
            BasedException: For unexpected errors during the creation process.
        """
        try:
            # Si la nueva transacción trae bl_id, impedir duplicados por (viaje_id, bl_id)
            bl_id = getattr(tran_data, 'bl_id', None)
            if bl_id is not None:
                existing = await self._repo.find_one(viaje_id=tran_data.viaje_id, bl_id=bl_id)
                if existing:
                    # Permitir si la transacción existente es de distinto 'tipo'
                    existing_tipo = getattr(existing, 'tipo', None)
                    new_tipo = getattr(tran_data, 'tipo', None)
                    try:
                        if existing_tipo is not None and new_tipo is not None and str(existing_tipo).strip().lower() != str(new_tipo).strip().lower():
                            log.info(f"create_transaccion_if_not_exists: existe transaccion con viaje_id={tran_data.viaje_id} y bl_id={bl_id} pero de tipo distinto ('{existing_tipo}' != '{new_tipo}'), permitiendo creación")
                        else:
                            raise EntityAlreadyRegisteredException(f"Ya existe transacción para viaje '{tran_data.viaje_id}' con bl_id '{bl_id}' y tipo '{existing_tipo}'")
                    except EntityAlreadyRegisteredException:
                        raise
                    except Exception as e_check:
                        # Si hay algún problema validando tipos, evitar crear duplicado por seguridad
                        log.error(f"Error validando existencia de transacción (viaje_id={tran_data.viaje_id}, bl_id={bl_id}): {e_check}", exc_info=True)
                        raise EntityAlreadyRegisteredException(f"Ya existe transacción para viaje '{tran_data.viaje_id}' con bl_id '{bl_id}'")

            tran_nueva = await self._repo.create(tran_data)
            return tran_nueva
        except EntityAlreadyRegisteredException as e:
            raise e
        except Exception as e:
            log.error(f"Error al crear transacción para viaje_id {tran_data.viaje_id}: {e}")
            raise BasedException(
                message=f"Error inesperado al crear la transacción: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def transaccion_finalizar(self, tran_id: int) -> TransaccionResponse:
        """
        Updates the 'estado' of an active transaction to 'Finalizada' and creates a corresponding movement.

        Args:
            tran_id (int): The ID of the transaction to finalize.

        Returns:
            TransaccionResponse: The updated transaction object.

        Raises:
            EntityNotFoundException: If the transaction with the given ID is not found.
            BasedException: If the transaction is not in 'Activa' state or for unexpected errors.
        """
        try:
            # 1. Obtener la transacción y validar su estado (usamos repo sólo para leer)
            tran = await self.get_transaccion(tran_id)
            if tran is None:
                raise EntityNotFoundException(f"La transacción con ID '{tran_id}' no fue encontrada.")

            if tran.estado != "Proceso":
                raise BasedException(
                    message=f"La transacción no se puede finalizar porque su estado es '{tran.estado}'. Solo las transacciones en estado 'Proceso' pueden finalizarse.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # 2. Se obtiene sumatoria de pesadas para setear peso real
            pesada = await self.pesadas_service.get_pesada_acumulada(tran_id=tran.id)
            peso_acc = Decimal(getattr(pesada, 'peso', 0) or 0)

            # 3. Ejecutar operaciones en una única transacción DB
            async with DatabaseConfiguration._async_session() as session:
                async with session.begin():
                    # Recuperar objeto Transacciones ORM
                    from sqlalchemy import select as _select
                    result = await session.execute(_select(Transacciones).where(Transacciones.id == int(tran_id)))
                    tran_obj = result.scalar_one_or_none()
                    if tran_obj is None:
                        raise EntityNotFoundException(f"Transacción con ID {tran_id} no encontrada (dentro de sesión).")

                    # Validar tipo exacto: 'Despacho' o 'Recibo'
                    tipo_tran_raw = getattr(tran_obj, 'tipo', None)
                    if tipo_tran_raw is None:
                        raise BasedException(message="Transacción sin campo 'tipo'.", status_code=status.HTTP_400_BAD_REQUEST)
                    tipo_lower = str(tipo_tran_raw).strip().lower()
                    if tipo_lower == 'despacho':
                        mov_tipo = 'Salida'
                        almacen_id = getattr(tran_obj, 'origen_id', None)
                    elif tipo_lower == 'recibo':
                        mov_tipo = 'Entrada'
                        almacen_id = getattr(tran_obj, 'destino_id', None) or getattr(tran_obj, 'origen_id', None)
                    else:
                        raise BasedException(message=f"Tipo de transacción '{tipo_tran_raw}' no soportado para finalización automática.", status_code=status.HTTP_400_BAD_REQUEST)

                    if almacen_id is None:
                        raise BasedException(message="No se encontró almacenamiento asociado (origen/destino) para crear movimiento.", status_code=status.HTTP_400_BAD_REQUEST)

                    # Capturar valores previos para auditoría de la transacción
                    valor_prev = {
                        'estado': getattr(tran_obj, 'estado', None),
                        'fecha_fin': getattr(tran_obj, 'fecha_fin', None),
                        'peso_real': getattr(tran_obj, 'peso_real', None)
                    }

                    # Aplicar cambios a la transacción
                    tran_obj.estado = 'Finalizada'
                    tran_obj.fecha_fin = now_local()
                    tran_obj.peso_real = peso_acc

                    # --- Obtener saldo anterior desde la vista VAlmMateriales ---
                    from database.models import VAlmMateriales, Movimientos, AlmacenamientosMateriales
                    saldo_anterior = Decimal('0')
                    try:
                        res = await session.execute(_select(VAlmMateriales).where(VAlmMateriales.almacenamiento_id == int(almacen_id), VAlmMateriales.material_id == int(getattr(tran_obj, 'material_id', 0))))
                        vrow = res.scalar_one_or_none()
                        if vrow is not None:
                            saldo_anterior = Decimal(getattr(vrow, 'saldo', 0) or 0)
                    except Exception as e_saldo:
                        log.error(f"Error consultando saldo anterior en VAlmMateriales: {e_saldo}")

                    # Calcular saldo nuevo
                    if mov_tipo == 'Salida':
                        saldo_nuevo = saldo_anterior - peso_acc
                    else:
                        saldo_nuevo = saldo_anterior + peso_acc

                    # Crear objeto Movimientos ORM
                    mov_obj = Movimientos(
                        transaccion_id=int(tran_id),
                        almacenamiento_id=int(almacen_id),
                        material_id=int(getattr(tran_obj, 'material_id', None)),
                        tipo=mov_tipo,
                        accion='Automatico',
                        observacion=None,
                        peso=peso_acc,
                        saldo_anterior=saldo_anterior,
                        saldo_nuevo=saldo_nuevo
                    )
                    session.add(mov_obj)
                    await session.flush()
                    await session.refresh(mov_obj)

                    # Actualizar tabla almacenamientos_materiales (registro existente) con nuevo saldo
                    try:
                        # Intentar actualizar el registro existente
                        update_stmt = (
                            sqlalchemy_update(AlmacenamientosMateriales)
                            .where(AlmacenamientosMateriales.c.almacenamiento_id == int(almacen_id))
                            .where(AlmacenamientosMateriales.c.material_id == int(getattr(tran_obj, 'material_id', 0)))
                            .values(saldo=saldo_nuevo, fecha_hora=now_local(), usuario_id=current_user_id.get())
                        )
                        res_update = await session.execute(update_stmt)
                        # Si no se actualizó ninguna fila, insertar el registro
                        rowcount = getattr(res_update, 'rowcount', None)
                        if not rowcount:
                            insert_stmt = AlmacenamientosMateriales.insert().values(
                                almacenamiento_id=int(almacen_id),
                                material_id=int(getattr(tran_obj, 'material_id', 0)),
                                saldo=saldo_nuevo,
                                fecha_hora=now_local(),
                                usuario_id=current_user_id.get()
                            )
                            await session.execute(insert_stmt)
                    except Exception as e_update_alm:
                        log.error(f"Error actualizando almacenamientos_materiales para almacen {almacen_id}: {e_update_alm}")

                    # Flush/commit handled by context manager

                    # Auditoría: construir valor nuevo para la transacción
                    valor_new = {
                        'estado': getattr(tran_obj, 'estado', None),
                        'fecha_fin': getattr(tran_obj, 'fecha_fin', None),
                        'peso_real': getattr(tran_obj, 'peso_real', None)
                    }

                    # Registrar auditoría para transacción
                    try:
                        audit_tr = AnyUtils.serialize_data(valor_prev)
                        await self._repo.auditor.log_audit(
                            audit_log_data=__import__('schemas.logs_auditoria_schema', fromlist=['LogsAuditoriaCreate']).LogsAuditoriaCreate(
                                entidad='transacciones',
                                entidad_id=str(tran_obj.id),
                                accion='UPDATE',
                                valor_anterior=AnyUtils.serialize_data(valor_prev),
                                valor_nuevo=AnyUtils.serialize_data(valor_new),
                                usuario_id=current_user_id.get()
                            )
                        )
                    except Exception as e_aud_tr:
                        log.error(f"No se pudo registrar auditoría para transacción {tran_id}: {e_aud_tr}")

                    # Registrar auditoría para movimiento creado
                    try:
                        await self.mov_service._repo.auditor.log_audit(
                            audit_log_data=__import__('schemas.logs_auditoria_schema', fromlist=['LogsAuditoriaCreate']).LogsAuditoriaCreate(
                                entidad='movimientos',
                                entidad_id=str(getattr(mov_obj, 'id', None)),
                                accion='CREATE',
                                valor_anterior=None,
                                valor_nuevo=AnyUtils.serialize_orm_object(mov_obj),
                                usuario_id=current_user_id.get()
                            )
                        )
                    except Exception as e_aud_mov:
                        log.error(f"No se pudo registrar auditoría para movimiento asociado a transacción {tran_id}: {e_aud_mov}")

                    # Refrescar transaccion
                    await session.refresh(tran_obj)

                    # Mapear a esquema de respuesta
                    from schemas.transacciones_schema import TransaccionResponse as _TR
                    updated_resp = _TR.model_validate(tran_obj)

            # Fin de la sesión/commit
            return updated_resp

        except EntityNotFoundException as e:
            raise e
        except BasedException as e:
            raise e
        except Exception as e:
            log.error(f"Error al finalizar transacción con ID {tran_id}: {e}")
            raise BasedException(
                message=f"Error inesperado al finalizar la transacción : {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

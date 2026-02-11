from decimal import Decimal
from typing import List, Optional, Tuple

from fastapi_pagination import Page, Params
from sqlalchemy import select, func
from sqlalchemy import update as sqlalchemy_update
from starlette import status

from core.config.context import current_user_id
from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
from database.connection import DatabaseConfiguration
from database.models import Transacciones, Bls
from repositories.bls_repository import BlsRepository
from repositories.flotas_repository import FlotasRepository
from repositories.transacciones_repository import TransaccionesRepository
from repositories.viajes_repository import ViajesRepository
from schemas.transacciones_schema import TransaccionResponse, TransaccionCreate, TransaccionUpdate, TransaccionCreateExt
from services.almacenamientos_service import AlmacenamientosService
from services.materiales_service import MaterialesService
from services.movimientos_service import MovimientosService
from services.pesadas_service import PesadasService
from utils.any_utils import AnyUtils
from utils.logger_util import LoggerUtil
from utils.time_util import now_local

log = LoggerUtil()

class TransaccionesService:

    def __init__(
        self,
        tran_repository: TransaccionesRepository,
        pesadas_service: PesadasService,
        mov_service: MovimientosService,
        alm_service: AlmacenamientosService = None,
        mat_service: MaterialesService = None,
        viajes_repository: ViajesRepository = None,
        bls_repository: BlsRepository = None,
        flotas_repository: FlotasRepository = None,
    ) -> None:
        self._repo = tran_repository
        self.pesadas_service = pesadas_service
        self.mov_service = mov_service
        self.alm_service = alm_service
        self.mat_service = mat_service
        self.viajes_repo = viajes_repository
        self.bls_repo = bls_repository
        self.flotas_repo = flotas_repository

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

    async def transaccion_finalizar(self, tran_id: int) -> Tuple[TransaccionResponse, Optional[dict]]:
        """
        Updates the 'estado' of an active transaction to 'Finalizada' and creates a corresponding movement.

        Args:
            tran_id (int): The ID of the transaction to finalize.

        Returns:
            tuple: (TransaccionResponse, Optional[dict]) - La transacción actualizada y el resultado de la notificación (si aplica)

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
            # Usamos get_suma_peso_by_transaccion que funciona para cualquier tipo de transacción
            # incluyendo Traslados (no depende de JOINs con Viajes/Flotas)
            suma_pesadas = await self.pesadas_service.get_suma_peso_by_transaccion(tran_id=tran.id)
            peso_acc = Decimal(suma_pesadas.get('peso_total', 0) or 0) if suma_pesadas else Decimal('0')

            # Obtener el tipo de transacción para usar después del bloque de sesión
            tipo_tran_para_envio = str(tran.tipo).strip().lower() if tran.tipo else ''

            # 3. Ejecutar operaciones en una única transacción DB
            async with DatabaseConfiguration._async_session() as session:
                async with session.begin():
                    # Recuperar objeto Transacciones ORM
                    from sqlalchemy import select as _select
                    result = await session.execute(_select(Transacciones).where(Transacciones.id == int(tran_id)))
                    tran_obj = result.scalar_one_or_none()
                    if tran_obj is None:
                        raise EntityNotFoundException(f"Transacción con ID {tran_id} no encontrada (dentro de sesión).")

                    # Validar tipo exacto: 'Despacho', 'Recibo' o 'Traslado'
                    tipo_tran_raw = getattr(tran_obj, 'tipo', None)
                    if tipo_tran_raw is None:
                        raise BasedException(message="Transacción sin campo 'tipo'.", status_code=status.HTTP_400_BAD_REQUEST)
                    tipo_lower = str(tipo_tran_raw).strip().lower()

                    # Determinar configuración de movimientos según el tipo
                    if tipo_lower == 'despacho':
                        mov_config = [{'tipo': 'Salida', 'almacen_id': getattr(tran_obj, 'origen_id', None)}]
                    elif tipo_lower == 'recibo':
                        mov_config = [{'tipo': 'Entrada', 'almacen_id': getattr(tran_obj, 'destino_id', None) or getattr(tran_obj, 'origen_id', None)}]
                    elif tipo_lower == 'traslado':
                        origen_id = getattr(tran_obj, 'origen_id', None)
                        destino_id = getattr(tran_obj, 'destino_id', None)
                        if origen_id is None or destino_id is None:
                            raise BasedException(
                                message="Para transacciones de tipo Traslado se requiere origen_id y destino_id.",
                                status_code=status.HTTP_400_BAD_REQUEST
                            )
                        # Primero Salida del origen, luego Entrada al destino
                        mov_config = [
                            {'tipo': 'Salida', 'almacen_id': origen_id},
                            {'tipo': 'Entrada', 'almacen_id': destino_id}
                        ]
                    else:
                        raise BasedException(message=f"Tipo de transacción '{tipo_tran_raw}' no soportado para finalización automática.", status_code=status.HTTP_400_BAD_REQUEST)

                    # Validar que todos los almacenamientos estén definidos
                    for cfg in mov_config:
                        if cfg['almacen_id'] is None:
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

                    from database.models import VAlmMateriales, Movimientos, AlmacenamientosMateriales

                    movimientos_creados = []

                    # Crear movimientos según la configuración
                    for cfg in mov_config:
                        almacen_id = cfg['almacen_id']
                        mov_tipo = cfg['tipo']

                        # --- Obtener saldo anterior desde la vista VAlmMateriales ---
                        saldo_anterior = Decimal('0')
                        try:
                            res = await session.execute(_select(VAlmMateriales).where(VAlmMateriales.almacenamiento_id == int(almacen_id), VAlmMateriales.material_id == int(getattr(tran_obj, 'material_id', 0))))
                            vrow = res.scalar_one_or_none()
                            if vrow is not None:
                                saldo_anterior = Decimal(getattr(vrow, 'saldo', 0) or 0)
                        except Exception as e_saldo:
                            log.error(f"Error consultando saldo anterior en VAlmMateriales para almacen {almacen_id}: {e_saldo}")

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
                            accion='Automático',
                            observacion=None,
                            peso=peso_acc,
                            saldo_anterior=saldo_anterior,
                            saldo_nuevo=saldo_nuevo,
                            usuario_id=current_user_id.get()
                        )
                        session.add(mov_obj)
                        await session.flush()
                        await session.refresh(mov_obj)
                        movimientos_creados.append(mov_obj)

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

                    # Registrar auditoría para movimientos creados
                    for mov_obj in movimientos_creados:
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

            # Después de finalizar exitosamente, verificar si es la última transacción de tipo Recibo
            # para el viaje y ejecutar envío final automáticamente
            notificacion_resultado = await self._verificar_y_ejecutar_envio_final(updated_resp, tipo_tran_para_envio)

            return updated_resp, notificacion_resultado

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

    async def _verificar_y_ejecutar_envio_final(self, tran: TransaccionResponse, tipo_lower: str) -> Optional[dict]:
        """
        Verifica el tipo de transacción y ejecuta las acciones correspondientes:
        - Despacho (camiones): Actualiza estado_operador de la flota y envía notificación CamionCargue
        - Recibo (buques): Si es la última transacción del viaje, ejecuta el envío final

        Args:
            tran: La transacción que se acaba de finalizar
            tipo_lower: El tipo de transacción en minúsculas

        Returns:
            dict: Resultado de la notificación con 'success' (bool) y 'message' (str), o None si no aplica
        """
        # Manejar Despacho (camiones)
        if tipo_lower == 'despacho':
            return await self._ejecutar_finalizacion_camion(tran)

        # Solo aplica para transacciones de tipo Recibo (buques)
        if tipo_lower != 'recibo':
            return None

        viaje_id = tran.viaje_id
        if viaje_id is None:
            log.warning(f"Transacción {tran.id} de tipo Recibo sin viaje_id, no se puede verificar envío final")
            return

        try:
            # Contar transacciones pendientes (estado='Proceso') para este viaje
            pending_count = await self._repo.count_pending_by_viaje(viaje_id)

            log.info(f"Verificando envío final para viaje {viaje_id}: {pending_count} transacciones pendientes")

            if pending_count > 0:
                log.info(f"Aún quedan {pending_count} transacciones pendientes para viaje {viaje_id}, no se ejecuta envío final")
                return

            # No quedan transacciones pendientes, ejecutar envío final
            log.info(f"Última transacción finalizada para viaje {viaje_id}, ejecutando envío final automático")

            # Obtener el puerto_id del viaje
            viaje = await self.viajes_repo.get_by_id(viaje_id)
            if not viaje:
                log.error(f"No se encontró viaje con ID {viaje_id} para envío final")
                return

            puerto_id = viaje.puerto_id

            # Obtener las pesadas para el envío final
            from services.envio_final_service import fetch_preview_for_puerto, notify_envio_final

            pesadas_to_send = await fetch_preview_for_puerto(puerto_id, self.pesadas_service)

            log.info(f"EnvioFinal automático: lista preparada para envío para {puerto_id} con {len(pesadas_to_send)} items")

            # Loguear el contenido completo que se va a enviar
            try:
                import json
                pesadas_log = []
                for item in pesadas_to_send:
                    if hasattr(item, 'model_dump'):
                        pesadas_log.append(item.model_dump())
                    elif hasattr(item, '__dict__'):
                        pesadas_log.append(item.__dict__)
                    else:
                        pesadas_log.append(item)
                log.info(f"EnvioFinal automático - contenido a enviar para {puerto_id}: {json.dumps(pesadas_log, default=str, indent=2)}")
            except Exception as e_log:
                log.warning(f"No se pudo loguear el contenido del envío final: {e_log}")

            # Para ejecutar notify_envio_final necesitamos viajes_service
            # Como no lo tenemos directamente, usamos el método send_envio_final_external del viaje
            # Necesitamos crear una instancia temporal o usar otra estrategia

            # Convertir pesadas a formato requerido
            pesadas_converted = []
            for item in pesadas_to_send:
                try:
                    if hasattr(item, 'model_dump'):
                        obj = item.model_dump()
                    elif hasattr(item, 'dict'):
                        obj = item.dict()
                    elif hasattr(item, '__dict__'):
                        obj = item.__dict__
                    else:
                        obj = dict(item)
                except Exception:
                    obj = item if isinstance(item, dict) else {}
                obj['voyage'] = puerto_id
                pesadas_converted.append(obj)

            # Ejecutar envío final usando el servicio de API externa
            await self._ejecutar_envio_final_externo(puerto_id, pesadas_converted)

            log.info(f"EnvioFinal automático completado exitosamente para viaje {viaje_id} (puerto_id={puerto_id})")

        except Exception as e:
            # No lanzar excepción para no interrumpir el flujo de finalización de transacción
            log.error(f"Error al ejecutar envío final automático para viaje {viaje_id}: {e}", exc_info=True)

    async def _ejecutar_finalizacion_camion(self, tran: TransaccionResponse) -> Optional[dict]:
        """
        Ejecuta la lógica de finalización de camión (despacho):
        - Actualiza el estado_operador de la flota a False
        - Envía notificación a la API externa CamionCargue

        Args:
            tran: La transacción de despacho que se acaba de finalizar

        Returns:
            dict: Resultado con 'success' (bool), 'message' (str), y opcionalmente 'flota_actualizada' (bool)
        """
        from core.config.settings import get_settings
        from services.ext_api_service import ExtApiService
        from schemas.ext_api_schema import NotificationCargue
        from utils.any_utils import AnyUtils
        import httpx

        resultado = {
            'success': False,
            'message': '',
            'flota_actualizada': False
        }

        viaje_id = tran.viaje_id
        if viaje_id is None:
            log.warning(f"Transacción {tran.id} de tipo Despacho sin viaje_id, no se puede ejecutar finalización de camión")
            resultado['message'] = "Transacción sin viaje_id asociado"
            return resultado

        try:
            # Obtener el viaje
            viaje = await self.viajes_repo.get_by_id(viaje_id)
            if not viaje:
                log.error(f"No se encontró viaje con ID {viaje_id} para finalización de camión")
                resultado['message'] = f"No se encontró viaje con ID {viaje_id}"
                return resultado

            # Obtener la flota
            flota = await self.flotas_repo.get_by_id(viaje.flota_id)
            if not flota:
                log.error(f"No se encontró flota con ID {viaje.flota_id} para finalización de camión")
                resultado['message'] = f"No se encontró flota con ID {viaje.flota_id}"
                return resultado

            # Verificar que sea un camión
            if flota.tipo != "camion":
                log.warning(f"Flota {flota.id} no es de tipo camion, es {flota.tipo}. No se ejecuta finalización de camión")
                resultado['message'] = f"Flota no es de tipo camion, es {flota.tipo}"
                return resultado

            # Actualizar estado_operador de la flota a False
            try:
                from schemas.flotas_schema import FlotaUpdate
                update_data = FlotaUpdate(estado_operador=False)
                await self.flotas_repo.update(flota.id, update_data)
                resultado['flota_actualizada'] = True
                log.info(f"Estado operador de flota {flota.id} actualizado a False para viaje {viaje_id}")
            except Exception as e_flota:
                log.error(f"Error al actualizar estado de flota {flota.id}: {e_flota}")
                resultado['message'] = f"Error al actualizar estado de flota: {e_flota}"
                # Continuar con la notificación aunque falle la actualización de estado

            # Enviar notificación a API externa CamionCargue
            settings = get_settings()
            ext_service = ExtApiService()

            notification = NotificationCargue(
                truckPlate=flota.referencia,
                truckTransaction=viaje.puerto_id,
                weighingPitId=tran.pit,
                weight=tran.peso_real
            ).model_dump()

            endpoint = f"{settings.TG_API_URL}/api/v1/Metalsoft/CamionCargue"

            try:
                serialized = AnyUtils.serialize_data(notification)
                log.info(f"Notificación CamionCargue para flota {flota.referencia} con request: {serialized}")
                await ext_service.post(serialized, endpoint)
                log.info(f"Notificación CamionCargue enviada exitosamente para viaje {viaje_id} (puerto_id={viaje.puerto_id})")
                resultado['success'] = True
                resultado['message'] = "Notificación CamionCargue enviada exitosamente"
            except httpx.HTTPStatusError as e:
                # Intentar extraer un JSON de la respuesta; si no es JSON usar el texto
                try:
                    error_json = e.response.json()
                except Exception:
                    error_json = None

                if isinstance(error_json, dict):
                    msg = error_json.get('message') or error_json.get('error') or e.response.text
                else:
                    msg = e.response.text

                log.error(f"Notificación CamionCargue falló. API externa error: {e.response.status_code}: {e.response.text}")
                resultado['message'] = f"Notificación CamionCargue falló. API externa error: {msg}"
            except Exception as e_notify:
                log.error(f"Error inesperado al enviar notificación CamionCargue para flota {flota.referencia}: {e_notify}", exc_info=True)
                resultado['message'] = f"Error inesperado al enviar notificación: {e_notify}"

            return resultado

        except Exception as e:
            # No lanzar excepción para no interrumpir el flujo de finalización de transacción
            log.error(f"Error al ejecutar finalización de camión para viaje {viaje_id}: {e}", exc_info=True)
            resultado['message'] = f"Error al ejecutar finalización de camión: {e}"
            return resultado

    async def _ejecutar_envio_final_externo(self, puerto_id: str, pesadas: list) -> None:
        """
        Ejecuta el envío final a la API externa.

        Args:
            puerto_id: ID del puerto/viaje
            pesadas: Lista de pesadas a enviar
        """
        from core.config.settings import get_settings
        from services.ext_api_service import ExtApiService
        from decimal import Decimal
        from datetime import datetime, timezone
        from utils.time_util import now_local
        import uuid
        import json

        settings = get_settings()
        ext_service = ExtApiService()

        # Normalizar payloads
        payloads = []
        for item in pesadas:
            it = item if isinstance(item, dict) else {}

            peso_val = it.get('peso', None)
            try:
                if peso_val is None:
                    peso_str = "0"
                else:
                    peso_dec = Decimal(peso_val) if not isinstance(peso_val, str) else Decimal(peso_val)
                    peso_str = format(peso_dec.quantize(Decimal('0.00')), 'f')
            except Exception:
                peso_str = "0"

            fecha = it.get('fecha_hora', None)
            if fecha is None:
                fecha_iso = now_local().isoformat()
            else:
                try:
                    fecha_iso = fecha if isinstance(fecha, str) else (fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha))
                except Exception:
                    fecha_iso = str(fecha)

            payloads.append({
                "voyage": puerto_id,
                "referencia": it.get('referencia'),
                "consecutivo": int(it.get('consecutivo') or 0),
                "transaccion": int(it.get('transaccion') or 0),
                "pit": int(it.get('pit') or 0),
                "material": it.get('material') or "",
                "peso": peso_str,
                "puerto_id": it.get('puerto_id') or puerto_id,
                "fecha_hora": fecha_iso,
                "usuario_id": int(it.get('usuario_id') or 0),
                "usuario": it.get('usuario') or "",
            })

        if not payloads:
            log.warning(f"EnvioFinal automático: no hay payloads para enviar a {puerto_id}")
            return

        # Enviar solo el último registro (más reciente por fecha_hora)
        def _parse_date(v):
            try:
                if isinstance(v, str):
                    try:
                        return datetime.fromisoformat(v)
                    except Exception:
                        return datetime.fromisoformat(v.replace('Z', '+00:00'))
                return v
            except Exception:
                return datetime.min.replace(tzinfo=timezone.utc)

        last_item = max(payloads, key=lambda x: _parse_date(x.get('fecha_hora')))

        # Headers
        idempotency_key = f"{last_item.get('referencia') or ''}-{last_item.get('transaccion') or 0}"
        correlation_id = str(uuid.uuid4())
        headers = {"Idempotency-Key": idempotency_key, "X-Correlation-Id": correlation_id}

        endpoint = f"{settings.TG_API_URL}/api/v1/Metalsoft/EnvioFinal"

        # Loguear el payload final
        log.info(f"EnvioFinal automático - enviando a {endpoint}")
        log.info(f"EnvioFinal automático - headers: {json.dumps(headers)}")
        log.info(f"EnvioFinal automático - payload: {json.dumps(last_item, default=str)}")

        # Serializar y enviar
        serialized = AnyUtils.serialize_data(last_item)
        await ext_service.post(serialized, endpoint, extra_headers=headers)

        log.info(f"EnvioFinal automático - notificación enviada exitosamente para {puerto_id}")

    async def create_transaccion_ext(self, tran_ext: TransaccionCreateExt) -> TransaccionResponse:
        """
        Create a new transaction using the simplified external schema.
        Resolves names to IDs and calculates peso_meta from BLs.

        Args:
            tran_ext (TransaccionCreateExt): The simplified transaction data.

        Returns:
            TransaccionResponse: The created transaction object.

        Raises:
            EntityNotFoundException: If viaje, material, or almacenamiento is not found.
            EntityAlreadyRegisteredException: If a similar transaction already exists.
            BasedException: For unexpected errors during the creation process.
        """
        try:
            tipo_lower = tran_ext.tipo.strip().lower()

            # 1. Resolver material_id por nombre
            material = await self.mat_service.get_mat_by_name(tran_ext.material)
            if not material:
                raise EntityNotFoundException(f"No existe material con nombre '{tran_ext.material}'")
            material_id = material

            # 2. Variables para almacenar IDs resueltos
            origen_id = None
            destino_id = None
            viaje_id = tran_ext.viaje_id
            pit = tran_ext.pit
            ref1 = None
            peso_meta = Decimal('0')

            # 3. Resolver almacenamientos según tipo
            if tran_ext.origen:
                origen_id = await self.alm_service.get_mat_by_name(tran_ext.origen)
                if not origen_id:
                    raise EntityNotFoundException(f"No existe almacenamiento con nombre '{tran_ext.origen}'")

            if tran_ext.destino:
                destino_id = await self.alm_service.get_mat_by_name(tran_ext.destino)
                if not destino_id:
                    raise EntityNotFoundException(f"No existe almacenamiento con nombre '{tran_ext.destino}'")

            # 4. Si es Recibo o Despacho, obtener ref1 del viaje y calcular peso_meta
            bl_id = None
            if tipo_lower in ['recibo', 'despacho']:
                if viaje_id is None:
                    raise EntityNotFoundException("viaje_id es requerido para transacciones de tipo Recibo/Despacho")

                # Obtener viaje para ref1 (puerto_id)
                viaje = await self.viajes_repo.get_by_id(viaje_id)
                if not viaje:
                    raise EntityNotFoundException(f"No existe viaje con ID '{viaje_id}'")

                if tipo_lower == 'recibo':
                    # Para Recibo (buques): ref1 es el puerto_id del viaje
                    ref1 = viaje.puerto_id
                    # Calcular peso_meta sumando peso_bl de los BLs del viaje con el mismo material
                    peso_meta = await self._calcular_peso_meta_por_material(viaje_id, material_id)
                    if peso_meta <= 0:
                        log.warning(f"No se encontraron BLs para viaje {viaje_id} con material_id {material_id}. peso_meta = 0")
                else:
                    # Para Despacho (camiones): ref1 es la referencia (placa) de la flota
                    flota = await self.flotas_repo.get_by_id(viaje.flota_id)
                    if not flota:
                        raise EntityNotFoundException(f"No existe flota con ID '{viaje.flota_id}'")
                    ref1 = flota.referencia
                    # Tomar peso_meta directamente del viaje
                    peso_meta = Decimal(str(viaje.peso_meta)) if viaje.peso_meta else Decimal('0')
                    if peso_meta <= 0:
                        log.warning(f"El viaje {viaje_id} no tiene peso_meta definido. peso_meta = 0")

                    # Buscar el bl_id correspondiente al viaje de recibo (buque)
                    # El viaje de despacho tiene viaje_origen que contiene el puerto_id del viaje de recibo
                    if viaje.viaje_origen:
                        # Buscar el viaje de recibo por puerto_id
                        viaje_recibo = await self.viajes_repo.check_puerto_id(viaje.viaje_origen)
                        if viaje_recibo:
                            # Buscar el BL activo (estado_puerto=True) para ese viaje y material
                            bl = await self.bls_repo.get_bl_activo_por_material(viaje_recibo.id, material_id)
                            if bl:
                                bl_id = bl.id
                                log.info(f"BL encontrado para despacho: bl_id={bl_id}, viaje_origen={viaje.viaje_origen}")
                            else:
                                log.warning(f"No se encontró BL activo (estado_puerto=True) para viaje {viaje_recibo.id} con material_id {material_id}")
                        else:
                            log.warning(f"No se encontró viaje de recibo con puerto_id '{viaje.viaje_origen}'")

            # 5. Verificar si ya existe una transacción similar
            existing = await self._repo.find_one(viaje_id=viaje_id, material_id=material_id, tipo=tran_ext.tipo)
            if existing:
                raise EntityAlreadyRegisteredException(
                    f"Ya existe transacción de tipo '{tran_ext.tipo}' para viaje '{viaje_id}' con material '{tran_ext.material}'. ID de transacción existente: {existing.id}"
                )

            # 6. Crear el objeto TransaccionCreate
            tran_create = TransaccionCreate(
                material_id=material_id,
                tipo=tran_ext.tipo,
                viaje_id=viaje_id,
                pit=pit,
                ref1=ref1,
                fecha_inicio=now_local(),
                origen_id=origen_id,
                destino_id=destino_id,
                peso_meta=peso_meta,
                estado="Registrada",
                leido=False,
                bl_id=bl_id,
            )

            # 7. Crear la transacción
            tran_nueva = await self._repo.create(tran_create)
            log.info(f"Transacción creada: tipo={tran_ext.tipo}, viaje_id={viaje_id}, material={tran_ext.material}")

            return tran_nueva

        except EntityNotFoundException as e:
            raise e
        except EntityAlreadyRegisteredException as e:
            raise e
        except Exception as e:
            log.error(f"Error al crear transacción ext: {e}")
            raise BasedException(
                message=f"Error inesperado al crear la transacción: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def _calcular_peso_meta_por_material(self, viaje_id: int, material_id: int) -> Decimal:
        """
        Calcula el peso_meta sumando el peso_bl de todos los BLs del viaje que tengan el material especificado.

        Args:
            viaje_id: ID del viaje
            material_id: ID del material

        Returns:
            Decimal: Suma de peso_bl de los BLs que coinciden
        """
        try:
            # Usar el repositorio de BLs para obtener la suma
            query = (
                select(func.coalesce(func.sum(Bls.peso_bl), 0))
                .where(Bls.viaje_id == viaje_id)
                .where(Bls.material_id == material_id)
            )
            result = await self.bls_repo.db.execute(query)
            total = result.scalar_one_or_none()
            return Decimal(str(total)) if total else Decimal('0')
        except Exception as e:
            log.error(f"Error calculando peso_meta para viaje {viaje_id}, material {material_id}: {e}")
            return Decimal('0')


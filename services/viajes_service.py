from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

import httpx
from fastapi_pagination import Page, Params
from sqlalchemy import select
from starlette import status

from core.config.settings import get_settings
from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import (
    EntityAlreadyRegisteredException,
    EntityNotFoundException,
)
from database.models import VViajes
from repositories.viajes_repository import ViajesRepository
from schemas.bls_schema import BlsCreate, BlsExtCreate, BlsResponse, BlsUpdate, VBlsResponse
from schemas.ext_api_schema import NotificationCargue, NotificationBuque, NotificationPitCargue, NotificationBlsPeso
from schemas.flotas_schema import FlotasResponse, FlotaCreate
from schemas.transacciones_schema import TransaccionResponse
from schemas.viajes_schema import (
    ViajesResponse, ViajeCreate, ViajeBuqueExtCreate, ViajeUpdate, ViajesActResponse, ViajeCamionExtCreate,
    VViajesResponse
)
from services.bls_service import BlsService
from services.clientes_service import ClientesService
from services.ext_api_service import ExtApiService
from services.flotas_service import FlotasService
from services.materiales_service import MaterialesService
from services.transacciones_service import TransaccionesService
from utils.any_utils import AnyUtils
from utils.logger_util import LoggerUtil

log = LoggerUtil()

class ViajesService:

    def __init__(self, viajes_repository: ViajesRepository, mat_service : MaterialesService, flotas_service : FlotasService, feedback_service : ExtApiService, transacciones_service : TransaccionesService, bl_service : BlsService, client_service : ClientesService) -> None:
        self._repo = viajes_repository
        self.mat_service = mat_service
        self.flotas_service = flotas_service
        self.bls_service = bl_service
        self.clientes_service = client_service
        self.feedback_service = feedback_service
        self.transacciones_service= transacciones_service

    async def create(self, viaje: ViajeCreate) -> ViajesResponse:
        """
        Create a new viaje in the database.

        Args:
            viaje (ViajeCreate): The viaje data to create.

        Returns:
            ViajesResponse: The created viaje object.

        Raises:
            BasedException: If creation fails due to database or other errors.
        """
        try:
            return await self._repo.create(viaje)
        except Exception as e:
            log.error(f"Error al crear viaje: {e}")
            raise BasedException(
                message="Error al crear el viaje",
                status_code=409
            )

    async def update(self, viaje_id: int, viaje: ViajeUpdate) -> Optional[ViajesResponse]:
        """
        Update an existing viaje by ID.

        Args:
            viaje_id (int): The ID of the viaje to update.
            viaje (ViajeUpdate): The updated viaje data.

        Returns:
            Optional[ViajesResponse]: The updated viaje object, or None if not found.

        Raises:
            BasedException: If update fails due to database or other errors.
        """
        try:
            return await self._repo.update(viaje_id, viaje)
        except Exception as e:
            log.error(f"Error al actualizar viaje con ID {viaje_id}: {e}")
            raise BasedException(
                message=f"Error al actualizar el viaje con ID {viaje_id}",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete(self, viaje_id: int) -> bool:
        """
        Delete a viaje by ID.

        Args:
            viaje_id (int): The ID of the viaje to delete.

        Returns:
            bool: True if deletion was successful, False otherwise.

        Raises:
            BasedException: If deletion fails due to database or other errors.
        """
        try:
            return await self._repo.delete(viaje_id)
        except Exception as e:
            log.error(f"Error al eliminar viaje con ID {viaje_id}: {e}")
            raise BasedException(
                message=f"Error al eliminar el viaje con ID {viaje_id}",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get(self, viaje_id: int) -> Optional[ViajesResponse]:
        """
        Retrieve a viaje by ID.

        Args:
            viaje_id (int): The ID of the viaje to retrieve.

        Returns:
            Optional[ViajesResponse]: The viaje object if found, None otherwise.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            return await self._repo.get_by_id(viaje_id)
        except Exception as e:
            log.error(f"Error al obtener el viaje con ID {viaje_id}: {e}")
            raise BasedException(
                message=f"Error al obtener el viaje con ID {viaje_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all(self) -> List[ViajesResponse]:
        """
        Retrieve all viajes from the database.

        Returns:
            List[ViajesResponse]: A list of all viaje objects.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            return await self._repo.get_all()
        except Exception as e:
            log.error(f"Error al obtener listado de viajes: {e}")
            raise BasedException(
                message="Error al obtener listado de viajes",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_viaje_by_puerto_id(self, puerto_id: str) -> Optional[ViajesResponse]:
        """
        Find a viaje by its puerto_id.

        Args:
            puerto_id (str): The puerto_id to filter the viaje.

        Returns:
            Optional[ViajesResponse]: The viaje object if found, None otherwise.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            return await self._repo.check_puerto_id(puerto_id)
        except Exception as e:
            log.error(f"Error obteniendo viaje con puerto_id {puerto_id}: {e}")
            raise BasedException(
                message=f"Error al obtener el viaje con puerto_id {puerto_id}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_buques_activos(self) -> List[ViajesActResponse]:
        """
        Retrieve all active buques from the database.

        Returns:
            List[ViajesActResponse]: A list of active buque objects.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            return await self._repo.get_buques_disponibles()
        except Exception as e:
            log.error(f"Error al obtener buques activos: {e}")
            raise BasedException(
                message="Error al obtener buques activos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pag_camiones_activos(self, truck_plate: Optional[str] = None, params: Params = Params()) -> Page[
        VViajesResponse]:
        """
        Retrieve a paginated list of active camiones, optionally filtered by truck_plate.

        Args:
            truck_plate (Optional[str]): The truck plate to filter camiones (optional).
            params (Params): Pagination parameters.

        Returns:
            Page[VViajesResponse]: A paginated list of active camiones.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            query = (
                select(VViajes)
                .where(VViajes.tipo == 'camion')
                .where(VViajes.fecha_salida.is_(None))
            )
            if truck_plate is not None:
                query = query.where(VViajes.referencia == truck_plate)
            return await self._repo.get_all_paginated(query=query, params=params)
        except Exception as e:
            log.error(f"Error al obtener camiones activos con placa (opcional) {truck_plate}: {e}")
            raise BasedException(
                message="Error al obtener camiones activos",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_buque_nuevo(self, viaje_create: ViajeBuqueExtCreate) -> ViajesResponse:
        """
        Create a new buque viaje, including associated flota if it doesn't exist.

        Args:
            viaje_create (ViajeBuqueExtCreate): The buque viaje data to create.

        Returns:
            ViajesResponse: The created buque viaje object.

        Raises:
            EntityAlreadyRegisteredException: If puerto_id already exists.
            EntityNotFoundException: If flota cannot be retrieved.
            BasedException: If creation fails due to database or other errors.
        """
        try:
            # 1. Validar si puerto_id ya existe
            if await self.get_viaje_by_puerto_id(viaje_create.puerto_id):
                raise EntityAlreadyRegisteredException(f"Ya existe un viaje con puerto_id '{viaje_create.puerto_id}'")

            # 2. Crear la flota si no existe
            nueva_flota = FlotaCreate.model_validate(viaje_create)
            await self.flotas_service.create_flota_if_not_exists(nueva_flota)

            # 3. Obtener flota (ya creada o existente)
            flota = await self.flotas_service.get_flota_by_ref(ref=viaje_create.referencia)
            if not flota:
                raise EntityNotFoundException(f"No se pudo obtener flota con tipo '{viaje_create.tipo}' y ref '{viaje_create.referencia}'")

            # 4. Ajustar el schema al requerido
            viaje_data = viaje_create.model_dump(exclude={"referencia", "estado"})
            viaje_data["flota_id"] = flota.id

            # 5. Crear registro en la base de datos
            db_viaje = ViajeCreate(**viaje_data)
            await self._repo.create(db_viaje)

            # 6. Consultar el viaje recién añadido
            created_viaje = await self.get_viaje_by_puerto_id(viaje_create.puerto_id)
            if not created_viaje:
                raise EntityNotFoundException("Error al recuperar el viaje recién creado")

            return ViajesResponse(**created_viaje.__dict__)
        except (EntityAlreadyRegisteredException, EntityNotFoundException) as e:
            raise e
        except Exception as e:
            log.error(f"Error inesperado al crear buque y/o viaje con puerto_id {viaje_create.puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_buque_load(self, bl_input: BlsExtCreate) -> BlsResponse:
        """
        Create a new BL (Bill of Lading) for a buque viaje.

        Args:
            bl_input (BlsExtCreate): The BL data to create.

        Returns:
            BlsResponse: The created BL object.

        Raises:
            EntityNotFoundException: If viaje, material, or client is not found.
            EntityAlreadyRegisteredException: If BL number already exists.
            BasedException: If creation fails due to database or other errors.
        """
        try:
            # Verifica que el viaje asociado exista
            viaje = await self.get_viaje_by_puerto_id(bl_input.puerto_id)
            if not viaje:
                raise EntityNotFoundException(f"No existe un viaje con puerto_id='{bl_input.puerto_id}'")

            # Verifica que no exista un BL con el mismo número
            existing_bl = await self.bls_service.get_bl_by_num(bl_input.no_bl)
            if existing_bl:
                raise EntityAlreadyRegisteredException(f"El número de BL '{bl_input.no_bl}' ya fue registrado")

            # Obtiene el ID del material
            material_id = await self.mat_service.get_mat_by_name(bl_input.material_name)
            if material_id is None:
                raise EntityNotFoundException(f"El material '{bl_input.material_name}' no existe")

            # Obtiene el ID del cliente
            cliente_find = await self.clientes_service.get_cliente_by_name(bl_input.cliente_name)
            if cliente_find is None:
                cliente_find = await self.clientes_service.get_cliente_by_name("CUSTOMER COMPANY NAME")
                #raise EntityNotFoundException(f"El cliente '{bl_input.cliente_name}' no existe")

            # Prepara los datos para la creación
            bl_data = bl_input.model_dump(exclude={"material_name", "puerto_id", "cliente_name"})
            bl_data.update({
                "cliente_id": cliente_find.id,
                "material_id": material_id,
                "viaje_id": viaje.id,
            })

            # Crea la instancia de BL
            db_bl = BlsCreate(**bl_data)
            await self.bls_service.create(db_bl)

            # Retorna la entidad creada
            created_bl = await self.bls_service.get_bl_by_num(bl_input.no_bl)
            if not created_bl:
                raise BasedException(
                    message="Error al recuperar el BL recién creado",
                    status_code=status.HTTP_404_NOT_FOUND
                )
            return BlsResponse.model_validate(created_bl)
        except EntityNotFoundException as e:
            raise e
        except EntityAlreadyRegisteredException as e:
            raise e
        except Exception as e:
            log.error(f"Error creando BL con no_bl {bl_input.no_bl}: {e}")
            raise BasedException(
                message=f"Error al crear el BL :{e}",
                status_code=status.HTTP_424_FAILED_DEPENDENCY
            )

    async def create_camion_nuevo(self, viaje_create: ViajeCamionExtCreate) -> ViajesResponse:
        """
        Create a new camion viaje, including associated flota and material if valid.

        Args:
            viaje_create (ViajeCamionExtCreate): The camion viaje data to create.

        Returns:
            ViajesResponse: The created camion viaje object.

        Raises:
            EntityAlreadyRegisteredException: If puerto_id already exists.
            EntityNotFoundException: If flota or material cannot be retrieved.
            BasedException: If creation fails due to database or other errors.
        """
        try:
            # 1. Validar si puerto_id ya existe
            if await self.get_viaje_by_puerto_id(viaje_create.puerto_id):
                raise EntityAlreadyRegisteredException(f"Ya existe una cita con id '{viaje_create.puerto_id}'")

            # 2. Crear la flota si no existe
            nueva_flota = FlotaCreate.model_validate(viaje_create)
            await self.flotas_service.create_flota_if_not_exists(nueva_flota)

            # 3. Obtener flota (ya creada o existente)
            flota = await self.flotas_service.get_flota_by_ref(ref=viaje_create.referencia)
            if not flota:
                raise EntityNotFoundException(f"No se pudo obtener flota con tipo '{viaje_create.tipo}' y ref '{viaje_create.referencia}'")

            # 4. Obtener material_id basado en el nombre del material
            material_id = await self.mat_service.get_mat_by_name(viaje_create.material_name)
            if material_id is None:
                raise EntityNotFoundException(f"Material '{viaje_create.material_name}' no existe")

            # 5. Ajustar el schema al requerido
            viaje_data = viaje_create.model_dump(exclude={"referencia", "puntos"})
            viaje_data["flota_id"] = flota.id
            viaje_data["material_id"] = material_id

            # 6. Crear registro en la base de datos
            db_viaje = ViajeCreate(**viaje_data)
            await self._repo.create(db_viaje)

            # 7. Consultar el viaje recién añadido
            created_viaje = await self.get_viaje_by_puerto_id(viaje_create.puerto_id)
            if not created_viaje:
                raise EntityNotFoundException("Error al recuperar la cita recién creada")

            return ViajesResponse(**created_viaje.__dict__)
        except (EntityAlreadyRegisteredException, EntityNotFoundException) as e:
            raise e
        except Exception as e:
            log.error(f"Error inesperado a crear camion y/o cita con puerto_id {viaje_create.puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def chg_estado_flota(self, puerto_id: str, estado_puerto: Optional[bool] = None, estado_operador: Optional[bool] = None) -> FlotasResponse:
        """
        Change the status of a flota associated with a viaje.

        Args:
            puerto_id (str): The puerto_id of the viaje.
            estado_puerto (bool): The puerto status value for the flota.
            estado_operador (bool): The operador status value for the flota.

        Returns:
            FlotasResponse: The updated flota object.

        Raises:
            EntityNotFoundException: If viaje or flota is not found.
            BasedException: If update fails due to database or other errors.
        """
        try:
            viaje = await self.get_viaje_by_puerto_id(puerto_id)
            if not viaje:
                raise EntityNotFoundException(f"Viaje con puerto_id: '{puerto_id}' no existe")

            flota = await self.flotas_service.get_flota(viaje.flota_id)
            if not flota:
                raise EntityNotFoundException(f"Flota con id '{viaje.flota_id}' no existe")

            updated_flota = await self.flotas_service.update_status(flota,estado_puerto, estado_operador)

            # Solo notificar si el cambio de estado es para finalizado
            if estado_operador is not None:
                tran = None
                bl = None
                if flota.tipo == "camion":
                    tran = await self.transacciones_service.get_tran_by_viaje(viaje.id)
                    if not tran:
                        raise EntityNotFoundException(f"Transacción para la cita: '{viaje.id}' no existe")
                    # Si la transacción no tiene peso_real, intentar finalizarla para calcular y guardar el peso
                    try:
                        if getattr(tran, 'peso_real', None) in (None, 0):
                            # Intentar finalizar; esto actualizará peso_real desde las pesadas acumuladas
                            tran = await self.transacciones_service.transaccion_finalizar(tran.id)
                    except Exception as e_final:
                        # No bloquear la operación por fallo al finalizar, pero loguear la situación
                        log.warning(f"No se pudo finalizar transacción {getattr(tran, 'id', None)} antes de notificar: {e_final}")
                if flota.tipo == "buque":
                    bl = await self.bls_service.get_bl_by_viaje(viaje.id)
                    if not bl:
                        raise EntityNotFoundException(f"No se encontró BL(s) para la cita: '{viaje.id}'.")

                await self.send_notification(flota, viaje, tran, bl)

            return updated_flota
        except EntityNotFoundException as e:
            raise e
        except Exception as e:
            log.error(f"Error al cambiar estado de flota con puerto_id {puerto_id}: {str(e)}")
            raise BasedException(
                message=f"Error al cambiar el estado de flota con puerto_id {puerto_id} : {str(e)}",
                status_code=status.HTTP_424_FAILED_DEPENDENCY
            )

    async def chg_estado_carga(self, bl_num: str, estado_puerto: Optional[bool] = None, estado_operador: Optional[bool] = None) -> BlsResponse:
        """
        Change the release status of a BL.

        Args:
            bl_num (str): The BL identifier.
            estado_puerto (bool): The realese status value changed by the PBCU.
            estado_operador (bool): The realese status value changed by the operator.

        Returns:
            BlsResponse: The updated BL object.

        Raises:
            EntityNotFoundException: If viaje or flota is not found.
            BasedException: If update fails due to database or other errors.
        """
        try:
            existing_bl = await self.bls_service.get_bl_by_num(bl_num)
            if not existing_bl:
                raise EntityNotFoundException(f"No existe BL'{bl_num}'")

            #Se crea diccionario
            update_fields = {}

            # Se valida el estado a actualizar
            if estado_puerto is not None:
                update_fields["estado_puerto"] = estado_puerto

            if estado_operador is not None:
                update_fields["estado_operador"] = estado_operador

            update_data = BlsUpdate(**update_fields)
            update_bl = await self.bls_service.update(existing_bl.id, update_data)
            return update_bl
        except EntityNotFoundException as e:
            raise e
        except Exception as e:
            log.error(f"Error al cambiar estado puerto de BL {bl_num}: {e}")
            raise BasedException(
                message=f"Error al cambiar el estado puerto de BL {bl_num}: {e}",
                status_code=status.HTTP_424_FAILED_DEPENDENCY
            )

    async def chg_camion_ingreso(self, puerto_id: str, fecha: datetime) -> NotificationPitCargue:
        """
        Update the arrival date of a camion viaje.

        Args:
            puerto_id (str): The puerto_id of the viaje.
            fecha (datetime): The arrival date to set.

        Returns:
            ViajesResponse: The updated viaje object.

        Raises:
            EntityNotFoundException: If viaje or flota is not found or flota type is not 'camion'.
            BasedException: If update fails due to database or other errors.
        """
        try:
            viaje = await self.get_viaje_by_puerto_id(puerto_id)
            if not viaje:
                raise EntityNotFoundException(f"Viaje con puerto_id: '{puerto_id}' no existe")

            flota = await self.flotas_service.get_flota(viaje.flota_id)
            if not flota:
                raise EntityNotFoundException(f"Flota con id '{viaje.flota_id}' no existe")
            if flota.tipo != "camion":
                raise EntityNotFoundException(
                    f"La flota es del tipo '{flota.tipo}' diferente al tipo esperado 'camion'")

            tran = await self.transacciones_service.get_tran_by_viaje(viaje.id)
            if not tran:
                raise EntityNotFoundException(f"Transacción para la cita: '{viaje.puerto_id}' no existe")

            update_fields = {
                "fecha_llegada": fecha,
            }
            update_data = ViajeUpdate(**update_fields)
            await self._repo.update(viaje.id, update_data)

            notification = NotificationPitCargue(
                cargoPit=tran.pit,
            ).model_dump()
            log.info(f"Ingreso actualizado para viaje: {viaje.puerto_id} a {fecha}")

            return notification
        except EntityNotFoundException as e:
            raise e
        except Exception as e:
            log.error(f"Error al actualizar ingreso de camión con puerto_id {puerto_id}: {e}")
            raise BasedException(
                message=f"Error al actualizar ingreso de camión con puerto_id {puerto_id}",
                status_code=status.HTTP_409_CONFLICT
            )

    async def chg_camion_salida(self, puerto_id: str, fecha: datetime, peso: Decimal) -> ViajesResponse:
        """
        Update the departure date and actual weight of a camion viaje.

        Args:
            puerto_id (str): The puerto_id of the viaje.
            fecha (datetime): The departure date to set.
            peso (Decimal): The actual weight to set.

        Returns:
            ViajesResponse: The updated viaje object.

        Raises:
            EntityNotFoundException: If viaje or flota is not found or flota type is not 'camion'.
            BasedException: If update fails due to database or other errors.
        """
        try:
            viaje = await self.get_viaje_by_puerto_id(puerto_id)
            if not viaje:
                raise EntityNotFoundException(f"Viaje con puerto_id: '{puerto_id}' no existe")

            flota = await self.flotas_service.get_flota(viaje.flota_id)
            if not flota:
                raise EntityNotFoundException(f"Flota con id '{viaje.flota_id}' no existe")
            if flota.tipo != "camion":
                raise EntityNotFoundException(
                    f"La flota es del tipo '{flota.tipo}' diferente al tipo esperado 'camion'")

            update_fields = {
                "fecha_salida": fecha,
                "peso_real": peso
            }
            update_data = ViajeUpdate(**update_fields)
            updated = await self._repo.update(viaje.id, update_data)
            log.info(f"Salida actualizada para viaje: {viaje.puerto_id} a {fecha} con peso {peso}")
            return updated
        except EntityNotFoundException as e:
            raise e
        except Exception as e:
            log.error(f"Error al actualizar salida de camion con puerto_id {puerto_id}: {e}")
            raise BasedException(
                message=f"Error al actualizar salida de camion con puerto_id {puerto_id}",
                status_code=status.HTTP_409_CONFLICT
            )

    async def send_notification(self, flota : FlotasResponse, viaje : ViajesResponse, tran: Optional[TransaccionResponse], bl: Optional[List[VBlsResponse]]) -> None:
        """
        Helper method to send notifications for camion or buque changes.

        Args:
            flota (str): The flota object.
            viaje (str): The viaje object.
            tran (Optional[TransaccionResponse]): The transaction optional object (for camion).
            bl(Optional[List[VBlsResponse]]): The BL Data optional object.

        Raises:
            BasedException: If the notification to external API fails.
        """

        if flota.tipo == "camion":

            notification = NotificationCargue(
                truckPlate=flota.referencia,
                truckTransaction=viaje.puerto_id,
                weighingPitId=tran.pit,
                weight=tran.peso_real
            ).model_dump()
            endpoint = f"{get_settings().TG_API_URL}/api/v1/Metalsoft/CamionCargue"
        else:
            #Se mapean los registros de interes del BL
            dt_bl = [
                NotificationBlsPeso(
                    noBL=bl_item.no_bl,
                    voyage=bl_item.viaje,
                    weightBl=bl_item.peso_real
                ).model_dump()
                for bl_item in bl
            ] if bl else None

            notification = NotificationBuque(
                voyage=viaje.puerto_id,
                status="Finished",
                data= dt_bl
            ).model_dump()
            endpoint = f"{get_settings().TG_API_URL}/api/v1/Metalsoft/FinalizaBuque"

        try:
            serialized = AnyUtils.serialize_data(notification)
            log.info(f"Notificación flota {flota.referencia} con request: {serialized}")
            await self.feedback_service.post(serialized, endpoint)
        except httpx.HTTPStatusError as e:
            # Intentar extraer un JSON de la respuesta; si no es JSON usar el texto
            try:
                error_json = e.response.json()
            except Exception:
                error_json = None

            if isinstance(error_json, dict):
                # Preferir keys comunes que contengan el mensaje
                msg = error_json.get('message') or error_json.get('error') or e.response.text
            else:
                msg = e.response.text

            log.error(f"Notificación de cargue falló. API externa error: {e.response.status_code}: {e.response.text}")
            raise BasedException(
                message=f"Notificación de cargue falló. API externa error: {msg}",
                status_code=e.response.status_code
            ) from e
        except Exception as e:
            log.error(f"Error inesperado al enviar notificación de cargue para flota {flota.referencia}: {e}", exc_info=True)
            raise BasedException(
                message=f"Error inesperado al enviar notificación de cargue: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def send_envio_final_external(self, voyage: str, envio_list: list, external_accepts_list: Optional[bool] = None) -> None:
        """
        Envía la lista de 'envio final' a la API externa en el endpoint /api/v1/Metalsoft/EnvioFinal.

        - voyage: puerto_id del viaje
        - envio_list: lista de objetos que siguen la forma de VPesadasAcumResponse (o dicts compatibles)
        - external_accepts_list: si None, se consulta get_settings().TG_API_ACCEPTS_LIST; si False, se enviará un POST por cada elemento.
        """
        try:
            from core.config.settings import get_settings
            from utils.any_utils import AnyUtils
            from decimal import Decimal
            from datetime import datetime, timezone
            import asyncio
            import httpx

            settings = get_settings()
            if external_accepts_list is None:
                external_accepts_list = bool(settings.TG_API_ACCEPTS_LIST)

            # Normalizar cada item a dict con campos esperados
            payloads = []
            for item in envio_list:
                if isinstance(item, dict):
                    it = item
                else:
                    try:
                        it = item.model_dump() if hasattr(item, 'model_dump') else item.__dict__
                    except Exception:
                        it = {k: getattr(item, k, None) for k in ['referencia', 'consecutivo', 'transaccion', 'pit', 'material', 'peso', 'puerto_id', 'fecha_hora', 'usuario_id', 'usuario']}

                peso_val = it.get('peso', None)
                try:
                    if peso_val is None:
                        peso_str = "0"
                    else:
                        peso_dec = Decimal(peso_val) if not isinstance(peso_val, str) else Decimal(peso_val)
                        peso_str = format(peso_dec.quantize(Decimal('0.00')), 'f')
                except Exception:
                    try:
                        peso_str = format(Decimal(str(peso_val)), 'f')
                    except Exception:
                        peso_str = "0"

                fecha = it.get('fecha_hora', None)
                if fecha is None:
                    fecha_iso = datetime.now(timezone.utc).isoformat()
                else:
                    try:
                        fecha_iso = fecha if isinstance(fecha, str) else (fecha.isoformat() if hasattr(fecha, 'isoformat') else str(fecha))
                    except Exception:
                        fecha_iso = str(fecha)

                payloads.append({
                    "voyage": voyage,
                    "referencia": it.get('referencia'),
                    "consecutivo": int(it.get('consecutivo') or 0),
                    "transaccion": int(it.get('transaccion') or 0),
                    "pit": int(it.get('pit') or 0),
                    "material": it.get('material') or "",
                    "peso": peso_str,
                    "puerto_id": it.get('puerto_id') or voyage,
                    "fecha_hora": fecha_iso,
                    "usuario_id": int(it.get('usuario_id') or 0),
                    "usuario": it.get('usuario') or "",
                })

            endpoint = f"{settings.TG_API_URL}/api/v1/Metalsoft/EnvioFinal"

            # Si la API acepta lista, enviar todo en una sola request (comportamiento actual)
            if external_accepts_list:
                serialized = AnyUtils.serialize_data(payloads)
                log.info(f"EnvioFinal - notificación externa para voyage {voyage} -> endpoint {endpoint} payload: {serialized}")
                await self.feedback_service.post(serialized, endpoint)
                return

            # Si no acepta lista: enviar un POST por cada item con concurrencia y retries
            concurrency = 5
            sem = asyncio.Semaphore(concurrency)
            max_retries = 3
            base_backoff = 0.5

            async def _post_single(p):
                # Generar idempotency key por item
                idempotency_key = f"{p.get('referencia') or ''}-{p.get('transaccion') or 0}"
                # serializar
                serialized = AnyUtils.serialize_data(p)
                headers = {"Idempotency-Key": idempotency_key}

                last_exc = None
                for attempt in range(1, max_retries + 1):
                    try:
                        async with sem:
                            # feedback_service.post firma: (data, url)
                            await self.feedback_service.post(serialized, endpoint)
                        return True
                    except httpx.HTTPStatusError as he:
                        last_exc = he
                        status_code = he.response.status_code if he.response is not None else None
                        # si 4xx -> no reintentar
                        if status_code and 400 <= status_code < 500:
                            log.error(f"EnvioFinal item non-retryable error {status_code}: {he.response.text if he.response is not None else he}")
                            raise
                        # si 5xx -> reintentar
                    except Exception as e:
                        last_exc = e
                        log.warning(f"EnvioFinal item, intento {attempt} fallo: {e}")

                    # backoff
                    await asyncio.sleep(base_backoff * (2 ** (attempt - 1)))

                # si falla todo, elevar
                log.error(f"EnvioFinal: fallaron todos los reintentos para item {p.get('referencia')} trans {p.get('transaccion')}")
                if isinstance(last_exc, Exception):
                    raise last_exc
                raise Exception("EnvioFinal: error desconocido al enviar item")

            tasks = [asyncio.create_task(_post_single(p)) for p in payloads]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            errors = [r for r in results if isinstance(r, Exception)]
            if errors:
                log.error(f"EnvioFinal: {len(errors)} items fallaron al notificar externamente")
                # decidir si lanzar o no. Por seguridad, lanzar BasedException para que caller lo maneje
                raise BasedException(message=f"Algunos items fallaron al notificar externamente ({len(errors)})", status_code=status.HTTP_424_FAILED_DEPENDENCY)

        except BasedException:
            raise
        except Exception as e:
            log.error(f"EnvioFinal: Error al enviar notificación externa para voyage {voyage}: {e}", exc_info=True)
            raise BasedException(
                message=f"EnvioFinal: Error al enviar notificación externa: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from datetime import datetime
from decimal import Decimal
from fastapi_pagination import Page, Params
from sqlalchemy import select
from starlette import status

from core.exceptions.base_exception import BasedException
from core.config.settings import get_settings
from database.models import VViajes
from typing import List, Optional
from repositories.viajes_repository import ViajesRepository
from schemas.bls_schema import BlsCreate, BlsExtCreate, BlsResponse, BlsUpdate
from services.bls_service import BlsService
from services.clientes_service import ClientesService
from services.ext_api_service import ExtApiService
from services.materiales_service import MaterialesService
from services.flotas_service import FlotasService
from schemas.viajes_schema import (
    ViajesResponse, ViajeCreate, ViajeBuqueExtCreate, ViajeUpdate, ViajesActResponse, ViajeCamionExtCreate,VViajesResponse
)
from schemas.flotas_schema import FlotasResponse, FlotaCreate
from core.exceptions.entity_exceptions import (
    EntityAlreadyRegisteredException,
    EntityNotFoundException,
)
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
                raise EntityNotFoundException(
                    f"No se pudo obtener flota con tipo '{viaje_create.tipo}' y ref '{viaje_create.referencia}'")

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
        except EntityAlreadyRegisteredException as e:
            raise e
        except EntityNotFoundException as e:
            raise e
        except Exception as e:
            log.error(f"Error creando buque nuevo con puerto_id {viaje_create.puerto_id}: {e}")
            raise BasedException(
                message="Error al crear el viaje de buque",
                status_code=status.HTTP_409_CONFLICT
            )

    async def create_camion_nuevo(self, viaje_create: ViajeCamionExtCreate, user_id : int) -> ViajesResponse:
        """
        Create a new camion viaje, including associated flota and material if valid.

        Args:
            viaje_create (ViajeCamionExtCreate): The camion viaje data to create.
            user_id (int): The ID of the user performing the creation, extracted from JWT.

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
                raise EntityAlreadyRegisteredException(f"Ya existe un viaje con puerto_id '{viaje_create.puerto_id}'")

            # 2. Crear la flota si no existe
            nueva_flota = FlotaCreate.model_validate(viaje_create)
            nueva_flota["usuario_id"] = user_id
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
                raise EntityNotFoundException("Error al recuperar el viaje recién creado")

            return ViajesResponse(**created_viaje.__dict__)
        except EntityAlreadyRegisteredException as e:
            raise e
        except EntityNotFoundException as e:
            raise e
        except Exception as e:
            log.error(f"Error creando camion nuevo con puerto_id {viaje_create.puerto_id}: {e}")
            raise BasedException(
                message="Error al crear el viaje de camion",
                status_code=status.HTTP_409_CONFLICT
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

            tran = await  self.transacciones_service.get_tran_by_viaje(viaje.id)
            if not tran:
                raise EntityNotFoundException(f"Transacción con viaje_id: '{viaje.id}' no existe")

            flota = await self.flotas_service.get_flota(viaje.flota_id)
            if not flota:
                raise EntityNotFoundException(f"Flota con id '{viaje.flota_id}' no existe")

            updated_flota = await self.flotas_service.update_status(flota,estado_puerto, estado_operador)

            if flota.tipo: 'camion'

            # Solo notificar si el cambio de estado es para finalizado
            if not estado_puerto:
                notification_data = {
                  "truckPlate": flota.referencia,
                  "truckTransaction": str(tran.id),
                  "weighingPitId": tran.pit,
                  "weight": tran.peso_real
               }

                await self.feedback_service.post(AnyUtils.serialize_data(notification_data),f"{get_settings().TG_API_URL}/api/v1/Metalsoft/SendTruckFinalizationLoading")
                log.info(f"Notificación enviada para flota {flota.referencia} con estado_puerto: {estado_puerto}")


            if flota.tipo: 'buque'

            # Solo notificar si el cambio de estado es para finalizado
            if not estado_puerto:
                notification_data = {
                   "voyage": puerto_id,
                    "status": "Finished"
               }
                await self.feedback_service.post(notification_data,f"{get_settings().TG_API_URL}/api/v1/Metalsoft/FinalizaBuque")
                log.info(f"Notificación enviada para flota {flota.referencia} con estado_puerto: {estado_puerto}")


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

    async def chg_camion_ingreso(self, puerto_id: str, fecha: datetime) -> ViajesResponse:
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

            update_fields = {
                "fecha_salida": fecha,
            }
            update_data = ViajeUpdate(**update_fields)
            updated = await self._repo.update(viaje.id, update_data)
            log.info(f"Ingreso actualizado para viaje: {viaje.puerto_id} a {fecha}")
            return updated
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
                raise EntityNotFoundException(f"El cliente '{bl_input.cliente_name}' no existe")

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




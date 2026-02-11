from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

import httpx
from sqlalchemy.exc import IntegrityError
from starlette import status

from core.config.settings import get_settings
from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import (
    EntityAlreadyRegisteredException,
    EntityNotFoundException,
)
from repositories.viajes_repository import ViajesRepository
from schemas.bls_schema import BlsCreate, BlsExtCreate, BlsResponse, BlsUpdate, VBlsResponse
from schemas.ext_api_schema import NotificationCargue, NotificationBuque, NotificationPitCargue, NotificationBlsPeso
from schemas.flotas_schema import FlotasResponse, FlotaCreate
from schemas.transacciones_schema import TransaccionResponse
from schemas.viajes_schema import (
    ViajesResponse, ViajeCreate, ViajeBuqueExtCreate, ViajeUpdate, ViajeCamionExtCreate,
    ViajesActivosPorMaterialResponse
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

# Referencia para evitar advertencias de import no usado
_TZ = timezone

class ViajesService:

    def __init__(self, viajes_repository: ViajesRepository, mat_service : MaterialesService, flotas_service : FlotasService, feedback_service : ExtApiService, transacciones_service : TransaccionesService, bl_service : BlsService, client_service : ClientesService) -> None:
        self._repo = viajes_repository
        self.mat_service = mat_service
        self.flotas_service = flotas_service
        self.bls_service = bl_service
        self.clientes_service = client_service
        self.feedback_service = feedback_service
        self.transacciones_service= transacciones_service

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

    async def get_viajes_activos_por_material(self, tipo_flota: str) -> List[ViajesActivosPorMaterialResponse]:
        """
        Retrieve active viajes grouped by material.

        For 'buque': groups by BLs materials
        For 'camion': uses the viaje's material_id

        Args:
            tipo_flota (str): Type of fleet ('buque' or 'camion')

        Returns:
            List[ViajesActivosPorMaterialResponse]: List of active viajes grouped by material

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            viajes = await self._repo.get_viajes_activos_por_material(tipo_flota)
            if not viajes:
                return []

            return [ViajesActivosPorMaterialResponse(**viaje) for viaje in viajes]
        except Exception as e:
            log.error(f"Error al obtener viajes activos por material: {e}")
            raise BasedException(
                message="Error al obtener viajes activos por material",
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

            # Salvaguarda: asegurar que las fechas estén en UTC (aceptar casos donde el validador no se ejecutó)
            for f in ("fecha_llegada", "fecha_salida", "fecha_hora"):
                if f in viaje_data and viaje_data[f] is not None:
                    from utils.time_util import normalize_to_app_tz
                    viaje_data[f] = normalize_to_app_tz(viaje_data[f])

            # Log de depuración: mostrar cómo quedaron las fechas antes de crear el registro
            try:
                log.info(f"[DEBUG create_buque_nuevo] viaje_data fecha_llegada: {viaje_data.get('fecha_llegada')} (tzinfo={getattr(viaje_data.get('fecha_llegada'), 'tzinfo', None)})")
                log.info(f"[DEBUG create_buque_nuevo] viaje_data fecha_salida:  {viaje_data.get('fecha_salida')} (tzinfo={getattr(viaje_data.get('fecha_salida'), 'tzinfo', None)})")
            except Exception:
                pass

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
            # DEBUG: inspeccionar viaje_data después de model_dump
            try:
                vll = viaje_data.get('fecha_llegada')
                vls = viaje_data.get('fecha_salida')
                log.info(f"[DEBUG create_camion_nuevo MODEL_DUMP] fecha_llegada: {vll} (type={type(vll)}, tzinfo={getattr(vll, 'tzinfo', None)})")
                log.info(f"[DEBUG create_camion_nuevo MODEL_DUMP] fecha_salida:  {vls} (type={type(vls)}, tzinfo={getattr(vls, 'tzinfo', None)})")
            except Exception:
                pass

            viaje_data["flota_id"] = flota.id
            viaje_data["material_id"] = material_id

            # Salvaguarda: asegurar que las fechas estén en UTC
            for f in ("fecha_llegada", "fecha_salida", "fecha_hora"):
                if f in viaje_data and viaje_data[f] is not None:
                    from utils.time_util import normalize_to_app_tz
                    before_val = viaje_data[f]
                    viaje_data[f] = normalize_to_app_tz(viaje_data[f])
                    try:
                        log.info(f"[DEBUG create_camion_nuevo NORMALIZE] field={f} before={before_val} (type={type(before_val)}, tzinfo={getattr(before_val, 'tzinfo', None)}) after={viaje_data[f]} (type={type(viaje_data[f])}, tzinfo={getattr(viaje_data[f], 'tzinfo', None)})")
                    except Exception:
                        pass

            # 6. Crear registro en la base de datos
            db_viaje = ViajeCreate(**viaje_data)
            try:
                await self._repo.create(db_viaje)
            except IntegrityError as ie:
                # Log completo para debugging
                log.error(f"IntegrityError creando viaje para puerto_id {viaje_create.puerto_id}: {ie}", exc_info=True)
                # Intentar obtener detalle legible si viene del driver
                detail = getattr(getattr(ie, 'orig', None), 'detail', None) or str(ie)
                # Normalizar mensaje para usuario
                if 'uk_viajes' in str(detail) or 'viajes' in str(detail):
                    user_msg = f"Ya existe un viaje para la combinación (flota_id, viaje_origen) o restricción única violada: {detail}"
                else:
                    user_msg = f"Violación de integridad al crear viaje: {detail}"
                raise BasedException(message=user_msg, status_code=status.HTTP_409_CONFLICT)

            # 7. Consultar el viaje recién añadido
            created_viaje = await self.get_viaje_by_puerto_id(viaje_create.puerto_id)
            if not created_viaje:
                raise EntityNotFoundException("Error al recuperar la cita recién creada")

            return ViajesResponse(**created_viaje.__dict__)
        except (EntityAlreadyRegisteredException, EntityNotFoundException) as e:
            raise e
        except BasedException:
            # Re-lanzar BasedException sin wrapping adicional
            raise
        except Exception as e:
            log.error(f"Error inesperado a crear camion y/o cita con puerto_id {viaje_create.puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message=str(e),
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def chg_estado_flota(self, puerto_id: Optional[str] = None, estado_puerto: Optional[bool] = None, estado_operador: Optional[bool] = None, viaje_id: Optional[int] = None, fecha_llegada: Optional[datetime] = None, fecha_salida: Optional[datetime] = None) -> FlotasResponse:
        """
        Change the status of a flota associated with a viaje.

        Args:
            puerto_id (str): The puerto_id of the viaje (optional if viaje_id is provided).
            estado_puerto (bool): The puerto status value for the flota.
            estado_operador (bool): The operador status value for the flota.
            viaje_id (int): The id of the viaje (optional if puerto_id is provided).
            fecha_llegada (datetime): Optional arrival date to update on the viaje.
            fecha_salida (datetime): Optional departure date to update on the viaje.

        Returns:
            FlotasResponse: The updated flota object.

        Raises:
            EntityNotFoundException: If viaje or flota is not found.
            BasedException: If update fails due to database or other errors.
            ValueError: If neither puerto_id nor viaje_id is provided.
        """
        try:
            if viaje_id is not None:
                viaje = await self._repo.find_one(id=viaje_id)
                if not viaje:
                    raise EntityNotFoundException(f"Viaje con id: '{viaje_id}' no existe")
            elif puerto_id is not None:
                viaje = await self.get_viaje_by_puerto_id(puerto_id)
                if not viaje:
                    raise EntityNotFoundException(f"Viaje con puerto_id: '{puerto_id}' no existe")
            else:
                raise ValueError("Debe proporcionar puerto_id o viaje_id")

            flota = await self.flotas_service.get_flota(viaje.flota_id)
            if not flota:
                raise EntityNotFoundException(f"Flota con id '{viaje.flota_id}' no existe")

            # Actualizar fechas del viaje si se proporcionan
            if fecha_llegada is not None or fecha_salida is not None:
                from utils.time_util import normalize_to_app_tz
                update_fields = {}
                if fecha_llegada is not None:
                    fecha_llegada_norm = normalize_to_app_tz(fecha_llegada)
                    log.info(f"[DEBUG chg_estado_flota] fecha_llegada original={fecha_llegada} (tzinfo={getattr(fecha_llegada, 'tzinfo', None)}), normalizada={fecha_llegada_norm} (tzinfo={getattr(fecha_llegada_norm, 'tzinfo', None)})")
                    update_fields["fecha_llegada"] = fecha_llegada_norm
                if fecha_salida is not None:
                    fecha_salida_norm = normalize_to_app_tz(fecha_salida)
                    log.info(f"[DEBUG chg_estado_flota] fecha_salida original={fecha_salida} (tzinfo={getattr(fecha_salida, 'tzinfo', None)}), normalizada={fecha_salida_norm} (tzinfo={getattr(fecha_salida_norm, 'tzinfo', None)})")
                    update_fields["fecha_salida"] = fecha_salida_norm
                update_data = ViajeUpdate(**update_fields)
                await self._repo.update(viaje.id, update_data)
                log.info(f"Fechas actualizadas para viaje {viaje.id}: {update_fields}")

            updated_flota = await self.flotas_service.update_status(flota, estado_puerto, estado_operador)

            # Solo notificar si el cambio de estado es para finalizado
            if estado_operador is False:
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
                            tran, _ = await self.transacciones_service.transaccion_finalizar(tran.id)
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
        except ValueError as e:
            raise e
        except Exception as e:
            identifier = f"viaje_id {viaje_id}" if viaje_id else f"puerto_id {puerto_id}"
            log.error(f"Error al cambiar estado de flota con {identifier}: {str(e)}")
            raise BasedException(
                message=f"Error al cambiar el estado de flota con {identifier} : {str(e)}",
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

            # Pit por defecto establecido en 1
            pit = 1

            # Asegurar que la fecha se normalice a la zona de la aplicación antes de guardar.
            # Esto evita diferencias en producción si el payload viene con tzinfo distinto o si
            # el cliente envía un datetime naive que deba interpretarse según APP_TIMEZONE.
            from utils.time_util import normalize_to_app_tz
            fecha_norm = normalize_to_app_tz(fecha)
            log.info(f"[DEBUG chg_camion_ingreso] fecha original={fecha} (tzinfo={getattr(fecha, 'tzinfo', None)}), fecha_norm={fecha_norm} (tzinfo={getattr(fecha_norm, 'tzinfo', None)})")

            update_fields = {
                "fecha_llegada": fecha_norm,
            }
            update_data = ViajeUpdate(**update_fields)
            await self._repo.update(viaje.id, update_data)

            notification = NotificationPitCargue(
                cargoPit=pit,
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

            from utils.time_util import normalize_to_app_tz
            # Normalizar y loguear para debugging en producción
            fecha_norm = normalize_to_app_tz(fecha)
            log.info(f"[DEBUG chg_camion_salida] fecha original={fecha} (tzinfo={getattr(fecha, 'tzinfo', None)}), fecha_norm={fecha_norm} (tzinfo={getattr(fecha_norm, 'tzinfo', None)}) peso={peso}")
            update_fields = {
                # Guardar la hora tal como llegó el cliente, asumiendo APP_TIMEZONE
                "fecha_salida": fecha_norm,
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

    async def send_envio_final_external(self, voyage: str, envio_list: list, external_accepts_list: Optional[bool] = None, send_last_as_object: Optional[bool] = True) -> None:
        """
        Envía la lista de 'envio final' a la API externa en el endpoint /api/v1/Metalsoft/EnvioFinal.

        - voyage: puerto_id del viaje
        - envio_list: lista de objetos que siguen la forma de VPesadasAcumResponse (o dicts compatibles)
        - external_accepts_list: si None, se consulta get_settings().TG_API_ACCEPTS_LIST; si False, se enviará un POST por cada elemento.
        - send_last_as_object: cuando True, se enviará únicamente el último registro (por fecha_hora) como un único objeto (no lista). Por defecto True (nuevo comportamiento).
        """
        try:
            from core.config.settings import get_settings
            from utils.any_utils import AnyUtils
            from decimal import Decimal
            from datetime import datetime, timezone
            from utils.time_util import now_local
            import asyncio
            import httpx
            import uuid
            import time

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
                    # Use the container local timezone (configured via TZ) for timestamps
                    fecha_iso = now_local().isoformat()
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

            # Si se solicita enviar solo la última pesada como objeto, elegir el registro con fecha_hora más reciente
            if send_last_as_object:
                if not payloads:
                    raise BasedException(message="No hay registros para enviar", status_code=status.HTTP_400_BAD_REQUEST)
                # intentar determinar la última por fecha_hora
                def _parse_date(v):
                     try:
                        if isinstance(v, str):
                            # Try parsing aware ISO strings first; if missing tz info, assume local
                            try:
                                return datetime.fromisoformat(v)
                            except Exception:
                                # Fallback: treat strings ending with Z as UTC
                                return datetime.fromisoformat(v.replace('Z', '+00:00'))
                        return v
                     except Exception:
                         return datetime.min.replace(tzinfo=timezone.utc)

                last_item = max(payloads, key=lambda x: _parse_date(x.get('fecha_hora')))
                # preparar headers: Idempotency-Key y X-Correlation-Id
                idempotency_key = f"{last_item.get('referencia') or ''}-{last_item.get('transaccion') or 0}"
                correlation_id = str(uuid.uuid4())
                headers = {"Idempotency-Key": idempotency_key, "X-Correlation-Id": correlation_id}

                serialized = AnyUtils.serialize_data(last_item)
                log.info(f"EnvioFinal - enviando última pesada como objeto para voyage {voyage} -> endpoint {endpoint} payload: {serialized} headers: {headers}")
                await self.feedback_service.post(serialized, endpoint, extra_headers=headers)
                return

            # Si la API acepta lista, enviar todo en una sola request (comportamiento actual)
            if external_accepts_list:
                # headers para lista
                correlation_id = str(uuid.uuid4())
                idempotency_key = f"{voyage}-{int(time.time())}"
                headers = {"Idempotency-Key": idempotency_key, "X-Correlation-Id": correlation_id}
                serialized = AnyUtils.serialize_data(payloads)
                log.info(f"EnvioFinal - notificación externa para voyage {voyage} -> endpoint {endpoint} payload: {serialized} headers: {headers}")
                await self.feedback_service.post(serialized, endpoint, extra_headers=headers)
                return

            # Si no acepta lista: enviar un POST por cada item con concurrencia y retries
            concurrency = 5
            sem = asyncio.Semaphore(concurrency)
            max_retries = 3
            base_backoff = 0.5

            async def _post_single(p):
                # Generar idempotency key por item
                idempotency_key = f"{p.get('referencia') or ''}-{p.get('transaccion') or 0}"
                correlation_id = str(uuid.uuid4())
                # serializar
                serialized = AnyUtils.serialize_data(p)
                headers = {"Idempotency-Key": idempotency_key, "X-Correlation-Id": correlation_id}

                last_exc = None
                for attempt in range(1, max_retries + 1):
                    try:
                        async with sem:
                            # feedback_service.post firma: (data, url, extra_headers)
                            await self.feedback_service.post(serialized, endpoint, extra_headers=headers)
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

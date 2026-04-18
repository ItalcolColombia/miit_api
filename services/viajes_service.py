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
from repositories.consumos_entrada_parcial_repository import ConsumosEntradaParcialRepository
from repositories.viajes_repository import ViajesRepository
from schemas.bls_schema import BlsCreate, BlsExtCreate, BlsResponse, BlsUpdate, VBlsResponse
from schemas.clientes_schema import ClienteCreate
from schemas.consumos_entrada_parcial_schema import ConsumosEntradaParcialCreate
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

    def __init__(self, viajes_repository: ViajesRepository, mat_service : MaterialesService, flotas_service : FlotasService, feedback_service : ExtApiService, transacciones_service : TransaccionesService, bl_service : BlsService, client_service : ClientesService, consumos_ep_repository: ConsumosEntradaParcialRepository = None) -> None:
        self._repo = viajes_repository
        self.mat_service = mat_service
        self.flotas_service = flotas_service
        self.bls_service = bl_service
        self.clientes_service = client_service
        self.feedback_service = feedback_service
        self.transacciones_service= transacciones_service
        self.consumos_ep_repository = consumos_ep_repository

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

    async def get_viaje_by_id(self, viaje_id: int) -> Optional[ViajesResponse]:
        try:
            return await self._repo.get_by_id(viaje_id)
        except Exception as e:
            log.error(f"Error obteniendo viaje con ID {viaje_id}: {e}")
            raise BasedException(
                message=f"Error al obtener el viaje con ID {viaje_id}",
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
            viaje_data["estado"] = "Programada"

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
                # Crea el cliente si no existe, con solo el nombre (razon_social)
                nuevo_cliente = ClienteCreate(razon_social=bl_input.cliente_name)
                cliente_find = await self.clientes_service.create(nuevo_cliente)
                log.info(f"Cliente '{bl_input.cliente_name}' creado automáticamente con ID: {cliente_find.id}")

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

            # 5. Buscar bl_id si se envió no_bl
            bl_id = None
            if viaje_create.no_bl:
                # Primero necesitamos el viaje de recibo (buque) para buscar el BL
                if viaje_create.viaje_origen:
                    viaje_recibo = await self.get_viaje_by_puerto_id(viaje_create.viaje_origen)
                    if viaje_recibo:
                        bl = await self.bls_service.get_bl_by_no_bl_and_viaje(viaje_create.no_bl, viaje_recibo.id)
                        if bl:
                            bl_id = bl.id
                            log.info(f"BL encontrado para despacho: bl_id={bl_id}, no_bl={viaje_create.no_bl}")
                        else:
                            log.warning(f"No se encontró BL con no_bl '{viaje_create.no_bl}' para viaje_origen '{viaje_create.viaje_origen}'")
                    else:
                        log.warning(f"No se encontró viaje de recibo con puerto_id '{viaje_create.viaje_origen}'")
                else:
                    # Si no hay viaje_origen pero sí no_bl, buscar el BL directamente por no_bl
                    bl = await self.bls_service.get_bl_by_num(viaje_create.no_bl)
                    if bl:
                        bl_id = bl.id
                        log.info(f"BL encontrado para despacho (sin viaje_origen): bl_id={bl_id}, no_bl={viaje_create.no_bl}")
                    else:
                        log.warning(f"No se encontró BL con no_bl '{viaje_create.no_bl}'")

            # 6. Determinar si es despacho directo
            # Regla: Si hay un viaje_origen que apunta a un buque activo (estado_puerto=True y estado_operador=True)
            es_despacho_directo = False
            if viaje_create.viaje_origen:
                viaje_buque = await self.get_viaje_by_puerto_id(viaje_create.viaje_origen)
                if viaje_buque:
                    flota_buque = await self.flotas_service.get_flota(viaje_buque.flota_id)
                    if flota_buque:
                        es_buque = getattr(flota_buque, 'tipo', '') == 'buque'
                        estado_puerto = getattr(flota_buque, 'estado_puerto', False)
                        estado_operador = getattr(flota_buque, 'estado_operador', False)
                        if es_buque and estado_puerto and estado_operador:
                            es_despacho_directo = True
                            log.info(f"Viaje camión {viaje_create.puerto_id}: marcado como despacho directo (buque activo viaje_origen={viaje_create.viaje_origen})")

            # 7. Ajustar el schema al requerido
            viaje_data = viaje_create.model_dump(exclude={"referencia", "puntos", "no_bl"})
            viaje_data["despacho_directo"] = es_despacho_directo
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
            viaje_data["bl_id"] = bl_id
            viaje_data["estado"] = "Programada"

            # La normalización de las fechas se delega al repositorio base (_normalize_datetimes).
            # El schema ViajeCamionExtCreate ya normaliza vía @field_validator.
            # NO normalizar aquí para evitar conversiones múltiples.

            # 8. Crear registro en la base de datos
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

            # 9. Consultar el viaje recién añadido
            created_viaje = await self.get_viaje_by_puerto_id(viaje_create.puerto_id)
            if not created_viaje:
                raise EntityNotFoundException("Error al recuperar la cita recién creada")

            # 10. Auto-cancelar citas Programadas previas de la misma flota dentro de la ventana
            # de 24h (mitigacion del ruido de citas zombi: la plataforma externa no notifica
            # cuando una cita se anula, asi que asumimos que la cita mas reciente reemplaza a
            # las anteriores no consumidas).
            await self._cancelar_citas_reemplazadas(flota.id, created_viaje.id)

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

    async def chg_estado_flota(self, puerto_id: Optional[str] = None, estado_puerto: Optional[bool] = None, estado_operador: Optional[bool] = None, viaje_id: Optional[int] = None, fecha_llegada: Optional[datetime] = None, fecha_salida: Optional[datetime] = None, reset_fecha_salida: bool = False) -> FlotasResponse:
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

            # Construir update_fields combinando fechas y transicion de estado del viaje.
            # Transiciones aplicadas:
            #   * estado_puerto=True  -> viaje pasa a 'Activa'  (gate in / arribo del buque)
            #   * estado_operador=False -> viaje pasa a 'Finalizada' (cierre del operador)
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
            elif reset_fecha_salida:
                update_fields["fecha_salida"] = None
                log.info(f"[DEBUG chg_estado_flota] fecha_salida reseteada a None")

            if estado_operador is False:
                update_fields["estado"] = "Finalizada"
            elif estado_puerto is True:
                update_fields["estado"] = "Activa"

            if update_fields:
                update_data = ViajeUpdate(**update_fields)
                await self._repo.update(viaje.id, update_data)
                log.info(f"Viaje {viaje.id} actualizado: {update_fields}")

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

    async def chg_camion_ingreso(self, puerto_id: str, fecha: datetime, peso_vacio: Decimal, peso_maximo: Decimal) -> NotificationPitCargue:
        """
        Update the arrival date of a camion viaje.

        Args:
            puerto_id (str): The puerto_id of the viaje.
            fecha (datetime): The arrival date to set.
            peso_vacio (Decimal): Empty truck weight.
            peso_maximo (Decimal): Maximum truck weight.

        Returns:
            ViajesResponse: The updated viaje object.

        Raises:
            EntityNotFoundException: If viaje or flota is not found or flota type is not 'camion'.
            BasedException: If update fails due to database or other errors.
        """
        try:
            if peso_vacio < 0 or peso_maximo < 0:
                raise BasedException(
                    message="peso_vacio y peso_maximo deben ser mayores o iguales a 0",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            if peso_maximo < peso_vacio:
                raise BasedException(
                    message="peso_maximo debe ser mayor o igual a peso_vacio",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            peso_tara = peso_maximo - peso_vacio

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

            # La fecha ya viene como timestamp del servidor (now_local) desde el
            # endpoint, así que no necesita normalización adicional.
            log.info(f"[DEBUG chg_camion_ingreso] fecha={fecha} (tzinfo={getattr(fecha, 'tzinfo', None)})")

            # Determinar si es despacho directo
            # Regla: Si hay un viaje_origen que apunta a un buque activo (estado_puerto=True y estado_operador=True)
            es_despacho_directo = False
            if viaje.viaje_origen:
                viaje_buque = await self.get_viaje_by_puerto_id(viaje.viaje_origen)
                if viaje_buque:
                    flota_buque = await self.flotas_service.get_flota(viaje_buque.flota_id)
                    if flota_buque:
                        es_buque = getattr(flota_buque, 'tipo', '') == 'buque'
                        estado_puerto = getattr(flota_buque, 'estado_puerto', False)
                        estado_operador = getattr(flota_buque, 'estado_operador', False)
                        if es_buque and estado_puerto and estado_operador:
                            es_despacho_directo = True
                            log.info(f"Viaje camión {puerto_id}: marcado como despacho directo en ingreso (buque activo viaje_origen={viaje.viaje_origen})")

            update_fields = {
                "fecha_llegada": fecha,
                "fecha_salida": None,
                "despacho_directo": es_despacho_directo,
                "peso_tara": peso_tara,
                "estado": "Activa",
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
        except BasedException as e:
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

            # La fecha ya viene como timestamp del servidor (now_local) desde el
            # endpoint, así que no necesita normalización adicional.
            log.info(f"[DEBUG chg_camion_salida] fecha={fecha} (tzinfo={getattr(fecha, 'tzinfo', None)}) peso={peso}")
            update_fields = {
                "fecha_salida": fecha,
                "peso_real": peso,
                "estado": "Finalizada",
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

    async def _cancelar_citas_reemplazadas(self, flota_id: int, nueva_cita_id: int, ventana_horas: int = 24) -> int:
        """
        Cancela las citas en estado 'Programada' de la misma flota creadas dentro de la
        ventana rolling indicada, excluyendo la cita recien creada. Se usa al recibir
        una nueva cita para asumir que reemplaza las anteriores no consumidas (la
        plataforma externa no notifica anulaciones).

        Returns:
            int: cantidad de citas canceladas.
        """
        try:
            previas = await self._repo.find_programadas_by_flota_in_window(
                flota_id=flota_id,
                hours=ventana_horas,
                exclude_viaje_id=nueva_cita_id,
            )
            if not previas:
                return 0

            motivo = f"reemplazada_por_cita_{nueva_cita_id}"
            update_payload = ViajeUpdate(estado="Cancelada", motivo_cancelacion=motivo)
            for cita in previas:
                try:
                    await self._repo.update(cita.id, update_payload)
                    log.info(
                        f"Cita {cita.id} (puerto_id={cita.puerto_id}) cancelada automaticamente: "
                        f"reemplazada por nueva cita {nueva_cita_id} de la misma flota {flota_id}."
                    )
                except Exception as e_upd:
                    log.error(f"No se pudo cancelar cita previa {cita.id} de flota {flota_id}: {e_upd}")
            return len(previas)
        except Exception as e:
            log.error(f"Error al ejecutar auto-cancelacion de citas previas para flota {flota_id}: {e}", exc_info=True)
            return 0

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
                weight=tran.peso_real,
                despacho_directo=viaje.despacho_directo
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

    async def _calcular_y_actualizar_pesos_reales_bls(self, viaje_id: int) -> List[dict]:
        """
        Calcula y actualiza los pesos reales de los BLs de un viaje mediante prorrateo.

        La lógica es:
        1. Obtener todas las transacciones finalizadas del viaje, agrupadas por material
        2. Para cada material, sumar el peso_real de las transacciones
        3. Obtener todos los BLs del viaje para ese material
        4. Calcular el peso_real de cada BL proporcionalmente:
           peso_real_bl = (peso_bl / suma_peso_bl_material) * peso_real_transacciones
        5. Actualizar cada BL con su peso_real calculado

        Args:
            viaje_id: ID del viaje (buque)

        Returns:
            List[dict]: Lista de BLs actualizados con sus pesos reales
        """
        from decimal import Decimal, ROUND_HALF_UP
        from collections import defaultdict
        from sqlalchemy import select, func
        from database.models import Transacciones, Bls
        from schemas.bls_schema import BlsUpdate

        bls_actualizados = []

        try:
            # 1. Obtener suma de peso_real por material de las transacciones finalizadas del viaje
            query_transacciones = (
                select(
                    Transacciones.material_id,
                    func.sum(Transacciones.peso_real).label('peso_real_total')
                )
                .where(Transacciones.viaje_id == viaje_id)
                .where(Transacciones.tipo == 'Recibo')
                .where(Transacciones.estado == 'Finalizada')
                .group_by(Transacciones.material_id)
            )
            result_trans = await self._repo.db.execute(query_transacciones)
            pesos_por_material = {row.material_id: Decimal(str(row.peso_real_total or 0)) for row in result_trans.fetchall()}

            log.info(f"Pesos reales por material para viaje {viaje_id}: {pesos_por_material}")

            if not pesos_por_material:
                log.warning(f"No se encontraron transacciones finalizadas para viaje {viaje_id}")
                return bls_actualizados

            # 2. Obtener todos los BLs del viaje
            query_bls = (
                select(Bls)
                .where(Bls.viaje_id == viaje_id)
            )
            result_bls = await self._repo.db.execute(query_bls)
            bls = result_bls.scalars().all()

            if not bls:
                log.warning(f"No se encontraron BLs para viaje {viaje_id}")
                return bls_actualizados

            # 3. Agrupar BLs por material y calcular suma de peso_bl por material
            bls_por_material = defaultdict(list)
            suma_peso_bl_por_material = defaultdict(Decimal)

            for bl in bls:
                material_id = bl.material_id
                peso_bl = Decimal(str(bl.peso_bl or 0))
                bls_por_material[material_id].append(bl)
                suma_peso_bl_por_material[material_id] += peso_bl

            log.info(f"Suma de peso_bl por material para viaje {viaje_id}: {dict(suma_peso_bl_por_material)}")

            # 4. Calcular y actualizar peso_real para cada BL
            for material_id, bls_del_material in bls_por_material.items():
                peso_real_total = pesos_por_material.get(material_id, Decimal('0'))
                suma_peso_bl = suma_peso_bl_por_material[material_id]

                if suma_peso_bl == 0:
                    log.warning(f"Suma de peso_bl es 0 para material {material_id} en viaje {viaje_id}")
                    continue

                for bl in bls_del_material:
                    peso_bl = Decimal(str(bl.peso_bl or 0))

                    # Calcular proporción: peso_real_bl = (peso_bl / suma_peso_bl) * peso_real_total
                    if suma_peso_bl > 0:
                        proporcion = peso_bl / suma_peso_bl
                        peso_real_calculado = (proporcion * peso_real_total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    else:
                        peso_real_calculado = Decimal('0')

                    log.info(f"BL {bl.no_bl}: peso_bl={peso_bl}, proporción={proporcion:.4f}, peso_real_calculado={peso_real_calculado}")

                    # Actualizar el BL con el peso_real calculado
                    try:
                        update_data = BlsUpdate(peso_real=peso_real_calculado)
                        await self.bls_service.update(bl.id, update_data)

                        bls_actualizados.append({
                            'bl_id': bl.id,
                            'no_bl': bl.no_bl,
                            'material_id': material_id,
                            'peso_bl': float(peso_bl),
                            'peso_real': float(peso_real_calculado)
                        })
                    except Exception as e_update:
                        log.error(f"Error al actualizar peso_real del BL {bl.id}: {e_update}")

            log.info(f"Actualización de pesos reales completada para viaje {viaje_id}. BLs actualizados: {len(bls_actualizados)}")
            return bls_actualizados

        except Exception as e:
            log.error(f"Error al calcular pesos reales de BLs para viaje {viaje_id}: {e}", exc_info=True)
            return bls_actualizados

    async def finalizar_buque(
        self,
        puerto_id: str,
        estado_puerto: Optional[bool] = None,
        estado_operador: Optional[bool] = False,
        fecha_salida: Optional[datetime] = None
    ) -> tuple:
        """
        Finaliza un buque actualizando los estados de la flota y enviando
        la notificación FinalizaBuque a la API externa con retry.

        Args:
            puerto_id (str): El puerto_id del viaje del buque.
            estado_puerto (Optional[bool]): El estado_puerto a actualizar. Default None (sin cambio).
            estado_operador (Optional[bool]): El estado_operador a actualizar. Default False.
            fecha_salida (Optional[datetime]): Fecha de salida a actualizar en el viaje. Default None.

        Returns:
            tuple: (FlotasResponse, dict) - La flota actualizada y el resultado de la notificación.
                   El dict contiene: 'success' (bool), 'message' (str), 'flota_actualizada' (bool)
        """
        resultado = {
            'success': False,
            'message': '',
            'flota_actualizada': False
        }

        try:
            # Obtener el viaje por puerto_id
            viaje = await self.get_viaje_by_puerto_id(puerto_id)
            if not viaje:
                raise EntityNotFoundException(f"Viaje con puerto_id: '{puerto_id}' no existe")

            # Obtener la flota
            flota = await self.flotas_service.get_flota(viaje.flota_id)
            if not flota:
                raise EntityNotFoundException(f"Flota con id '{viaje.flota_id}' no existe")

            # Verificar que sea un buque
            if flota.tipo != "buque":
                log.warning(f"Flota {flota.id} no es de tipo buque, es {flota.tipo}.")
                raise BasedException(
                    message=f"La flota no es de tipo buque, es {flota.tipo}",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # Calcular y actualizar los pesos reales de los BLs mediante prorrateo
            # ANTES de obtener los BLs para la notificación
            log.info(f"FinalizaBuque - Calculando pesos reales de BLs para viaje {viaje.id} (puerto_id: {puerto_id})")
            bls_actualizados = await self._calcular_y_actualizar_pesos_reales_bls(viaje.id)
            log.info(f"FinalizaBuque - BLs actualizados con peso real: {len(bls_actualizados)}")

            # Obtener BLs del viaje DESPUÉS de actualizar los pesos reales
            # (para evitar problemas de lazy loading fuera de sesión)
            bl = await self.bls_service.get_bl_by_viaje(viaje.id)

            # Preparar datos de BLs para la notificación.
            # Se calcula el delta (peso_real - peso_enviado_api) para cada BL:
            # - Despacho directo: peso_enviado_api > 0 (parciales ya enviados vía entrada-parcial-buque),
            #   por lo que se envía solo el restante.
            # - No despacho directo: peso_enviado_api = 0, por lo que el delta equivale al total.
            if bl:
                dt_bl = []
                for bl_item in bl:
                    peso_real = Decimal(str(bl_item.peso_real or 0)) if hasattr(bl_item, 'peso_real') and bl_item.peso_real else Decimal(str(bl_item.peso_bl or 0))
                    peso_enviado = Decimal(str(bl_item.peso_enviado_api or 0)) if hasattr(bl_item, 'peso_enviado_api') and bl_item.peso_enviado_api else Decimal('0')
                    delta = peso_real - peso_enviado

                    log.info(f"FinalizaBuque - BL {bl_item.no_bl}: peso_real={peso_real}, peso_enviado_api={peso_enviado}, delta={delta}")

                    dt_bl.append(
                        NotificationBlsPeso(
                            noBL=bl_item.no_bl,
                            voyage=viaje.puerto_id,
                            weightBl=float(delta)
                        ).model_dump()
                    )
            else:
                dt_bl = None

            # Actualizar fecha_salida y estado del viaje (estado pasa a Finalizada).
            # Aun cuando no llegue fecha_salida explicita marcamos la cita como Finalizada
            # para alinearla con la finalizacion del buque.
            from utils.time_util import normalize_to_app_tz
            update_viaje_fields = {"estado": "Finalizada"}
            if fecha_salida is not None:
                fecha_salida_norm = normalize_to_app_tz(fecha_salida)
                log.info(f"FinalizaBuque - fecha_salida original={fecha_salida} (tzinfo={getattr(fecha_salida, 'tzinfo', None)}), normalizada={fecha_salida_norm} (tzinfo={getattr(fecha_salida_norm, 'tzinfo', None)})")
                update_viaje_fields["fecha_salida"] = fecha_salida_norm
            update_viaje_data = ViajeUpdate(**update_viaje_fields)
            await self._repo.update(viaje.id, update_viaje_data)
            log.info(f"FinalizaBuque - Viaje {viaje.id} actualizado: {update_viaje_fields}")

            # Actualizar estados de la flota
            try:
                updated_flota = await self.flotas_service.update_status(flota, estado_puerto=estado_puerto, estado_operador=estado_operador)
                resultado['flota_actualizada'] = True
                estados_actualizados = []
                if estado_puerto is not None:
                    estados_actualizados.append(f"estado_puerto={estado_puerto}")
                if estado_operador is not None:
                    estados_actualizados.append(f"estado_operador={estado_operador}")
                log.info(f"Estados de flota {flota.id} (buque {flota.referencia}) actualizados: {', '.join(estados_actualizados)} para puerto_id {puerto_id}")
            except Exception as e_flota:
                log.error(f"Error al actualizar estado de flota {flota.id}: {e_flota}")
                raise BasedException(
                    message=f"Error al actualizar estado de flota: {e_flota}",
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Preparar notificación

            notification = NotificationBuque(
                voyage=viaje.puerto_id,
                status="Finished",
                data=dt_bl
            ).model_dump()

            settings = get_settings()
            endpoint = f"{settings.TG_API_URL}/api/v1/Metalsoft/FinalizaBuque"

            # Loguear el payload que se enviará
            try:
                serialized = AnyUtils.serialize_data(notification)
                log.info(f"FinalizaBuque - Payload a enviar para puerto_id {puerto_id}: {serialized}")
                log.info(f"FinalizaBuque - Endpoint destino: {endpoint}")

                # Enviar notificación con retry (el método post ya tiene retry implementado)
                await self.feedback_service.post(serialized, endpoint)
                log.info(f"FinalizaBuque - Notificación enviada exitosamente para puerto_id {puerto_id}")
                resultado['success'] = True
                resultado['message'] = "Notificación FinalizaBuque enviada exitosamente"

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

                log.error(f"FinalizaBuque - Notificación falló. API externa error: {e.response.status_code}: {e.response.text}")
                log.error(f"FinalizaBuque - Payload que falló: {serialized}")
                resultado['message'] = f"Notificación FinalizaBuque falló. API externa error: {msg}"

            except Exception as e_notify:
                log.error(f"FinalizaBuque - Error inesperado al enviar notificación para puerto_id {puerto_id}: {e_notify}", exc_info=True)
                log.error(f"FinalizaBuque - Payload que falló: {notification}")
                resultado['message'] = f"Error inesperado al enviar notificación FinalizaBuque: {e_notify}"

            return updated_flota, resultado

        except EntityNotFoundException as e:
            raise e
        except BasedException as e:
            raise e
        except Exception as e:
            log.error(f"FinalizaBuque - Error al finalizar buque para puerto_id {puerto_id}: {e}", exc_info=True)
            raise BasedException(
                message=f"Error al finalizar buque: {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def obtener_entrada_parcial_buque(self, puerto_id: str) -> dict:
        """
        Calcula los pesos parciales (delta) de los BLs de un buque con arribo activo.

        Obtiene la suma de peso_real de las pesadas por material de las transacciones
        de Recibo del buque, prorratea por BL, calcula el delta respecto a lo ya
        enviado (peso_enviado_api) y actualiza peso_enviado_api tras el cálculo.

        Args:
            puerto_id (str): El puerto_id del viaje del buque.

        Returns:
            dict: Estructura compatible con NotificationBuque con voyage, status="InProgress"
                  y data con los deltas por BL.
        """
        from collections import defaultdict
        from decimal import Decimal, ROUND_HALF_UP
        from sqlalchemy import select, func
        from database.models import Transacciones, Bls, Pesadas

        # 1. Obtener viaje del buque
        viaje = await self.get_viaje_by_puerto_id(puerto_id)
        if not viaje:
            raise EntityNotFoundException(f"Viaje con puerto_id: '{puerto_id}' no existe")

        # 2. Verificar que sea un buque activo
        flota = await self.flotas_service.get_flota(viaje.flota_id)
        if not flota:
            raise EntityNotFoundException(f"Flota con id '{viaje.flota_id}' no existe")

        if flota.tipo != "buque":
            raise BasedException(
                message=f"La flota no es de tipo buque, es {flota.tipo}",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        if not flota.estado_puerto or not flota.estado_operador:
            raise BasedException(
                message=f"El buque {puerto_id} no tiene un arribo activo (estado_puerto={flota.estado_puerto}, estado_operador={flota.estado_operador})",
                status_code=status.HTTP_400_BAD_REQUEST
            )

        viaje_id = viaje.id

        # 3. Obtener suma de peso_real de las PESADAS por material de transacciones de RECIBO del buque
        query_pesadas = (
            select(
                Transacciones.material_id,
                func.sum(Pesadas.peso_real).label('peso_real_total')
            )
            .join(Pesadas, Pesadas.transaccion_id == Transacciones.id)
            .where(Transacciones.viaje_id == viaje_id)
            .where(Transacciones.tipo == 'Recibo')
            .group_by(Transacciones.material_id)
        )
        result_trans = await self._repo.db.execute(query_pesadas)
        pesos_por_material = {row.material_id: Decimal(str(row.peso_real_total or 0)) for row in result_trans.fetchall()}

        log.info(f"EntradaParcialBuque - Pesos reales (pesadas acumuladas) por material para buque {viaje_id}: {pesos_por_material}")

        # 4. Obtener TODOS los BLs del buque
        query_bls = select(Bls).where(Bls.viaje_id == viaje_id)
        result_bls = await self._repo.db.execute(query_bls)
        bls = result_bls.scalars().all()

        if not bls:
            log.warning(f"EntradaParcialBuque - No se encontraron BLs para buque {viaje_id}")
            return NotificationBuque(
                voyage=puerto_id,
                status="InProgress",
                data=[]
            ).model_dump()

        # 5. Agrupar BLs por material y calcular suma de peso_bl por material
        bls_por_material = defaultdict(list)
        suma_peso_bl_por_material = defaultdict(Decimal)

        for bl in bls:
            material_id = bl.material_id
            peso_bl = Decimal(str(bl.peso_bl or 0))
            bls_por_material[material_id].append(bl)
            suma_peso_bl_por_material[material_id] += peso_bl

        # 6. Calcular peso prorrateado actual y delta para cada BL
        dt_bl = []
        bls_a_actualizar = []

        for material_id, bls_del_material in bls_por_material.items():
            peso_real_total = pesos_por_material.get(material_id, Decimal('0'))
            suma_peso_bl = suma_peso_bl_por_material[material_id]

            if suma_peso_bl == 0:
                log.warning(f"EntradaParcialBuque - Suma de peso_bl es 0 para material {material_id}")
                continue

            for bl in bls_del_material:
                peso_bl = Decimal(str(bl.peso_bl or 0))
                peso_enviado_anterior = Decimal(str(bl.peso_enviado_api or 0))

                proporcion = peso_bl / suma_peso_bl
                peso_prorrateado_actual = (proporcion * peso_real_total).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                delta_peso = (peso_prorrateado_actual - peso_enviado_anterior).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

                log.info(f"EntradaParcialBuque - BL {bl.no_bl}: peso_bl={peso_bl}, proporción={proporcion:.4f}, "
                         f"peso_prorrateado_actual={peso_prorrateado_actual}, peso_enviado_anterior={peso_enviado_anterior}, "
                         f"delta_peso={delta_peso}")

                dt_bl.append(
                    NotificationBlsPeso(
                        noBL=bl.no_bl,
                        voyage=puerto_id,
                        weightBl=float(delta_peso)
                    ).model_dump()
                )

                bls_a_actualizar.append({
                    'bl_id': bl.id,
                    'no_bl': bl.no_bl,
                    'material_id': bl.material_id,
                    'peso_bl': peso_bl,
                    'peso_enviado_api': peso_prorrateado_actual,
                    'peso_enviado_anterior': peso_enviado_anterior,
                    'delta_peso': delta_peso,
                })

        # 7. Actualizar peso_enviado_api de cada BL
        for bl_update_info in bls_a_actualizar:
            try:
                update_data = BlsUpdate(peso_enviado_api=bl_update_info['peso_enviado_api'])
                await self.bls_service.update(bl_update_info['bl_id'], update_data)
                log.debug(f"EntradaParcialBuque - Actualizado peso_enviado_api del BL {bl_update_info['bl_id']} a {bl_update_info['peso_enviado_api']}")
            except Exception as e_bl_update:
                log.error(f"EntradaParcialBuque - Error al actualizar peso_enviado_api del BL {bl_update_info['bl_id']}: {e_bl_update}")

        # 8. Guardar trazabilidad de consumos
        if self.consumos_ep_repository and bls_a_actualizar:
            try:
                consecutivo_actual = await self.consumos_ep_repository.get_max_consecutivo_by_puerto_id(puerto_id) + 1

                consumos_a_crear = []
                for bl_update_info in bls_a_actualizar:
                    consumos_a_crear.append(
                        ConsumosEntradaParcialCreate(
                            puerto_id=puerto_id,
                            bl_id=bl_update_info['bl_id'],
                            no_bl=bl_update_info['no_bl'],
                            material_id=bl_update_info['material_id'],
                            consecutivo=consecutivo_actual,
                            peso_bl=bl_update_info['peso_bl'],
                            peso_prorrateado_acumulado=bl_update_info['peso_enviado_api'],
                            peso_enviado_anterior=bl_update_info['peso_enviado_anterior'],
                            delta_peso=bl_update_info['delta_peso'],
                        )
                    )

                if consumos_a_crear:
                    await self.consumos_ep_repository.create_bulk(consumos_a_crear)
                    log.info(f"EntradaParcialBuque - Guardados {len(consumos_a_crear)} registros de trazabilidad, consecutivo={consecutivo_actual}")
            except Exception as e_consumo:
                log.error(f"EntradaParcialBuque - Error al guardar trazabilidad de consumos: {e_consumo}")

        resultado = NotificationBuque(
            voyage=puerto_id,
            status="InProgress",
            data=dt_bl if dt_bl else None
        ).model_dump()

        log.info(f"EntradaParcialBuque - Resultado para buque {puerto_id}: {resultado}")
        return resultado

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

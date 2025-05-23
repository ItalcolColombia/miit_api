from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from core.exceptions.base_exception import BaseException
from repositories.viajes_repository import ViajesRepository
from schemas.bls_schema import BlsCreate, BlsExtCreate, BlsResponse
from services.bls_service import BlsService
from services.clientes_service import ClientesService
from services.materiales_service import MaterialesService
from services.flotas_service import FlotasService
from schemas.viajes_schema import (
    ViajesResponse, ViajeCreate, ViajeBuqueExtCreate, ViajeUpdate, ViajesActResponse, ViajeCamionExtCreate
)
from schemas.flotas_schema import FlotasResponse, FlotaCreate
from schemas.clientes_schema import ClientesResponse, ClienteCreate, ClienteUpdate
from core.exceptions.entity_exceptions import EntityAlreadyRegisteredException


from utils.logger_util import LoggerUtil
log = LoggerUtil()

class ViajesService:

    def __init__(self, viajes_repository: ViajesRepository, mat_service : MaterialesService, flotas_service : FlotasService, bl_service : BlsService, client_service : ClientesService) -> None:
        self._repo = viajes_repository
        self.mat_service = mat_service
        self.flotas_service = flotas_service
        self.bls_service = bl_service
        self.clientes_service = client_service

    async def create(self, flota: ViajeCreate) -> ViajesResponse:
        return await self._repo.create(flota)

    async def update(self, id: int, flota: ViajeUpdate) -> Optional[ViajesResponse]:
        return await self._repo.update(id, flota)

    async def delete(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get(self, id: int) -> Optional[ViajesResponse]:
        return await self._repo.get_by_id(id)

    async def get_all(self) -> List[ViajesResponse]:
        return await self._repo.get_all()

    async def get_viaje_by_puerto_id(self, puerto_id: str) -> Optional[ViajesResponse]:
        """
         Find a Viaje by their 'puerto_id'

         Args:
             puerto_id: The Viaje reference param to filter.

         Returns:
             Flota object filtered by 'puerto_id'.
         """
        return await self._repo.check_puerto_id(puerto_id)

    # async def get_paginated_flotas(self, skip_number: int, limit_number: int):
    #     return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)

    async def get_buques_activos(self) -> List[ViajesActResponse]:
        return await self._repo.get_buques_disponibles()

    async def get_camiones_activos(self) -> List[ViajesActResponse]:
        return await self._repo.get_camiones_disponibles()

    async def create_buque_nuevo(self, viaje_create: ViajeBuqueExtCreate) -> ViajesResponse:

        # 1. Validar si  puerto_id ya existe
        if await self.get_viaje_by_puerto_id(viaje_create.puerto_id):
            raise EntityAlreadyRegisteredException(f"Ya existe un viaje con puerto_id '{viaje_create.puerto_id}'")

        # 2. Se crea la flota sino existe en la BD
        nueva_flota = FlotaCreate.model_validate(viaje_create)
        await self.flotas_service.create_flota_if_not_exists(nueva_flota)

        # 3. Obtener flota (ya creada o existente)
        flota = await self.flotas_service.get_flota_by_ref(ref=viaje_create.referencia)
        if not flota:
            raise BaseException(f"No se pudo obtener flota con tipo '{viaje_create.tipo}' y ref '{viaje_create.referencia}'")

        # 4. Se ajusta el schema al requerido
        viaje_data = viaje_create.model_dump(exclude={"referencia","estado"})
        viaje_data["flota_id"] = flota.id

        # 5. Crea registro en la base de datos (Flotas)
        db_viaje = ViajeCreate(**viaje_data)
        await self._repo.create(db_viaje)

        # 6. Se consulta el viaje recíen añadido en DB
        created_viaje = await self.get_viaje_by_puerto_id(viaje_create.puerto_id)

        return ViajesResponse(**created_viaje.__dict__)

    async def create_camion_nuevo(self, viaje_create: ViajeCamionExtCreate) -> ViajesResponse:

        # 1. Validar si puerto_id ya existe
        if await self.get_viaje_by_puerto_id(viaje_create.puerto_id):
            raise EntityAlreadyRegisteredException(f"Ya existe un viaje con puerto_id '{viaje_create.puerto_id}'")

        # 2. Se crea la flota sino existe en la BD
        nueva_flota = FlotaCreate.model_validate(viaje_create)
        await self.flotas_service.create_flota_if_not_exists(nueva_flota)

        # 3. Obtener flota (ya creada o existente)
        flota = await self.flotas_service.get_flota_by_ref(ref=viaje_create.referencia)
        if not flota:
            raise BaseException(f"No se pudo obtener flota con tipo '{viaje_create.tipo}' y ref '{viaje_create.referencia}'")

        # 4. Se obtiene material_id basado en el nombre del material
        material_id = await self.mat_service.get_mat_by_name(viaje_create.material_name)
        if material_id is None:
            raise BaseException(f"Material '{viaje_create.material_name}' no existe")

        # 5. Se ajusta el schema al requerido
        viaje_data = viaje_create.model_dump(exclude={"referencia","puntos"})
        viaje_data["flota_id"] = flota.id
        viaje_data["material_id"] = material_id

        # 6. Crea registro en la base de datos (Flotas)
        db_viaje = ViajeCreate(**viaje_data)
        await self._repo.create(db_viaje)

        # 7. Se consulta el viaje recíen añadido en DB
        created_viaje = await self.get_viaje_by_puerto_id(viaje_create.puerto_id)

        return ViajesResponse(**created_viaje.__dict__)


    async def chg_estado_buque(self, puerto_id: str, estado: bool) -> FlotasResponse:
        viaje = await self.get_viaje_by_puerto_id(puerto_id)
        if not viaje:
            raise BaseException(f"Viaje con puerto_id: '{puerto_id}' no existe")

        flota = await self.flotas_service.get_flota(viaje.flota_id)
        if not flota:
            raise BaseException(f"Flota con id '{viaje.flota_id}' no existe")

        updated_buque = await self.flotas_service.update_status(flota, estado)
        return updated_buque

    async def chg_camion_ingreso(self, puerto_id: str, fecha: datetime) -> ViajesResponse:
        viaje = await self.get_viaje_by_puerto_id(puerto_id)
        if not viaje:
            raise BaseException(f"Viaje con puerto_id: '{puerto_id}' no existe")

        flota = await self.flotas_service.get_flota(viaje.flota_id)
        if not flota:
            raise BaseException(f"Flota con id '{viaje.flota_id}' no existe")
        elif flota.tipo != "camion":
            raise BaseException(f"La flota es del tipo  '{flota.tipo}' diferente al tipo esperado 'camion'")

        update_data = ViajeUpdate(fecha_llegada=fecha)
        updated = await self._repo.update(viaje.id, update_data)
        log.info(f"Ingreso actualizado para viaje: {viaje.puerto_id} a {fecha}")
        return updated

    async def chg_camion_salida(self, puerto_id: str, fecha: datetime, peso:Decimal) -> ViajesResponse:
        viaje = await self.get_viaje_by_puerto_id(puerto_id)
        if not viaje:
            raise BaseException(f"Viaje con puerto_id: '{puerto_id}' no existe")

        flota = await self.flotas_service.get_flota(viaje.flota_id)
        if not flota:
            raise BaseException(f"Flota con id '{viaje.flota_id}' no existe")
        elif flota.tipo != "camion":
            raise BaseException(f"La flota es del tipo  '{flota.tipo}' diferente al tipo esperado 'camion'")

        update_data = ViajeUpdate(fecha_salida=fecha, peso_real=peso)
        updated = await self._repo.update(viaje.id, update_data)
        log.info(f"Ingreso actualizado para viaje: {viaje.puerto_id} a {fecha}")
        return updated

    async def create_buque_load(self, bl_input: BlsExtCreate) -> BlsResponse:
        # Verifica que el viaje asociado exista
        viaje = await self.get_viaje_by_puerto_id(bl_input.puerto_id)
        if not viaje:
            raise BaseException(f"No existe un viaje con puerto_id='{bl_input.puerto_id}'")

        # Verifica que no exista un BL con el mismo número
        existing_bl = await self.bls_service.get_bl_by_num(bl_input.no_bl)
        if existing_bl:
            raise BaseException(f"El número de BL '{bl_input.no_bl}' ya fue registrado")

        # Obtiene el ID del material
        material_id = await self.mat_service.get_mat_by_name(bl_input.material_name)
        if material_id is None:
            raise BaseException(f"El material '{bl_input.material_name}' no existe")

        # Obtiene el ID del cliente
        cliente_id = await self.clientes_service.get_cliente_by_name(bl_input.cliente_name)
        if cliente_id is None:
            raise BaseException(f"El cliente '{bl_input.cliente_name}' no existe")

        # Prepara los datos para la creación
        bl_data = bl_input.model_dump(exclude={"material_name", "puerto_id", "cliente_name"})
        bl_data.update({
            "flota_id": bl_input.flota_id,
            "cliente_id": cliente_id,
            "material_id": material_id,
            "viaje_id": viaje.id,
        })

        # Crea la instancia de BL
        db_bl = BlsCreate(**bl_data)
        await self.bls_service.create(db_bl)

        # Retorna la entidad creada
        created_bl = await self.bls_service.get_bl_by_num(bl_input.no_bl)
        return BlsResponse(**created_bl.__dict__)

    # async def set_buque_load(self, voyage: int, no_bl:str, customer:str, product: str, peso: float) -> FlotasResponse:
    #     flota = await self._repo.get_by_id(voyage)
    #     if not flota:
    #         raise BaseException(f"Flota con id '{voyage}' no encontrada")
    #
    #     flota_buque = await self.flotas_service.get_flota_by_ref(flota.referencia)
    #     if not flota_buque:
    #         raise BaseException(f"Flota con ref '{flota.referencia}' no existe")
    #
    #     updated_buque = await self.flotas_service.update_status(flota_buque, True)
    #     return updated_buque


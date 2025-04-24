from typing import List, Optional
from core.exceptions.base_exception import BaseException
from repositories.flotas_repository import FlotasRepository
from repositories.materiales_repository import MaterialesRepository
from services.materiales_service import MaterialesService
from services.buques_service import BuquesService
from services.camiones_service import CamionesService
from schemas.flotas_schema import (
    FlotasResponse, FlotaCreate, FlotaBuqueExtCreate, FlotaUpdate, FlotasActResponse, FlotaCamionExtCreate
)
from schemas.buques_schema import BuquesResponse
from core.exceptions.entity_exceptions import EntityAlreadyRegisteredException


class FlotasService:

    def __init__(self, flotas_repository: FlotasRepository, mat_service : MaterialesService, buque_service : BuquesService, camion_service: CamionesService) -> None:
        self._repo = flotas_repository
        self.mat_service = mat_service
        self.buque_service = buque_service
        self.camion_service = camion_service

    async def create_flota(self, flota: FlotaCreate) -> FlotasResponse:
        return await self._repo.create(flota)

    async def update_flota(self, id: int, flota: FlotaUpdate) -> Optional[FlotasResponse]:
        return await self._repo.update(id, flota)

    async def delete_flota(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_flota(self, id: int) -> Optional[FlotasResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_flotas(self) -> List[FlotasResponse]:
        return await self._repo.get_all()

    async def get_paginated_flotas(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)

    async def get_buques_activos(self) -> List[FlotasActResponse]:
        return await self._repo.get_buques_activos()

    async def get_camiones_activos(self) -> List[FlotasActResponse]:
        return await self._repo.get_camiones_activos()

    async def create_buque_nuevo(self, buque_create: FlotaBuqueExtCreate) -> FlotasResponse:
        """ Check if a flota with the given ID already exists"""
        existing_flota = await self._repo.get_by_id(buque_create.id)
        if existing_flota:
            raise EntityAlreadyRegisteredException(f"Flota with ID '{buque_create.id}'")

        """Creates a new Flota by looking up the material ID using the material name."""
        material_id = await self.mat_service.get_mat_by_name(buque_create.material_name)
        if material_id is None:
            raise BaseException(f"Material '{buque_create.material_name}' no encontrado")

        # Se crea el buque sino existe en la BD
        await self.buque_service.create_buque_if_not_exists(buque_create.referencia)

        flota_data = buque_create.model_dump(exclude={"material_name"})
        flota_data["material_id"] = material_id

        #  Crea una instancia del modelo de la base de datos (Flotas)
        db_flota = FlotaCreate(**flota_data)

        await self._repo.create(db_flota)  # Ejecuta la creación en la base de datos

        return {"id": buque_create.id}  # Retorna solo el ID de la flota creada

    async def create_camion(self, camion_create: FlotaCamionExtCreate) -> FlotasResponse:
        """ Check if a flota with the given ID already exists"""
        existing_flota = await self._repo.get_by_id(camion_create.id)
        if existing_flota:
            raise EntityAlreadyRegisteredException(f"Flota with ID '{camion_create.id}'")

        """Creates a new Flota by looking up the material ID using the material name."""
        material_id = await self.mat_service.get_mat_by_name(camion_create.material_name)
        if material_id is None:
            raise BaseException(f"Material '{camion_create.material_name}' no encontrado")

        # Se crea el camion sino existe en la BD
        await self.camion_service.create_camion_if_not_exists(camion_create.referencia, camion_create.puntos)

        camion_data = camion_create.model_dump(exclude={"material_name"})
        camion_data["material_id"] = material_id

        #  Crea una instancia del modelo de la base de datos (Flotas)
        db_flota = FlotaCreate(**camion_data)

        await self._repo.create(db_flota)  # Ejecuta la creación en la base de datos

        return {"id": camion_create.id}  # Retorna solo el ID de la flota creada


    async def chg_estado_buque(self, flota_id: int, estado: bool) -> BuquesResponse:
        flota = await self._repo.get_by_id(flota_id)
        if not flota:
            raise BaseException(f"Flota con id '{flota_id}' no encontrada")

        buque = await self.buque_service.get_buque_by_name(flota.referencia)
        if not buque:
            raise BaseException(f"Buque con nombre '{flota.referencia}' no encontrado")

        updated_buque = await self.buque_service.update_status(buque, estado)
        return updated_buque

    async def set_buque_load(self, voyage: int, no_bl:str, customer:str, product: str, peso: float) -> BuquesResponse:
        flota = await self._repo.get_by_id(voyage)
        if not flota:
            raise BaseException(f"Flota con id '{voyage}' no encontrada")

        buque = await self.buque_service.get_buque_by_name(flota.referencia)
        if not buque:
            raise BaseException(f"Buque con nombre '{flota.referencia}' no encontrado")

        updated_buque = await self.buque_service.update_status(buque, True)
        return updated_buque


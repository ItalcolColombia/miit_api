from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Camiones
from schemas.camiones_schema import CamionResponse, CamionCreate
from repositories.camiones_repository import CamionesRepository


class CamionesService:

    def __init__(self, buques_repository: CamionesRepository) -> None:
        self._repo = buques_repository

    async def create_camion(self, mat: CamionCreate) -> CamionResponse:
        return await self._repo.create(mat)

    async def update_camion(self, id: int, mat: CamionResponse) -> Optional[CamionResponse]:
        return await self._repo.update(id, mat)

    async def delete_camion(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_camion(self, id: int) -> Optional[CamionResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_camiones(self) -> List[CamionResponse]:
        return await self._repo.get_all()

    async def get_paginated_camiones(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)


    async def get_camion_by_placa(self, placa: str) -> Optional[CamionResponse]:
        """
                             Find a Camion by their 'Placa'

                             Args:
                                 placa: The truck plate param to filter.

                             Returns:
                                 Camion object filtered by 'placa'.
                             """
        return await self._repo.get_camion_by_plate(placa)

    async def create_camion_if_not_exists(self, placa: str, puntos: int) -> CamionResponse:
        return await self._repo.create_camion_if_not_exists(placa, puntos)

    async def update_points(self, truck: Camiones, puntos: int ) -> CamionResponse:
        return await self._repo.update_camion(truck, puntos)
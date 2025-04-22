from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Buques
from schemas.buques_schema import BuquesResponse, BuqueCreate
from repositories.buques_repository import BuquesRepository


class BuquesService:

    def __init__(self, buques_repository: BuquesRepository) -> None:
        self._repo = buques_repository

    async def create_buque(self, mat: BuqueCreate) -> BuquesResponse:
        return await self._repo.create(mat)

    async def update_buque(self, id: int, mat: BuquesResponse) -> Optional[BuquesResponse]:
        return await self._repo.update(id, mat)

    async def delete_buque(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_buque(self, id: int) -> Optional[BuquesResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_buques(self) -> List[BuquesResponse]:
        return await self._repo.get_all()

    async def get_paginated_buques(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)


    async def get_buque_by_name(self, nombre: str) -> Optional[BuquesResponse]:
        """
                             Find a Buque by their 'name'

                             Args:
                                 nombre: The buque name param to filter.

                             Returns:
                                 Buque object filtered by 'name'.
                             """
        return await self._repo.get_buque_by_name(nombre)

    async def create_buque_if_not_exists(self, nombre: str) -> BuquesResponse:
        return await self._repo.create_buque_if_not_exists(nombre)

    async def update_status(self, buque: Buques, estado: bool ) -> BuquesResponse:
        return await self._repo.update_buque_estado(buque, estado)
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Bls
from schemas.bls_schema import BlsResponse, BlsCreate
from repositories.bls_repository import BlsRepository


class BlsService:

    def __init__(self, bls_repository: BlsRepository) -> None:
        self._repo = bls_repository

    async def create_bls(self, bl: BlsCreate) -> BlsResponse:
        return await self._repo.create(bl)

    async def update_bls(self, id: int, bl: BlsCreate) -> Optional[BlsResponse]:
        return await self._repo.update(id, bl)

    async def delete_bls(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_bls(self, id: int) -> Optional[BlsResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_bls(self) -> List[BlsResponse]:
        return await self._repo.get_all()

    async def get_paginated_bls(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)

    async def get_bls_by_flota_id(self, flota_id: int) -> Optional[BlsResponse]:
        """
         Find a Bls by their 'name'

         Args:
             flota_id: The flota id param to filter.

         Returns:
             Buque object filtered by 'name'.
         """
        return await self._repo.get_by_id(flota_id)

    # async def create_buque_if_not_exists(self, nombre: str) -> BuquesResponse:
    #     return await self._repo.create_buque_if_not_exists(nombre)
    #
    # async def update_status(self, buque: Buques, estado: bool ) -> BuquesResponse:
    #     return await self._repo.update_buque_estado(buque, estado)
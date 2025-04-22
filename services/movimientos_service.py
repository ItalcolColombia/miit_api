from typing import List, Optional
from schemas.movimientos_schema import MovimientosResponse, MovimientosCreate, MovimientosUpdate
from repositories.movimientos_repository import MovimientosRepository

class MovimientosService:

    def __init__(self, mov_repository: MovimientosRepository) -> None:
        self._repo = mov_repository


    async def create_mov(self, mov: MovimientosCreate) -> MovimientosResponse:
        return await self._repo.create(mov)

    async def update_mov(self, id: int, mov: MovimientosUpdate) -> Optional[MovimientosResponse]:
        return await self._repo.update(id, mov)

    async def delete_mov(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_mov(self, id: int) -> Optional[MovimientosResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_mov(self) -> List[MovimientosResponse]:
        return await self._repo.get_all()

    async def get_paginated_mov(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)

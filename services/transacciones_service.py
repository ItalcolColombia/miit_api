from typing import List, Optional
from schemas.pesadas_schema import PesadaResponse, PesadaCreate, PesadaUpdate
from repositories.transacciones_repository import TransaccionesRepository

class TransaccionesService:

    def __init__(self, mov_repository: TransaccionesRepository) -> None:
        self._repo = mov_repository


    async def create_transaccion(self, mat: PesadaCreate) -> PesadaResponse:
        return await self._repo.create(mat)

    async def update_transaccion(self, id: int, mat: PesadaUpdate) -> Optional[PesadaResponse]:
        return await self._repo.update(id, mat)

    async def delete_transaccion(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_transaccion(self, id: int) -> Optional[PesadaResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_transacciones(self) -> List[PesadaResponse]:
        return await self._repo.get_all()

    async def get_paginated_transacciones(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)


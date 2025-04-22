from typing import List, Optional
from schemas.pesadas_schema import PesadaResponse, PesadaCreate, PesadaUpdate
from repositories.pesadas_repository import PesadasRepository

class PesadasService:

    def __init__(self, mov_repository: PesadasRepository) -> None:
        self._repo = mov_repository


    async def create_pesada(self, pesada: PesadaCreate) -> PesadaResponse:
        return await self._repo.create(pesada)

    async def update_pesada( self, id: int, pesada: PesadaUpdate) -> Optional[PesadaResponse]:
        return await self._repo.update(id, pesada)

    async def delete_pesada(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_pesada(self, id: int) -> Optional[PesadaResponse]:
        return await self._repo.get_by_id(id)

    async def get_pesada_by_idtrans(self, idTran: int) -> Optional[PesadaResponse]:
        return await self._repo.get_pesada_by_transaccion(idTran)

    async def get_all_pesadas(self) -> List[PesadaResponse]:
        return await self._repo.get_all()

    async def get_paginated_pesadas(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)



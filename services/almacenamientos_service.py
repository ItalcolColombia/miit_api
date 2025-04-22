from typing import List, Optional
from schemas.almacenamientos_schema import AlmacenamientoResponse, AlmacenamientoCreate, AlmacenamientoUpdate
from repositories.almacenamientos_repository import AlmacenamientosRepository

class AlmacenamientosService:

    def __init__(self, mat_repository: AlmacenamientosRepository) -> None:
        self._repo = mat_repository


    async def create_alm(self, mat: AlmacenamientoCreate) -> AlmacenamientoResponse:
        return await self._repo.create(mat)

    async def update_alm(
        self, id: int, mat: AlmacenamientoUpdate
    ) -> Optional[AlmacenamientoResponse]:
        return await self._repo.update(id, mat)

    async def delete_alm(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_alm(self, id: int) -> Optional[AlmacenamientoResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_alm(self) -> List[AlmacenamientoResponse]:
        return await self._repo.get_all()


    async def get_mat_by_name(self, nombre: str) -> Optional[AlmacenamientoResponse]:
        """
                             Find an Almacenamiento by their 'name'

                             Args:
                                 nombre: The Almacenamiento name param to filter.

                             Returns:
                                 Almacenamiento object filtered by 'name'.
                             """
        return await self._repo.get_alm_id_by_name(nombre)

from typing import List, Optional
from schemas.materiales_schema import MaterialesResponse, MaterialesCreate, MaterialesUpdate
from repositories.materiales_repository import MaterialesRepository

class MaterialesService:

    def __init__(self, mat_repository: MaterialesRepository) -> None:
        self._repo = mat_repository


    async def create_mat(self, mat: MaterialesCreate) -> MaterialesResponse:
        return await self._repo.create(mat)

    async def update_mat(self, id: int, mat: MaterialesUpdate) -> Optional[MaterialesResponse]:
        return await self._repo.update(id, mat)

    async def delete_mat(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_mat(self, id: int) -> Optional[MaterialesResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_mat(self) -> List[MaterialesResponse]:
        return await self._repo.get_all()

    async def get_paginated_mat(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)

    async def get_mat_by_name(self, nombre: str) -> Optional[MaterialesResponse]:
        """
                             Find a Material by their 'name'

                             Args:
                                 nombre: The Material name param to filter.

                             Returns:
                                 Material object filtered by 'name'.
                             """
        return await self._repo.get_material_id_by_name(nombre)

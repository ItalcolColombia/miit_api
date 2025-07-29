from typing import List, Optional
from fastapi_pagination import Page, Params

from sqlalchemy import select
from starlette import status

from core.exceptions.base_exception import BasedException
from database.models import Materiales
from schemas.materiales_schema import MaterialesResponse, MaterialesCreate, MaterialesUpdate
from repositories.materiales_repository import MaterialesRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class MaterialesService:

    def __init__(self, mat_repository: MaterialesRepository) -> None:
        self._repo = mat_repository



    async def create_mat(self, mat: MaterialesCreate) -> MaterialesResponse:
        """
        Create a new material in the database.

        Args:
            mat (MaterialesCreate): The data for the material to be created.

        Returns:
            MaterialesResponse: The created material object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            new_material = await self._repo.create(mat)
            return new_material
        except Exception as e:
            log.error(f"Error al crear material: {e}")
            raise BasedException(
                message="Error inesperado al crear el material.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_mat(self, mat_id: int, mat: MaterialesUpdate) -> Optional[MaterialesResponse]:
        """
        Update an existing material in the database.

        Args:
            mat_id (int): The ID of the material to update.
            mat (MaterialesUpdate): The updated material data.

        Returns:
            Optional[MaterialesResponse]: The updated material object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            updated_material = await self._repo.update(mat_id, mat)
            return updated_material
        except Exception as e:
            log.error(f"Error al actualizar material con ID {mat_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar el material.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete_mat(self, mat_id: int) -> bool:
        """
        Delete a material from the database.

        Args:
            mat_id (int): The ID of the material to delete.

        Returns:
            bool: True if the material was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(mat_id)
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar material con ID {mat_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar el material.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_mat(self, mat_id: int) -> Optional[MaterialesResponse]:
        """
        Retrieve a material by its ID.

        Args:
            mat_id (int): The ID of the material to retrieve.

        Returns:
            Optional[MaterialesResponse]: The material object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            material = await self._repo.get_by_id(mat_id)
            return material
        except Exception as e:
            log.error(f"Error al obtener material con ID {mat_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el material.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_mat(self) -> List[MaterialesResponse]:
        """
        Retrieve all materials from the database.

        Returns:
            List[MaterialesResponse]: A list of all material objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            materials = await self._repo.get_all()
            return materials
        except Exception as e:
            log.error(f"Error al obtener todos los materiales: {e}")
            raise BasedException(
                message="Error inesperado al obtener los materiales.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_paginated_mat(self, params: Params = Params()) -> Page[MaterialesResponse]:
        """
        Retrieve a paginated list of materials from the database.

        Args:
           params (Params): Pagination parameters.

        Returns:
            Page[MaterialesResponse]: A paginated list of material objects within the specified range.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            query = select(Materiales)

            return await self._repo.get_all_paginated(query=query, params=params)

        except Exception as e:
            log.error(f"Error al obtener materiales paginados: {e}")
            raise BasedException(
                message="Error inesperado al obtener los materiales paginados.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_mat_by_name(self, nombre: str) -> Optional[MaterialesResponse]:
        """
        Retrieve a material by its name.

        Args:
            nombre (str): The name of the material to filter by.

        Returns:
            Optional[MaterialesResponse]: The material object filtered by name, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            material = await self._repo.get_material_id_by_name(nombre)
            return material
        except Exception as e:
            log.error(f"Error al obtener material con nombre {nombre}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el material por nombre.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

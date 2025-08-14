from typing import List, Optional

from starlette import status
from fastapi_pagination import Page, Params
from sqlalchemy import select
from core.exceptions.base_exception import BasedException
from database.models import VAlmMateriales
from repositories.almacenamientos_materiales_repository import AlmacenamientosMaterialesRepository
from schemas.almacenamientos_materiales_schema import VAlmMaterialesResponse, AlmacenamientoMaterialesCreate
from schemas.almacenamientos_materiales_schema import AlmacenamientoMaterialesResponse, AlmacenamientoMaterialesCreate, AlmacenamientoMaterialesUpdate, VAlmMaterialesResponse

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class AlmacenamientosMaterialesService:

    def __init__(self, alm_mat_repo: AlmacenamientosMaterialesRepository) -> None:
        self._repo = alm_mat_repo


    async def create_alm_mat(self, alm_mat: AlmacenamientoMaterialesCreate) -> AlmacenamientoMaterialesResponse:
        """
        Create a new almacenamiento in the database.

        Args:
            alm_mat (AlmacenamientoMaterialesCreate): The data for the almacenamiento to be created.

        Returns:
            AlmacenamientoMaterialesResponse: The created almacenamiento object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            new = await self._repo.create(alm_mat)
            return new
        except Exception as e:
            log.error(f"Error al crear almacenamiento material: {e}")
            raise BasedException(
                message="Error inesperado al crear el almacenamiento material.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_alm(self, alm_id: int, mat: AlmacenamientoMaterialesUpdate) -> Optional[AlmacenamientoMaterialesResponse]:
        """
        Update an existing almacenamiento in the database.

        Args:
            alm_id (int): The ID of the almacenamiento to update.
            mat (AlmacenamientoMaterialesUpdate): The updated almacenamiento data.

        Returns:
            Optional[AlmacenamientoMaterialesResponse]: The updated almacenamiento object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            updated_almacenamiento = await self._repo.update(alm_id, mat)
            return updated_almacenamiento
        except Exception as e:
            log.error(f"Error al actualizar almacenamiento con ID {alm_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar el almacenamiento.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete_alm(self, alm_id: int) -> bool:
        """
        Delete an almacenamiento material from the database.

        Args:
            alm_id (int): The ID of the almacenamiento to delete.

        Returns:
            bool: True if the almacenamiento was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(alm_id)
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar almacenamiento con ID {alm_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar el almacenamiento.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_pag_alm_mat(self, name: Optional[str] = None, params: Params = Params()) -> Page[VAlmMaterialesResponse]:
        """
        Retrieve a paginated list of alm_materiales, optionally filtered by name.

        Args:
            name (Optional[str]): The almacenamiento name to filter (optional).
            params (Params): Pagination parameters.

        Returns:
            Page[VAlmMaterialesResponse]: A paginated list of alm_materiales.

        Raises:
            BasedException: If retrieval fails due to database or other errors.
        """
        try:
            query = (
                select(VAlmMateriales)
            )
            if name is not None:
                query = query.where(VAlmMateriales.almacenamiento == name)
            return await self._repo.get_all_paginated(query=query, params=params)

        except Exception as e:
            log.error(f"Error al obtener alm_materiales con nombre (opcional) {name}: {e}")
            raise BasedException(
                message="Error al obtener alm_materiales",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



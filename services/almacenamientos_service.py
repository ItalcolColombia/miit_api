from typing import List, Optional

from starlette import status
from fastapi_pagination import Page, Params
from sqlalchemy import select
from core.exceptions.base_exception import BasedException
from database.models import VAlmMateriales
from schemas.almacenamientos_materiales_schema import VAlmMaterialesResponse
from schemas.almacenamientos_schema import AlmacenamientoResponse, AlmacenamientoCreate, AlmacenamientoUpdate
from repositories.almacenamientos_repository import AlmacenamientosRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class AlmacenamientosService:

    def __init__(self, mat_repository: AlmacenamientosRepository) -> None:
        self._repo = mat_repository


    async def create_alm(self, mat: AlmacenamientoCreate) -> AlmacenamientoResponse:
        """
        Create a new almacenamiento in the database.

        Args:
            mat (AlmacenamientoCreate): The data for the almacenamiento to be created.

        Returns:
            AlmacenamientoResponse: The created almacenamiento object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            new_almacenamiento = await self._repo.create(mat)
            return new_almacenamiento
        except Exception as e:
            log.error(f"Error al crear almacenamiento: {e}")
            raise BasedException(
                message="Error inesperado al crear el almacenamiento.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_alm(self, alm_id: int, mat: AlmacenamientoUpdate) -> Optional[AlmacenamientoResponse]:
        """
        Update an existing almacenamiento in the database.

        Args:
            alm_id (int): The ID of the almacenamiento to update.
            mat (AlmacenamientoUpdate): The updated almacenamiento data.

        Returns:
            Optional[AlmacenamientoResponse]: The updated almacenamiento object, or None if not found.

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
        Delete an almacenamiento from the database.

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

    async def get_alm(self, alm_id: int) -> Optional[AlmacenamientoResponse]:
        """
        Retrieve an almacenamiento by its ID.

        Args:
            alm_id (int): The ID of the almacenamiento to retrieve.

        Returns:
            Optional[AlmacenamientoResponse]: The almacenamiento object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            almacenamiento = await self._repo.get_by_id(alm_id)
            return almacenamiento
        except Exception as e:
            log.error(f"Error al obtener almacenamiento con ID {alm_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el almacenamiento.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_alm(self) -> List[AlmacenamientoResponse]:
        """
        Retrieve all almacenamientos from the database.

        Returns:
            List[AlmacenamientoResponse]: A list of all almacenamiento objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            almacenamientos = await self._repo.get_all()
            return almacenamientos
        except Exception as e:
            log.error(f"Error al obtener todos los almacenamientos: {e}")
            raise BasedException(
                message="Error inesperado al obtener los almacenamientos.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    async def get_mat_by_name(self, nombre: str) -> Optional[AlmacenamientoResponse]:
        """
        Retrieve an almacenamiento by its name.

        Args:
            nombre (str): The name of the almacenamiento to filter by.

        Returns:
            Optional[AlmacenamientoResponse]: The almacenamiento object filtered by name, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            # Find an Almacenamiento by their 'name'
            almacenamiento = await self._repo.get_alm_id_by_name(nombre)
            return almacenamiento
        except Exception as e:
            log.error(f"Error al obtener almacenamiento con nombre {nombre}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el almacenamiento por nombre.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
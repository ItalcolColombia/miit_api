from typing import List, Optional

from starlette import status

from core.exceptions.base_exception import BasedException
from schemas.bls_schema import BlsResponse, BlsCreate, BlsUpdate
from repositories.bls_repository import BlsRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class BlsService:

    def __init__(self, bls_repository: BlsRepository) -> None:
        self._repo = bls_repository


    async def create(self, bl: BlsCreate) -> BlsResponse:
        """
        Create a new BL in the database.

        Args:
            bl (BlsCreate): The data for the BL to be created.

        Returns:
            BlsResponse: The created BL object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            creado = await self._repo.create(bl)
            log.info(f"BL creado con N°: {bl.no_bl}")
            return creado
        except Exception as e:
            log.error(f"Error al crear BL: {e}")
            raise BasedException(
                message="Error inesperado al crear el BL.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def update(self, bl_id: int, bl: BlsUpdate) -> Optional[BlsResponse]:
        """
        Update an existing BL in the database.

        Args:
            bl_id (int): The ID of the BL to update.
            bl (BlsUpdate): The updated BL data.

        Returns:
            Optional[BlsResponse]: The updated BL object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            actualizado = await self._repo.update(bl_id, bl)
            log.info(f"BL actualizado con ID: {bl_id}")
            return actualizado
        except Exception as e:
            log.error(f"Error al actualizar BL con ID {bl_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar el BL.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete(self, bl_id: int) -> bool:
        """
        Delete a BL from the database.

        Args:
            bl_id (int): The ID of the BL to delete.

        Returns:
            bool: True if the BL was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(bl_id)
            log.info(f"BL eliminado con ID: {bl_id}")
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar BL con ID {bl_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar el BL.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get(self, bl_id: int) -> Optional[BlsResponse]:
        """
        Retrieve a BL by its ID.

        Args:
            bl_id (int): The ID of the BL to retrieve.

        Returns:
            Optional[BlsResponse]: The BL object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            bl = await self._repo.get_by_id(bl_id)
            return BlsResponse.model_validate(bl) if bl else None
        except Exception as e:
            log.error(f"Error al obtener BL con ID {bl_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el BL.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all(self) -> List[BlsResponse]:
        """
        Retrieve all BLs from the database.

        Returns:
            List[BlsResponse]: A list of all BL objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            bls = await self._repo.get_all()
            return [BlsResponse.model_validate(bl) for bl in bls]
        except Exception as e:
            log.error(f"Error al obtener todos los BLs: {e}")
            raise BasedException(
                message="Error inesperado al obtener los BLs.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_bl_if_not_exist(self, bl_data: BlsCreate) -> BlsResponse:
        """
        Check if a BL with the same no_bl already exists. If not, create a new one.

        Args:
            bl_data (BlsCreate): The data for the BL to be created.

        Returns:
            BlsResponse: The existing or newly created BL object.

        Raises:
            BasedException: For unexpected errors during the creation or retrieval process.
        """
        try:
            bl_existente = await self._repo.get_bls_no_bl(bl_data.no_bl)
            if bl_existente:
                log.info(f"BL ya existente con N°: {bl_data.no_bl}")
                return BlsResponse.model_validate(bl_existente)

            bl_creado = await self._repo.create(bl_data)
            log.info(f"Se creó BL: {bl_creado.no_bl}")
            return BlsResponse.model_validate(bl_creado)
        except Exception as e:
            log.error(f"Error al crear o consultar BL: {bl_data.no_bl} - {e}")
            raise BasedException(
                message="Error inesperado al crear o consultar el BL.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_bl_by_num(self, number: str) -> Optional[BlsResponse]:
        """
        Retrieve a BL by its number.

        Args:
            number (str): The number (no_bl) of the BL to filter by.

        Returns:
            Optional[BlsResponse]: The BL object filtered by number, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            # Find a Bl by their 'number'
            bl = await self._repo.get_bls_no_bl(number)
            return BlsResponse.model_validate(bl) if bl else None
        except Exception as e:
            log.error(f"Error al obtener BL con número {number}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el BL por número.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
   
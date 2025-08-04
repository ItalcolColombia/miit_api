from typing import List, Optional
from starlette import status

from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import EntityNotFoundException
from database.models import Flotas
from schemas.flotas_schema import FlotasResponse, FlotaCreate, FlotaUpdate
from repositories.flotas_repository import FlotasRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class FlotasService:

    def __init__(self, flotas_repository: FlotasRepository) -> None:
        self._repo = flotas_repository

    async def create_flota(self, flota_data: FlotaCreate) -> FlotasResponse:
        """
        Create a new flota in the database.

        Args:
            flota_data (FlotaCreate): The data for the flota to be created.

        Returns:
            FlotasResponse: The created flota object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            flota_model = Flotas(**flota_data.model_dump())
            created_flota = await self._repo.create(flota_model)
            log.info(f"Flota creada con referencia: {created_flota.referencia}")
            return FlotasResponse.model_validate(created_flota)
        except Exception as e:
            log.error(f"Error al crear flota: {e}")
            raise BasedException(
                message="Error inesperado al crear la flota.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def update_flota(self, flota_id: int, flota_data: FlotaUpdate) -> Optional[FlotasResponse]:
        """
        Update an existing flota in the database.

        Args:
            flota_id (int): The ID of the flota to update.
            flota_data (FlotaUpdate): The updated flota data.

        Returns:
            Optional[FlotasResponse]: The updated flota object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            flota_model = Flotas(**flota_data.model_dump())
            updated_flota = await self._repo.update(flota_id, flota_model)
            log.info(f"Flota actualizada con ID: {flota_id}")
            return FlotasResponse.model_validate(updated_flota) if updated_flota else None
        except Exception as e:
            log.error(f"Error al actualizar flota con ID {flota_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar la flota.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete_flota(self, flota_id: int) -> bool:
        """
        Delete a flota from the database.

        Args:
            flota_id (int): The ID of the flota to delete.

        Returns:
            bool: True if the flota was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(flota_id)
            log.info(f"Flota eliminada con ID: {flota_id}")
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar flota con ID {flota_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar la flota.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_flota(self, flota_id: int) -> Optional[FlotasResponse]:
        """
        Retrieve a flota by its ID.

        Args:
            flota_id (int): The ID of the flota to retrieve.

        Returns:
            Optional[FlotasResponse]: The flota object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            flota = await self._repo.get_by_id(flota_id)
            return FlotasResponse.model_validate(flota) if flota else None
        except Exception as e:
            log.error(f"Error al obtener flota con ID {flota_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la flota.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_flotas(self) -> List[FlotasResponse]:
        """
        Retrieve all flotas from the database.

        Returns:
            List[FlotasResponse]: A list of all flota objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            flotas = await self._repo.get_all()
            return [FlotasResponse.model_validate(f) for f in flotas]
        except Exception as e:
            log.error(f"Error al obtener todas las flotas: {e}")
            raise BasedException(
                message="Error inesperado al obtener las flotas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_flota_by_ref(self, ref: str) -> Optional[FlotasResponse]:
        """
        Retrieve a flota by its reference.

        Args:
            ref (str): The reference of the flota to filter by.

        Returns:
            Optional[FlotasResponse]: The flota object filtered by reference, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            # Find a Flota by their 'referencia'
            flota = await self._repo.get_flota_by_ref(ref)
            return FlotasResponse.model_validate(flota) if flota else None
        except Exception as e:
            log.error(f"Error al obtener flota con referencia {ref}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la flota por referencia.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_flota_if_not_exists(self, flota_data: FlotaCreate) -> FlotasResponse:
        """
        Check if a flota with the same reference already exists. If not, create a new one.

        Args:
            flota_data (FlotaCreate): The data for the flota to be created.

        Returns:
            FlotasResponse: The existing or newly created flota object.

        Raises:
            BasedException: For unexpected errors during the creation or retrieval process.
        """
        try:
            # Check if a Flota already exists
            flota_existente = await self._repo.get_flota_by_ref(flota_data.referencia)
            if flota_existente:
                log.info(f"Flota ya existente con referencia: {flota_data.referencia}")
                return FlotasResponse.model_validate(flota_existente)

            # Create a new flota
            flota_creada = await self._repo.create(flota_data)
            log.info(f"Se creó flota: {flota_creada.referencia}")
            return FlotasResponse.model_validate(flota_creada)
        except Exception as e:
            log.error(f"Error al crear o consultar flota: {flota_data.referencia} - {e}")
            raise BasedException(
                message="Error inesperado al crear o consultar la flota.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_status(self, flota: Flotas, estado: bool) -> FlotasResponse:
        """
        Update the 'estado' for an existing flota.

        Args:
            flota (Flotas): The flota object whose status needs to be updated.
            estado (bool): The new boolean value for the flota's status (e.g., True for active, False for inactive).

        Returns:
            FlotasResponse: The updated flota object.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:

            update_fields = {
                "estado": estado,
            }
            update_data = FlotaUpdate(**update_fields)
            updated = await self._repo.update(flota.id, update_data)
            log.info(f"Estado modificado para flota {flota.referencia} a {estado}")
            return FlotasResponse.model_validate(updated)
        except Exception as e:
            log.error(f"Error al cambiar estado de flota: {flota.referencia} - {e}")
            raise BasedException(
                message="Error inesperado al cambiar el estado de la flota.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def update_points(self, flota: Flotas, points: int) -> FlotasResponse:
        """
        Update the 'puntos' (points) for an existing flota.

        Args:
            flota (Flotas): The flota object whose points need to be updated.
            points (int): The new integer value for the flota's points.

        Returns:
            FlotasResponse: The updated flota object.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            update_fields = {
                "puntos": points,
            }
            update_data = FlotaUpdate(**update_fields)
            updated = await self._repo.update(flota.id, update_data)
            log.info(f"Puntos actualizados para flota: {flota.referencia} a {points}")
            return FlotasResponse.model_validate(updated)
        except Exception as e:
            log.error(f"Error al cambiar puntos de flota: {flota.referencia} - {e}")
            raise BasedException(
                message="Error inesperado al cambiar los puntos de la flota.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def chg_points(self, ref: str, points: int) -> FlotasResponse:
        """
        Update the points for a flota identified by its reference.

        Args:
            ref (str): The reference of the flota to update.
            points (int): The new integer value for the flota's points.

        Returns:
            FlotasResponse: The updated flota object.

        Raises:
            EntityNotFoundException: If the flota with the given reference is not found.
            BasedException: For unexpected errors during the update process.
        """
        try:
            flota = await self.get_flota_by_ref(ref)
            if not flota:
                raise EntityNotFoundException(f"Flota con referencia: '{ref}' no encontrada")

            updated_buque = await self.update_points(flota, points)
            return updated_buque
        except EntityNotFoundException as e:
            raise e
        except Exception as e:
            log.error(f"Error al actualizar puntos de flota con referencia {ref}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar los puntos de la flota.",
                status_code=status.HTTP_409_CONFLICT
            )
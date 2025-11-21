from typing import List, Optional

from starlette import status

from core.exceptions.base_exception import BasedException
from database.models import Bls
from repositories.clientes_repository import ClientesRepository
from schemas.clientes_schema import ClientesResponse, ClienteCreate, ClienteUpdate
from utils.logger_util import LoggerUtil

log = LoggerUtil()


class ClientesService:

    def __init__(self, clientes_repository: ClientesRepository) -> None:
        self._repo = clientes_repository

    async def create(self, bl: ClienteCreate) -> ClientesResponse:
        """
        Create a new cliente in the database.

        Args:
            bl (ClienteCreate): The data for the cliente to be created.

        Returns:
            ClientesResponse: The created cliente object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            cliente_model = Bls(**bl.model_dump())
            created_bl = await self._repo.create(cliente_model)
            log.info(f"Cliente creado con N°: {created_bl.no_bl}")
            return ClientesResponse.model_validate(created_bl)
        except Exception as e:
            log.error(f"Error al crear cliente: {e}")
            raise BasedException(
                message="Error inesperado al crear el cliente.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def update(self, cliente_id: int, bl: ClienteUpdate) -> Optional[ClientesResponse]:
        """
        Update an existing cliente in the database.

        Args:
            cliente_id (int): The ID of the cliente to update.
            bl (ClienteUpdate): The updated cliente data.

        Returns:
            Optional[ClientesResponse]: The updated cliente object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            cliente_model = Bls(**bl.model_dump())
            updated_bl = await self._repo.update(cliente_id, cliente_model)
            log.info(f"Cliente actualizado con ID: {cliente_id}")
            return ClientesResponse.model_validate(updated_bl) if updated_bl else None
        except Exception as e:
            log.error(f"Error al actualizar cliente con ID {cliente_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar el cliente.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete(self, cliente_id: int) -> bool:
        """
        Delete a cliente from the database.

        Args:
            cliente_id (int): The ID of the cliente to delete.

        Returns:
            bool: True if the cliente was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(cliente_id)
            log.info(f"Cliente eliminado con ID: {cliente_id}")
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar cliente con ID {cliente_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar el cliente.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get(self, cliente_id: int) -> Optional[ClientesResponse]:
        """
        Retrieve a cliente by its ID.

        Args:
            cliente_id (int): The ID of the cliente to retrieve.

        Returns:
            Optional[ClientesResponse]: The cliente object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            cliente = await self._repo.get_by_id(cliente_id)
            return ClientesResponse.model_validate(cliente) if cliente else None
        except Exception as e:
            log.error(f"Error al obtener cliente con ID {cliente_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el cliente.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all(self) -> List[ClientesResponse]:
        """
        Retrieve all clientes from the database.

        Returns:
            List[ClientesResponse]: A list of all cliente objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            clientes = await self._repo.get_all()
            return [ClientesResponse.model_validate(cliente) for cliente in clientes]
        except Exception as e:
            log.error(f"Error al obtener todos los clientes: {e}")
            raise BasedException(
                message="Error inesperado al obtener los clientes.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_client_if_not_exists(self, cliente_data: ClienteCreate) -> ClientesResponse:
        """
        Check if a cliente with the same no_bl already exists. If not, create a new one.

        Args:
            cliente_data (ClienteCreate): The data for the cliente to be created.

        Returns:
            ClientesResponse: The existing or newly created cliente object.

        Raises:
            BasedException: For unexpected errors during the creation or retrieval process.
        """
        try:
            # Check if a Cliente already exists
            cliente_existente = await self._repo.get_cliente_by_name(cliente_data.no_bl)
            if cliente_existente:
                log.info(f"Cliente ya existente con N°: {cliente_data.no_bl}")
                return ClientesResponse.model_validate(cliente_existente)

            # Create a new cliente
            cliente_creado = await self._repo.create(cliente_data)
            log.info(f"Se creó Cliente: {cliente_creado.no_bl}")
            return ClientesResponse.model_validate(cliente_creado)
        except Exception as e:
            log.error(f"Error al crear o consultar Cliente: {cliente_data.no_bl} - {e}")
            raise BasedException(
                message="Error inesperado al crear o consultar el cliente.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_cliente_by_name(self, nombre: str) -> Optional[ClientesResponse]:
        """
        Retrieve a cliente by its name.

        Args:
            nombre (str): The name (no_bl) of the cliente to filter by.

        Returns:
            Optional[ClientesResponse]: The cliente object filtered by name, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            # Find a Cliente by their 'name'
            cliente = await self._repo.get_cliente_by_name(nombre)
            return ClientesResponse.model_validate(cliente) if cliente else None
        except Exception as e:
            log.error(f"Error al obtener cliente con nombre {nombre}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el cliente por nombre.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

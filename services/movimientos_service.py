from typing import List, Optional
from fastapi_pagination import Page, Params
from sqlalchemy import select
from starlette import status

from core.exceptions.base_exception import BasedException
from database.models import Movimientos
from schemas.movimientos_schema import MovimientosResponse, MovimientosCreate, MovimientosUpdate
from repositories.movimientos_repository import MovimientosRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class MovimientosService:

    def __init__(self, mov_repository: MovimientosRepository) -> None:
        self._repo = mov_repository

    async def create_mov(self, mov: MovimientosCreate) -> MovimientosResponse:
        """
        Create a new movimiento in the database.

        Args:
            mov (MovimientosCreate): The data for the movimiento to be created.

        Returns:
            MovimientosResponse: The created movimiento object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        # Create a new movimiento if it doesn't exist on database
        try:
            log.info(f"Intentando crear movimiento para transacción_id: {mov.transaccion_id}")
            new_movimiento = await self._repo.create(mov)
            log.info(f"Movimiento creado exitosamente con ID: {new_movimiento.id}")
            return new_movimiento
        except Exception as e:
            log.error(f"Error al crear movimiento: {e}")
            raise BasedException(
                message="Error inesperado al crear el movimiento.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def update_mov(self, mov_id: int, mov: MovimientosUpdate) -> Optional[MovimientosResponse]:
        """
        Update an existing movimiento in the database.

        Args:
            mov_id (int): The ID of the movimiento to update.
            mov (MovimientosUpdate): The updated movimiento data.

        Returns:
            Optional[MovimientosResponse]: The updated movimiento object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            updated_movimiento = await self._repo.update(mov_id, mov)
            return updated_movimiento
        except Exception as e:
            log.error(f"Error al actualizar movimiento con ID {mov_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar el movimiento.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete_mov(self, mov_id: int) -> bool:
        """
        Delete a movimiento from the database.

        Args:
            mov_id (int): The ID of the movimiento to delete.

        Returns:
            bool: True if the movimiento was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(mov_id)
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar movimiento con ID {mov_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar el movimiento.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_mov(self, mov_id: int) -> Optional[MovimientosResponse]:
        """
        Retrieve a movimiento by its ID.

        Args:
            mov_id (int): The ID of the movimiento to retrieve.

        Returns:
            Optional[MovimientosResponse]: The movimiento object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            movimiento = await self._repo.get_by_id(mov_id)
            return movimiento
        except Exception as e:
            log.error(f"Error al obtener movimiento con ID {mov_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener el movimiento.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_mov(self) -> List[MovimientosResponse]:
        """
        Retrieve all movimientos from the database.

        Returns:
            List[MovimientosResponse]: A list of all movimiento objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            movimientos = await self._repo.get_all()
            return movimientos
        except Exception as e:
            log.error(f"Error al obtener todos los movimientos: {e}")
            raise BasedException(
                message="Error inesperado al obtener los movimientos.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pag_movimientos(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[MovimientosResponse]:
        """
        Retrieve paginated movimientos, optionally filtered by transaction ID.

        Args:
            tran_id (Optional[int]): The ID of the transaction to filter by, if provided.
            params (Params): Pagination parameters.

        Returns:
            Page[MovimientosResponse]: A paginated list of movimiento objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            query = select(Movimientos)

            if tran_id is not None:
                query = query.where(Movimientos.transaccion_id == tran_id)

            return await self._repo.get_all_paginated(query=query, params=params)
        except Exception as e:
            log.error(f"Error al obtener movimientos paginados con tran_id {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener los movimientos paginados.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

from typing import List, Optional
from fastapi_pagination import Page, Params

from sqlalchemy import select
from starlette import status

from core.exceptions.base_exception import BasedException
from core.exceptions.db_exception import DatabaseSQLAlchemyException
from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
from database.models import Pesadas
from schemas.pesadas_schema import PesadaResponse, PesadaCreate, PesadaUpdate, VPesadasAcumResponse
from repositories.pesadas_repository import PesadasRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class PesadasService:

    def __init__(self, pesada_repository: PesadasRepository) -> None:
        self._repo = pesada_repository

    async def create_pesada(self, pesada_data: PesadaCreate) -> PesadaResponse:
        """
        Create a new pesada in the database.

        Args:
            pesada_data (PesadaCreate): The data for the pesada to be created.

        Returns:
            PesadaResponse: The created pesada object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            pesada_model = Pesadas(**pesada_data.model_dump())
            created_pesada = await self._repo.create(pesada_model)
            log.info(f"Pesada creada con referencia: {created_pesada.referencia}")
            return PesadaResponse.model_validate(created_pesada)
        except Exception as e:
            log.error(f"Error al crear pesada: {e}")
            raise BasedException(
                message="Error inesperado al crear la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def update_pesada(self, pesada_id: int, pesada: PesadaUpdate) -> Optional[PesadaResponse]:
        """
        Update an existing pesada in the database.

        Args:
            pesada_id (int): The ID of the pesada to update.
            pesada (PesadaUpdate): The updated pesada data.

        Returns:
            Optional[PesadaResponse]: The updated pesada object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            pesada_model = Pesadas(**pesada.model_dump())
            updated_pesada = await self._repo.update(pesada_id, pesada_model)
            log.info(f"Pesada actualizada con ID: {pesada_id}")
            return PesadaResponse.model_validate(updated_pesada) if updated_pesada else None
        except Exception as e:
            log.error(f"Error al actualizar pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def delete_pesada(self, pesada_id: int) -> bool:
        """
        Delete a pesada from the database.

        Args:
            pesada_id (int): The ID of the pesada to delete.

        Returns:
            bool: True if the pesada was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            deleted = await self._repo.delete(pesada_id)
            log.info(f"Pesada eliminada con ID: {pesada_id}")
            return deleted
        except Exception as e:
            log.error(f"Error al eliminar pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_pesada(self, pesada_id: int) -> Optional[PesadaResponse]:
        """
        Retrieve a pesada by its ID.

        Args:
            pesada_id (int): The ID of the pesada to retrieve.

        Returns:
            Optional[PesadaResponse]: The pesada object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            pesada = await self._repo.get_by_id(pesada_id)
            return PesadaResponse.model_validate(pesada) if pesada else None
        except Exception as e:
            log.error(f"Error al obtener pesada con ID {pesada_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la pesada.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pag_pesadas(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[PesadaResponse]:
        """
        Retrieve paginated pesadas, optionally filtered by transaction ID.

        Args:
            tran_id (Optional[int]): The ID of the transaction to filter by, if provided.
            params (Params): Pagination parameters.

        Returns:
            Page[PesadaResponse]: A paginated list of pesada objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            query = select(Pesadas)

            if tran_id is not None:
                query = query.where(Pesadas.transaccion_id == tran_id)

            return await self._repo.get_all_paginated(query=query, params=params)
        except Exception as e:
            log.error(f"Error al obtener pesadas paginadas con tran_id {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener las pesadas paginadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_pesadas(self) -> List[PesadaResponse]:
        """
        Retrieve all pesadas from the database.

        Returns:
            List[PesadaResponse]: A list of all pesada objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            pesadas = await self._repo.get_all()
            return [PesadaResponse.model_validate(p) for p in pesadas]
        except Exception as e:
            log.error(f"Error al obtener todas las pesadas: {e}")
            raise BasedException(
                message="Error inesperado al obtener las pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_pesada_if_not_exists(self, pesada_data: PesadaCreate) -> PesadaResponse:
        """
        Check if a pesada with the same transaction ID and consecutivo already exists. If not, create a new one.

        Args:
            pesada_data (PesadaCreate): The data for the pesada to be created.

        Returns:
            PesadaResponse: The existing or newly created pesada object.

        Raises:
            EntityAlreadyRegisteredException: If a pesada with the same transaction ID and consecutivo already exists.
            BasedException: For unexpected errors during the creation process.
        """
        try:
            # 1. Validar si transacción ya existe
            if await self._repo.find_one(transaccion_id=pesada_data.transaccion_id,
                                         consecutivo=pesada_data.consecutivo):
                raise EntityAlreadyRegisteredException(f"En la transacción {pesada_data.transaccion_id} ya existe una pesada con ese consecutivo '{pesada_data.consecutivo}'")

            # 2. Se crea transacción si esta no existe en la BD
            pesada_nueva = await self._repo.create(pesada_data)
            return pesada_nueva
        except EntityAlreadyRegisteredException as e:
            raise e
        except Exception as e:
            log.error(
                f"Error al crear pesada para transacción {pesada_data.transaccion_id} con consecutivo {pesada_data.consecutivo}: {e}")
            raise BasedException(
                message="Error inesperado al crear la pesada.",
                status_code=status.HTTP_409_CONFLICT
            )

    async def get_pesadas_acumuladas(self, puerto_id: Optional[str] = None, tran_id: Optional[int] = None) -> List[VPesadasAcumResponse]:
        """
        Retrieve the sum of pesadas related to a puerto_id.

        Args:
            puerto_id (str): The optional ID of the puerto to filter pesadas by.
            tran_id (int): The optional ID of the transaction to filter pesadas by.

        Returns:
            VPesadasAcumResponse: An object containing the accumulated pesada data.

        Raises:
            EntityNotFoundException: If no pesadas are found for the given puerto_id.
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            return await self._repo.get_sumatoria_pesadas(puerto_id, tran_id)
        except EntityNotFoundException as e:
            raise e
        except DatabaseSQLAlchemyException:
            raise
        except Exception as e:
            log.error(f"Error al obtener suma de pesadas para puerto_id {puerto_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la suma de pesadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
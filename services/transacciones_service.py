from datetime import datetime
from typing import List, Optional
from fastapi_pagination import Page, Params
from sqlalchemy import select
from starlette import status

from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
from database.models import Transacciones
from schemas.transacciones_schema import TransaccionResponse, TransaccionCreate, TransaccionUpdate
from repositories.transacciones_repository import TransaccionesRepository
from services.movimientos_service import MovimientosService
from services.pesadas_service import PesadasService

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class TransaccionesService:

    def __init__(self, tran_repository: TransaccionesRepository, pesadas_service : PesadasService, mov_service : MovimientosService) -> None:
        self._repo = tran_repository
        self.pesadas_service = pesadas_service
        self.mov_service = mov_service

    async def create_transaccion(self, tran: TransaccionCreate) -> TransaccionResponse:
        """
        Create a new transaction in the database.

        Args:
            tran (TransaccionCreate): The data for the transaction to be created.

        Returns:
            TransaccionResponse: The created transaction object.

        Raises:
            BasedException: For unexpected errors during the creation process.
        """
        try:
            return await self._repo.create(tran)
        except Exception as e:
            log.error(f"Error al crear transacción: {e}")
            raise BasedException(
                message="Error inesperado al crear la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def update_transaccion(self, tran_id: int, tran: TransaccionUpdate) -> Optional[TransaccionResponse]:
        """
        Update an existing transaction in the database.

        Args:
            tran_id (int): The ID of the transaction to update.
            tran (TransaccionUpdate): The updated transaction data.

        Returns:
            Optional[TransaccionResponse]: The updated transaction object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the update process.
        """
        try:
            return await self._repo.update(tran_id, tran)
        except Exception as e:
            log.error(f"Error al actualizar transacción con ID {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al actualizar la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def delete_transaccion(self, tran_id: int) -> bool:
        """
        Delete a transaction from the database.

        Args:
            tran_id (int): The ID of the transaction to delete.

        Returns:
            bool: True if the transaction was deleted, False otherwise.

        Raises:
            BasedException: For unexpected errors during the deletion process.
        """
        try:
            return await self._repo.delete(tran_id)
        except Exception as e:
            log.error(f"Error al eliminar transacción con ID {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al eliminar la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_transaccion(self, tran_id: int) -> Optional[TransaccionResponse]:
        """
        Retrieve a transaction by its ID.

        Args:
            tran_id (int): The ID of the transaction to retrieve.

        Returns:
            Optional[TransaccionResponse]: The transaction object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            return await self._repo.get_by_id(tran_id)
        except Exception as e:
            log.error(f"Error al obtener transacción con ID {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_tran_by_viaje(self, viaje: int) -> Optional[TransaccionResponse]:
        """
        Retrieve a transaction record by its viaje ID.

        Args:
            viaje (int): The ID of the voyage to retrieve.

        Returns:
            Optional[TransaccionResponse]: The transaction object, or None if not found.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            return await self._repo.find_one(viaje_id=viaje)
        except Exception as e:
            log.error(f"Error al obtener transacción con viaje {viaje}: {e}")
            raise BasedException(
                message="Error inesperado al obtener la transacción.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_all_transacciones(self) -> List[TransaccionResponse]:
        """
        Retrieve all transactions from the database.

        Returns:
            List[TransaccionResponse]: A list of all transaction objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            return await self._repo.get_all()
        except Exception as e:
            log.error(f"Error al obtener todas las transacciones: {e}")
            raise BasedException(
                message="Error inesperado al obtener las transacciones.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def get_pag_transacciones(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[TransaccionResponse]:
        """
        Retrieve paginated transactions, optionally filtered by transaction ID.

        Args:
            tran_id (Optional[int]): The ID of the transaction to filter by, if provided.
            params (Params): Pagination parameters.

        Returns:
            Page[TransaccionResponse]: A paginated list of transaction objects.

        Raises:
            BasedException: For unexpected errors during the retrieval process.
        """
        try:
            query = select(Transacciones)

            if tran_id is not None:
                query = query.where(Transacciones.id == tran_id)

            return await self._repo.get_all_paginated(query=query, params=params)
        except Exception as e:
            log.error(f"Error al obtener transacciones paginadas con tran_id {tran_id}: {e}")
            raise BasedException(
                message="Error inesperado al obtener las transacciones paginadas.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def create_transaccion_if_not_exists(self, tran_data: TransaccionCreate) -> TransaccionResponse:
        """
        Check if a transaction with the same Viaje ID already exists. If not, create a new one.

        Args:
            tran_data (TransaccionCreate): The data for the transaction to be created.

        Returns:
            TransaccionResponse: The existing or newly created transaction object.

        Raises:
            EntityAlreadyRegisteredException: If a transaction with the same Viaje ID already exists.
            BasedException: For unexpected errors during the creation process.
        """
        try:
            # 1. Validar si transacción ya existe
            if await self._repo.find_one(viaje_id=tran_data.viaje_id, estado='Proceso' ):
                raise EntityAlreadyRegisteredException(f"Ya existe transacción en proceso del viaje '{tran_data.viaje_id}'")

            # 2. Se crea transacción si esta no existe en la BD
            tran_nueva = await self._repo.create(tran_data)
            return tran_nueva
        except EntityAlreadyRegisteredException as e:
            raise e
        except Exception as e:
            log.error(f"Error al crear transacción para viaje_id {tran_data.viaje_id}: {e}")
            raise BasedException(
                message=f"Error inesperado al crear la transacción: {str(e)}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def transaccion_finalizar(self, tran_id: int) -> TransaccionResponse:
        """
        Updates the 'estado' of an active transaction to 'Finalizada' and creates a corresponding movement.

        Args:
            tran_id (int): The ID of the transaction to finalize.

        Returns:
            TransaccionResponse: The updated transaction object.

        Raises:
            EntityNotFoundException: If the transaction with the given ID is not found.
            BasedException: If the transaction is not in 'Activa' state or for unexpected errors.
        """
        try:
            # 1. Obtener la transacción y validar su estado
            tran = await self.get_transaccion(tran_id)
            if tran is None:
                raise EntityNotFoundException(f"La transacción con ID '{tran_id}' no fue encontrada.")

            if tran.estado != "Proceso":
                raise BasedException(
                    message=f"La transacción no se puede finalizar porque su estado es '{tran.estado}'. Solo las transacciones en estado 'Proceso' pueden finalizarse.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            # 2. Se obtiene sumatoria de pesadas para setear peso real
            pesada = await self.pesadas_service.get_pesada_acumulada(tran_id=tran.id)

            # 2. Se prepara los datos para actualizar la transacción

            update_fields = {
                "estado": "Finalizada",
                "fecha_fin": datetime.now(),
                "peso_real" : pesada.peso,
            }
            update_data = TransaccionUpdate(**update_fields)

            # 3. Se actualiza la transacción en la base de datos
            updated = await self._repo.update(tran_id, update_data)

            # #5. Se consulta saldo anterior
            #
            # # 5. Preparar y crear el movimiento asociado
            # movimiento_data = MovimientosCreate(
            #     transaccion_id= tran_id,
            #     almacenamiento_id=tran.origen_id,
            #     material_id=tran.material_id,
            #     tipo='Entrada',
            #     accion='Automático',
            #     peso=tran.peso,
            #     saldo_anterior=
            #     saldo_nuevo=
            #
            # )
            #
            #
            # new_movimiento = await self.movimiento_service.create_movimiento(movimiento_data)

            # 5. Retornar los resultados
            return updated
        except EntityNotFoundException as e:
            raise e
        except BasedException as e:
            raise e
        except Exception as e:
            log.error(f"Error al finalizar transacción con ID {tran_id}: {e}")
            raise BasedException(
                message=f"Error inesperado al finalizar la transacción : {e}",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )



from datetime import datetime
from typing import List, Optional
from fastapi_pagination import Page, Params
from sqlalchemy import select

from core.exceptions.entity_exceptions import EntityNotFoundException
from database.models import Transacciones
from schemas.movimientos_schema import MovimientosCreate, MovimientosResponse
from schemas.transacciones_schema import TransaccionResponse, TransaccionCreate, TransaccionUpdate
from repositories.transacciones_repository import TransaccionesRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class TransaccionesService:

    def __init__(self, tran_repository: TransaccionesRepository) -> None:
        self._repo = tran_repository


    async def create_transaccion(self, tran: TransaccionCreate) -> TransaccionResponse:
        return await self._repo.create(tran)

    async def update_transaccion(self, id: int, tran: TransaccionUpdate) -> Optional[TransaccionResponse]:
        return await self._repo.update(id, tran)

    async def delete_transaccion(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_transaccion(self, id: int) -> Optional[TransaccionResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_transacciones(self) -> List[TransaccionResponse]:
        return await self._repo.get_all()

    async def get_pag_transacciones(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[TransaccionResponse]:
        """
            Get one or more transacciones related to an id_transaccion (optional).
            Returns a page with filtered optionally transaction ID pesadas.
            """
        query = select(Transacciones)

        if tran_id is not None:
            query = query.where(Transacciones.id == tran_id)

        return await self._repo.get_all_paginated(query=query, params=params)

    async def create_transaccion_if_not_exists(self, tran_data: TransaccionCreate) -> tuple[TransaccionResponse, bool]:
        """
               Check if a Transacción with same Viaje ID already exists. If not, create a new one.

               Args:
                   tran_data: The data set in the schema of Transacción object.

               Returns:
                   A tuple with the existing or newly created Transacción and a boolean (True if it was created, False if it already existed).
           """
        try:
            # Intentar encontrar una transacción existente por el id de referencia de un viaje
            tran_existente = await self._repo.find_one(
                viaje_id=tran_data.viaje_id
            )

            if tran_existente:
                log.info(f"Transacción ya existente con ID: {tran_existente.id}, "
                         f"Viaje ID: {tran_existente.viaje_id}")
                return tran_existente, False
            else:
                tran_nueva = await self._repo.create(tran_data)
                log.info(f"Se creó nueva transacción con ID: {tran_nueva.id}, "
                         f"Viaje ID: {tran_nueva.viaje_id}")
                return tran_nueva, True
        except Exception as e:
            log.error(f"Error al crear transacción "
                      f"Viaje ID: {tran_data.viaje_id} - {e}")
            raise

    # async def transaccion_finalizar(self, tran_id: int) -> tuple[TransaccionResponse, MovimientosResponse]:
    #     """
    #                   Updates the current 'estado' for an active Transaction.
    #
    #                   This method updates the 'estado' value of a Transaction in the database.
    #                   Also creates the corresponding 'movimiento' of the transaction.
    #
    #                   Args:
    #                       tran_id: The transaction register whose 'estado' will change.
    #
    #                   Returns:
    #                       The transaction object after it have been finished.
    #
    #                   Raises:
    #                       Exception: If an error occurs during the operation.
    #     """
    #     async with self._repo.db.begin():  # Inicia una transacción de base de datos
    #
    #         # 1. Obtener la transacción y validar su estado
    #         existing_transaccion = await self._repo.get_by_id(tran_id)
    #         if not existing_transaccion:
    #             log.warning(f"Finalizar Transacción Fallida: Transacción {tran_id} no encontrada.")
    #             raise BaseException(f"La transacción con ID '{tran_id}' no fue encontrada.")
    #
    #         if existing_transaccion.estado != "Activa":
    #             log.warning(
    #                 f"Finalizar Transacción Fallida: Transacción {tran_id} no está en estado 'Activa' (estado actual: {existing_transaccion.estado}).")
    #             raise BaseException(
    #                 f"La transacción no pudo finalizar porque su estado actual es '{existing_transaccion.estado}'. Solo las transacciones 'Activa' pueden finalizarse.")
    #
    #         log.info(f"Transacción {tran_id} validada como 'Activa'. Procediendo a finalizar.")
    #
    #         # 2. Se prepara los datos para actualizar la transacción
    #         transaccion_update_data = TransaccionUpdate(
    #             estado="Finalizada",
    #             fecha_fin=datetime.now()
    #         )
    #
    #         # 3. Se actualiza la transacción en la base de datos
    #         updated_transaccion = await self._repo.update(
    #             tran_id,
    #             transaccion_update_data
    #         )
    #
    #         # Verificación de seguridad, aunque si get_by_id encontró, update debería funcionar
    #         if not updated_transaccion:
    #             log.error(f"Fallo inesperado al actualizar la transacción {tran_id} a 'Finalizada'.")
    #             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #                                 detail="Error interno al actualizar la transacción.")
    #
    #         log.info(f"Transacción {transaccion_id} actualizada a 'Finalizada'.")
    #
    #         # 4. Preparar y crear el movimiento asociado
    #         movimiento_data.transaccion_id = transaccion_id
    #
    #
    #         new_movimiento = await self.movimiento_service.create_movimiento(movimiento_data)
    #         log.info(f"Movimiento creado exitosamente para transacción {transaccion_id} con ID: {new_movimiento.id}.")
    #
    #         # 5. Retornar los resultados
    #         return updated_transaccion, new_movimiento
    #

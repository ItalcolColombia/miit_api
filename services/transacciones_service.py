from datetime import datetime
from typing import List, Optional
from fastapi_pagination import Page, Params
from sqlalchemy import select

from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
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

    async def create_transaccion_if_not_exists(self, tran_data: TransaccionCreate) -> TransaccionResponse:
        """
               Check if a Transacción with same Viaje ID already exists. If not, create a new one.

               Args:
                   tran_data: The data set in the schema of Transacción object.

               Returns:
                   An existing or newly created Transacción.
           """
        # 1. Validar si transacción ya existe
        if await self._repo.find_one(viaje_id=tran_data.viaje_id):
            raise EntityAlreadyRegisteredException(f"Ya existe una transacción del viaje '{tran_data.viaje_id}'")

        # 2. Se crea transacción si esta no existe en la BD
        tran_nueva = await self._repo.create(tran_data)
        return tran_nueva

    async def transaccion_finalizar(self, tran_id: int) -> TransaccionResponse:
        """
              Updates the current 'estado' for an active Transaction.

              This method updates the 'estado' value of a Transaction in the database.
              Also creates the corresponding 'movimiento' of the transaction.

              Args:
                  tran_id: The transaction register whose 'estado' will change.

              Returns:
                  The transaction object after it have been finished.

              Raises:
                  Exception: If an error occurs during the operation.
        """
        # 1. Obtener la transacción y validar su estado

        tran = await self._repo.get_by_id(tran_id)
        if tran is None:
            raise EntityNotFoundException(f"La transacción con ID '{tran_id}' no fue encontrada.")

        if tran.estado != "Activa":
            raise BaseException(f"La transacción no pudo finalizar porque su estado es '{tran.estado}'. Solo las transacciones 'Activa' pueden finalizarse.")

        # 2. Se prepara los datos para actualizar la transacción
        transaccion_update_data = TransaccionUpdate(estado="Finalizada", fecha_fin=datetime.now())

        # 3. Se actualiza la transacción en la base de datos
        updated_transaccion = await self._repo.update(
            tran_id,
            transaccion_update_data
        )

        # # 4. Verificación de update
        # if not updated_transaccion:
        #     raise BaseException(f"Error al actualizar la transacción")
        #
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
        return updated_transaccion


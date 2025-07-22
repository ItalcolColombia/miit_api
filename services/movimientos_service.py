from typing import List, Optional
from fastapi_pagination import Page, Params
from sqlalchemy import select
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
            Create a new movimiento if it doesn't exist on database
           """
        log.info(f"Intentando crear movimiento para transacción_id: {mov.transaccion_id}")
        try:
            new_movimiento = await self._repo.create(mov)
            log.info(f"Movimiento creado exitosamente con ID: {new_movimiento.id}")
            return new_movimiento
        except Exception as e:
            log.error(f"Error al crear movimiento: {e}")
            raise

    async def update_mov(self, id: int, mov: MovimientosUpdate) -> Optional[MovimientosResponse]:
        return await self._repo.update(id, mov)

    async def delete_mov(self, id: int) -> bool:
        return await self._repo.delete(id)

    async def get_mov(self, id: int) -> Optional[MovimientosResponse]:
        return await self._repo.get_by_id(id)

    async def get_all_mov(self) -> List[MovimientosResponse]:
        return await self._repo.get_all()

    async def get_pag_movimientos(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[MovimientosResponse]:
        """
             Get one or more movimientos related to an id_transaccion (optional).
             Returns a page with filtered optionally transaction ID pesadas.
             """
        query = select(Movimientos)

        if tran_id is not None:
            query = query.where(Movimientos.transaccion_id == tran_id)

        return await self._repo.get_all_paginated(query=query, params=params)

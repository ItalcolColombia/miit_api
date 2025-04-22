from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repositories.base_repository import IRepository
from schemas.movimientos_schema import MovimientosResponse, MovimientosCreate, MovimientosUpdate
from database.models import Movimientos  # Import your Material model

class MovimientosRepository(IRepository[Movimientos, MovimientosResponse]):
    db: AsyncSession

    def __init__(self, model: type[Movimientos], schema: type[MovimientosResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)


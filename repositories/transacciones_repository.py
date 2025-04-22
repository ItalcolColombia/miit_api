from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repositories.base_repository import IRepository
from schemas.transacciones_schema import TransaccionResponse, TransaccionCreate, TransaccionUpdate
from database.models import Transacciones

class TransaccionesRepository(IRepository[Transacciones, TransaccionResponse]):
    db: AsyncSession

    def __init__(self, model: type[Transacciones], schema: type[TransaccionResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)



from sqlalchemy.ext.asyncio import AsyncSession
from core.contracts.auditor import Auditor
from repositories.base_repository import IRepository
from schemas.transacciones_schema import TransaccionResponse
from database.models import Transacciones

class TransaccionesRepository(IRepository[Transacciones, TransaccionResponse]):
    db: AsyncSession

    def __init__(self, model: type[Transacciones], schema: type[TransaccionResponse], db: AsyncSession, auditor:Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)



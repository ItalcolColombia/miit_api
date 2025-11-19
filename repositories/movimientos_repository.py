from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import Movimientos
from repositories.base_repository import IRepository
from schemas.movimientos_schema import MovimientosResponse


class MovimientosRepository(IRepository[Movimientos, MovimientosResponse]):
    db: AsyncSession

    def __init__(self, model: type[Movimientos], schema: type[MovimientosResponse], db: AsyncSession, auditor:Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)



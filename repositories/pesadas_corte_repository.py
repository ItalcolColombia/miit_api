from sqlalchemy.ext.asyncio import AsyncSession
from core.contracts.auditor import Auditor
from repositories.base_repository import IRepository
from schemas.pesadas_corte_schema import PesadasCorteResponse
from database.models import PesadasCorte


class PesadasCorteRepository(IRepository[PesadasCorte, PesadasCorteResponse]):
    db: AsyncSession

    def __init__(self, model: type[PesadasCorte], schema: type[PesadasCorteResponse], db: AsyncSession, auditor:Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)



from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import Ajustes
from repositories.base_repository import IRepository
from schemas.ajustes_schema import AjusteResponse


class AjustesRepository(IRepository[Ajustes, AjusteResponse]):
    db: AsyncSession

    def __init__(self, model: type[Ajustes], schema: type[AjusteResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)


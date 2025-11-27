from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import Flotas
from repositories.base_repository import IRepository
from schemas.flotas_schema import FlotasResponse


class FlotasRepository(IRepository[Flotas, FlotasResponse]):
    db: AsyncSession

    def __init__(self, model: type[Flotas], schema: type[FlotasResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def get_flota_by_ref(self, ref: str) -> Optional[Flotas]:
        stmt = select(self.model).filter(self.model.referencia == ref)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
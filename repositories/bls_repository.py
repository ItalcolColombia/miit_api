from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.contracts.auditor import Auditor
from repositories.base_repository import IRepository
from schemas.bls_schema import BlsResponse
from database.models import Bls

class BlsRepository(IRepository[Bls, BlsResponse]):
    db: AsyncSession


    def __init__(self, model: type[Bls], schema: type[BlsResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)


    async def get_bls_no_bl(self, ref: str) -> Optional[Bls]:
        stmt = select(self.model).filter(self.model.no_bl == ref)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
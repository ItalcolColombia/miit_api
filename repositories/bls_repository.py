from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import Bls
from repositories.base_repository import IRepository
from schemas.bls_schema import BlsResponse


class BlsRepository(IRepository[Bls, BlsResponse]):
    db: AsyncSession


    def __init__(self, model: type[Bls], schema: type[BlsResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)


    async def get_bls_viaje(self, ref: int) -> List[BlsResponse] | None:
        query = (
            select(Bls)
            .where(Bls.viaje_id == ref)
        )
        result = await self.db.execute(query)
        return result.scalars().all()


from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound

from core.exceptions.entity_exceptions import EntityNotFoundException
from repositories.base_repository import IRepository
from schemas.bls_schema import BlsResponse, BlsCreate
from database.models import Bls

class BlsRepository(IRepository[Bls, BlsResponse]):
    db: AsyncSession


    def __init__(self, model: type[Bls], schema: type[BlsResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)


    async def get_bls_no_bl(self, ref: str) -> Optional[Bls]:
        stmt = select(self.model).filter(self.model.no_bl == ref)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
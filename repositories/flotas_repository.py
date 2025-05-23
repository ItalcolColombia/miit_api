from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound

from core.exceptions.entity_exceptions import EntityNotFoundException
from repositories.base_repository import IRepository
from schemas.flotas_schema import FlotasResponse, FlotaCreate, FlotaUpdate
from database.models import Flotas


class FlotasRepository(IRepository[Flotas, FlotasResponse]):
    db: AsyncSession

    def __init__(self, model: type[Flotas], schema: type[FlotasResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)

    async def get_flota_by_ref(self, ref: str) -> Optional[Flotas]:
        stmt = select(self.model).filter(self.model.referencia == ref)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
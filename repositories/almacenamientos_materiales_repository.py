from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repositories.base_repository import IRepository
from schemas.almacenamientos_materiales_schema import AlmacenamientoMaterialesResponse
from database.models import AlmacenamientosMateriales


class AlmacenamientosMaterialesRepository(IRepository[AlmacenamientosMateriales, AlmacenamientoMaterialesResponse]):
    db: AsyncSession

    def __init__(self, model: type[AlmacenamientosMateriales], schema: type[AlmacenamientoMaterialesResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)


from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import AlmacenamientosMateriales
from repositories.base_repository import IRepository
from schemas.almacenamientos_materiales_schema import AlmacenamientoMaterialesResponse


class AlmacenamientosMaterialesRepository(IRepository[AlmacenamientosMateriales, AlmacenamientoMaterialesResponse]):
    db: AsyncSession

    def __init__(self, model: type[AlmacenamientosMateriales], schema: type[AlmacenamientoMaterialesResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)


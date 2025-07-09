
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.base_repository import IRepository
from schemas.pesadas_schema import PesadaResponse
from database.models import Pesadas

class PesadasRepository(IRepository[Pesadas, PesadaResponse]):
    db: AsyncSession

    def __init__(self, model: type[Pesadas], schema: type[PesadaResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)


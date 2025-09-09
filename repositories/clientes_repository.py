from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.contracts.auditor import Auditor
from repositories.base_repository import IRepository
from schemas.clientes_schema import ClientesResponse
from database.models import Clientes

class ClientesRepository(IRepository[Clientes, ClientesResponse]):
    db: AsyncSession

    def __init__(self, model: type[Clientes], schema: type[ClientesResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def get_cliente_by_name(self, ref: str) -> Optional[Clientes]:
        stmt = select(self.model).filter(self.model.razon_social == ref)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()



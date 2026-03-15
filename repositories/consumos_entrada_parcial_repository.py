from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import ConsumosEntradaParcial
from repositories.base_repository import IRepository
from schemas.consumos_entrada_parcial_schema import ConsumosEntradaParcialResponse


class ConsumosEntradaParcialRepository(IRepository[ConsumosEntradaParcial, ConsumosEntradaParcialResponse]):
    db: AsyncSession

    def __init__(self, model: type[ConsumosEntradaParcial], schema: type[ConsumosEntradaParcialResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def get_max_consecutivo_by_puerto_id(self, puerto_id: str) -> int:
        """
        Retorna el máximo consecutivo para un puerto_id, o 0 si no hay registros.
        """
        query = select(func.coalesce(func.max(ConsumosEntradaParcial.consecutivo), 0)).where(
            ConsumosEntradaParcial.puerto_id == puerto_id
        )
        result = await self.db.execute(query)
        return int(result.scalar_one())

    async def get_by_puerto_id(self, puerto_id: str):
        """
        Retorna todos los consumos de un viaje ordenados por consecutivo y BL.
        """
        query = (
            select(ConsumosEntradaParcial)
            .where(ConsumosEntradaParcial.puerto_id == puerto_id)
            .order_by(ConsumosEntradaParcial.consecutivo, ConsumosEntradaParcial.no_bl)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

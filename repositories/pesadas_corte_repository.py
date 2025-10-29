from sqlalchemy.ext.asyncio import AsyncSession
from core.contracts.auditor import Auditor
from repositories.base_repository import IRepository
from schemas.pesadas_corte_schema import PesadasCorteResponse
from database.models import PesadasCorte


class PesadasCorteRepository(IRepository[PesadasCorte, PesadasCorteResponse]):
    db: AsyncSession

    def __init__(self, model: type[PesadasCorte], schema: type[PesadasCorteResponse], db: AsyncSession, auditor:Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def get_last_pesada_corte_for_transaccion(self, tran_id: int):
        """
        Obtener la última pesada_corte para una transacción ordenando por fecha_hora desc.
        Retorna el registro como instancia del schema (model attributes preserved) o None.
        """
        from sqlalchemy import select
        query = select(PesadasCorte).where(PesadasCorte.transaccion == tran_id).order_by(PesadasCorte.fecha_hora.desc()).limit(1)
        result = await self.db.execute(query)
        pesada_corte = result.scalars().first()
        return pesada_corte

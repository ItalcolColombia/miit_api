from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repositories.base_repository import IRepository
from schemas.pesadas_schema import PesadaResponse, PesadaCreate, PesadaUpdate
from database.models import Pesadas

class PesadasRepository(IRepository[Pesadas, PesadaResponse]):
    db: AsyncSession

    def __init__(self, model: type[Pesadas], schema: type[PesadaResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)


    async def get_pesada_by_transaccion(self, tran_id: int) -> Optional[int]:
            """
            Get all 'Pesadas' entries filtered by transaction ID.

            Args:
                tran_id (int): The transaction ID to filter by.

            Returns:
                List[Pesadas]: A list of Pesadas instances matching the transaction ID.
            """
            result = await self.db.execute(
                select(Pesadas).where(Pesadas.transaccion_id == tran_id)
            )
            pesadas_list = result.scalars().all()
            return pesadas_list
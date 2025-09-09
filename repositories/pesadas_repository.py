from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from core.contracts.auditor import Auditor
from repositories.base_repository import IRepository
from schemas.pesadas_schema import PesadaResponse, VPesadasAcumResponse
from database.models import Pesadas, VPesadasAcumulado


class PesadasRepository(IRepository[Pesadas, PesadaResponse]):
    db: AsyncSession

    def __init__(self, model: type[Pesadas], schema: type[PesadaResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)


    async def get_sumatoria_pesadas(self, puerto_ref: Optional[str] = None, tran_id: Optional[int] = None) -> VPesadasAcumResponse | None:
        """
                Filter pesada sum

                Returns:
                    A sum of Pesadas register matching the filter, otherwise, returns a null.
                """

        query = select(VPesadasAcumulado)

        if puerto_ref is not None:
            query = query.where(VPesadasAcumulado.puerto_id == puerto_ref)

        if tran_id is not None:
            query = query.where(VPesadasAcumulado.transaccion == tran_id)

        result = await self.db.execute(query)
        pesada = result.scalars().all()

        if not pesada:
            return None

        return VPesadasAcumResponse.model_validate(pesada[0])


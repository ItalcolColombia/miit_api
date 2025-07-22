from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from repositories.base_repository import IRepository
from schemas.pesadas_schema import PesadaResponse, VPesadasAcumResponse
from database.models import Pesadas, VPesadasAcumulado


class PesadasRepository(IRepository[Pesadas, PesadaResponse]):
    db: AsyncSession

    def __init__(self, model: type[Pesadas], schema: type[PesadaResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)


    async def get_sumatoria_pesadas(self, puerto_ref: str) -> VPesadasAcumResponse | None:
        """
                Filter pesada sum

                Returns:
                    A sum of Pesadas register matching the filter, otherwise, returns a null.
                """
        query = (
            select(VPesadasAcumulado)
            .where(VPesadasAcumulado.puerto_id == puerto_ref)
        )
        result = await self.db.execute(query)
        pesada = result.scalars().all()

        if not pesada:
            return None

        return VPesadasAcumResponse.model_validate(pesada[0])


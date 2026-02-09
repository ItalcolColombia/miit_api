from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import Bls
from repositories.base_repository import IRepository
from schemas.bls_schema import BlsResponse


class BlsRepository(IRepository[Bls, BlsResponse]):
    db: AsyncSession


    def __init__(self, model: type[Bls], schema: type[BlsResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)


    async def get_bls_viaje(self, ref: int) -> List[BlsResponse] | None:
        query = (
            select(Bls)
            .where(Bls.viaje_id == ref)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_bl_activo_por_material(self, viaje_id: int, material_id: int) -> Optional[Bls]:
        """
        Busca el BL activo (estado_puerto=True) para un viaje y material específico.
        Si hay más de uno, retorna el último por fecha_hora.

        Args:
            viaje_id: ID del viaje de recibo (buque)
            material_id: ID del material

        Returns:
            El BL encontrado o None si no existe
        """
        query = (
            select(Bls)
            .where(Bls.viaje_id == viaje_id)
            .where(Bls.material_id == material_id)
            .where(Bls.estado_puerto == True)
            .order_by(Bls.fecha_hora.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


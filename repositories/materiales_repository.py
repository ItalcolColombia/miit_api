from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from repositories.base_repository import IRepository
from schemas.materiales_schema import MaterialesResponse, MaterialesCreate, MaterialesUpdate
from database.models import Materiales  # Import your Material model

class MaterialesRepository(IRepository[Materiales, MaterialesResponse]):
    db: AsyncSession

    def __init__(self, model: type[Materiales], schema: type[MaterialesResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)

    async def get_material_id_by_name(self, material_name: str) -> Optional[int]:
        """
                        Find a Material by 'id'

                        Args:
                            material_name: The material name param to filter.

                        Returns:
                            An integer of the material id column.
                        """
        result = await self.db.execute(
            select(Materiales.id).where(Materiales.nombre == material_name)
        )
        material_id = result.scalar_one_or_none()
        return material_id
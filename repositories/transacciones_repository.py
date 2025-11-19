from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import Transacciones
from repositories.base_repository import IRepository
from schemas.transacciones_schema import TransaccionResponse


class TransaccionesRepository(IRepository[Transacciones, TransaccionResponse]):
    db: AsyncSession

    def __init__(self, model: type[Transacciones], schema: type[TransaccionResponse], db: AsyncSession, auditor:Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def find_one_ordered(self, order_by: str = 'fecha_hora', desc: bool = True, **kwargs) -> Optional[TransaccionResponse]:
        """
        Find a single Transacciones record matching filters, ordered by given column (defaults to fecha_hora desc).
        Returns the first row or None.
        """
        from sqlalchemy import select
        try:
            query = select(self.model)
            for attribute_name, attribute_value in kwargs.items():
                # Only apply filter if attribute exists on model
                if hasattr(self.model, attribute_name):
                    attribute = getattr(self.model, attribute_name)
                    query = query.where(attribute == attribute_value)

            if hasattr(self.model, order_by):
                col = getattr(self.model, order_by)
                query = query.order_by(col.desc() if desc else col)

            query = query.limit(1)
            result = await self.db.execute(query)
            item = result.scalars().first()
            return self.schema.model_validate(item) if item else None
        except AttributeError as e:
            raise ValueError(f"Invalid attribute in filter or order_by: {e}")
        except Exception:
            raise

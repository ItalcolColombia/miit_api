from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page
from repositories.base_repository import IRepository
from schemas.movimientos_schema import MovimientosResponse, MovimientosCreate, MovimientosUpdate
from database.models import Movimientos  # Import your Material model

class MovimientosRepository(IRepository[Movimientos, MovimientosResponse]):
    db: AsyncSession

    def __init__(self, model: type[Movimientos], schema: type[MovimientosResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)


    async def get_movimientos_paginados(self, transaccion_id: Optional[int] = None) -> Page[MovimientosResponse]:
        """
                Retrieve paginated movimientos

                Returns:
                    A page of movimientos objects.
                """
        query = select(Movimientos)

        # Si se proporciona un movimiento_id, aplicamos el filtro.
        if transaccion_id is not None:
            query = query.where(Movimientos.transaccion_id == transaccion_id)

        paginated_result = await paginate(self.db, query)

        paginated_result.items = [MovimientosResponse.model_validate(item) for item in paginated_result.items]

        return paginated_result





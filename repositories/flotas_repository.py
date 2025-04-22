from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from repositories.base_repository import IRepository
from schemas.flotas_schema import FlotasResponse, FlotaCreate, FlotaUpdate, FlotasActResponse
from database.models import Flotas, Buques, VFlotas

class FlotasRepository(IRepository[Flotas, FlotasResponse]):
    db: AsyncSession

    def __init__(self, model: type[Flotas], schema: type[FlotasResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)

    async def get_buques_activos(self) -> List[FlotasActResponse]:
        """
                Filters flotas by 'tipo' = buque and 'estado = True

                Args:
                    tipo: The value to filter the 'tipo' column by (e.g., 'Buque').
                    estado: The value to filter the 'estado' column by (e.g., True).

                Returns:
                    A list of Buques objects matching the filter.
                """
        query = (
            select(VFlotas)
            .where(VFlotas.tipo == 'buque')
            .where(VFlotas.estado == True)
        )
        result = await self.db.execute(query)
        flotas = result.scalars().all()

        if not flotas:
            return None

        return [FlotasActResponse.model_validate(flota) for flota in flotas]

    async def get_camiones_activos(self) -> List[FlotasActResponse]:
        """
                Filters flotas by 'tipo' = camion and 'estado = True

                Args:
                    tipo: The value to filter the 'tipo' column by (e.g., 'Buque').
                    estado: The value to filter the 'estado' column by (e.g., True).

                Returns:
                    A list of Buques objects matching the filter.
                """
        query = (
            select(VFlotas)
            .where(VFlotas.tipo == 'camion')
        )
        result = await self.db.execute(query)
        flotas = result.scalars().all()

        if not flotas:
            return None

        return [FlotasActResponse.model_validate(flota) for flota in flotas]

    async def create_flota_by_integrador(self, flota_create: FlotaCreate) -> FlotasResponse:
        db_obj = Flotas(**flota_create.model_dump())
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return self.schema.model_validate(db_obj)
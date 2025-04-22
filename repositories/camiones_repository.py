from imaplib import Flags
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound

from core.exceptions.entity_exceptions import EntityNotFoundException
from repositories.base_repository import IRepository
from schemas.camiones_schema import CamionResponse, CamionCreate, CamionUpdate
from database.models import Camiones

class CamionesRepository(IRepository[Camiones, CamionResponse]):
    db: AsyncSession

    def __init__(self, model: type[Camiones], schema: type[CamionResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)

    async def get_camion_by_plate(self, plate: str) -> Optional[CamionResponse]:
        """
                        Find a Camion by 'placa'

                        Args:
                            placa: The truck plate param to filter.

                        Returns:
                            An Camion object based on their placa value.
                        """
        try:
            result = await self.db.execute(select(self.model).filter(self.model.placa == plate))
            camion = result.scalar_one()
            return self.schema.model_validate(camion)
        except NoResultFound:
            return None

    async def create_camion_if_not_exists(self, plate: str, points: int) -> CamionResponse:
        """
                            Check if a Camion already exists. If not, create a new Camion.

                            Args:
                                plate: The truck plate of camion object.
                                points: The number of points of camion object.
                                direct: Boolean which informs if the truck will be attended as despacho directo.

                            Returns:
                                The existing or newly created camion
                            """
        existing_camion = await self.get_camion_by_plate(plate)
        if existing_camion:
            return existing_camion
        else:
            new_camion = CamionCreate(
                placa=plate,
                puntos=points,
            )
            print(type(new_camion))
            return await self.create(new_camion)

    async def update_camion(self, truck: Camiones, points: int) -> CamionResponse:
        update_data = CamionUpdate(puntos=points)
        return await self.update(truck.id, update_data)

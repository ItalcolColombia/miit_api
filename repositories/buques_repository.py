from imaplib import Flags
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound

from core.exceptions.entity_exceptions import EntityNotFoundException
from repositories.base_repository import IRepository
from schemas.buques_schema import BuquesResponse, BuqueCreate, BuqueUpdate
from database.models import Buques

class BuquesRepository(IRepository[Buques, BuquesResponse]):
    db: AsyncSession

    def __init__(self, model: type[Buques], schema: type[BuquesResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)

    async def get_buque_by_name(self, name: str) -> Optional[BuquesResponse]:
        """
                        Find a Buque by 'name'

                        Args:
                            name: The buque name param to filter.

                        Returns:
                            An Buque object based on their name value.
                        """
        try:
            result = await self.db.execute(select(self.model).filter(self.model.nombre == name))
            buque = result.scalar_one()
            return self.schema.model_validate(buque)
        except NoResultFound:
            return None

    async def create_buque_if_not_exists(self, nombre: str) -> BuquesResponse:
        """
                            Check if a Buque already exists. If not, create a new Buque.

                            Args:
                                buque_create: The buque object.

                            Returns:
                                The existing or newly created buque
                            """
        existing_buque = await self.get_buque_by_name(nombre)
        if existing_buque:
            return existing_buque
        else:
            new_buque = BuqueCreate(
                nombre=nombre,
                estado=False  # You might want to set a default value or get this from somewhere
            )
            print(type(new_buque))
            return await self.create(new_buque)

    async def update_buque_estado(self, buque: Buques, estado: bool) -> BuquesResponse:
        # Update the state using the generic update method
        update_data = BuqueUpdate(estado=estado)  # Assuming you have a BuqueUpdate schema
        return await self.update(buque.id, update_data)

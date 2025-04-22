from imaplib import Flags
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.exc import NoResultFound

from core.exceptions.entity_exceptions import EntityNotFoundException
from repositories.base_repository import IRepository
from schemas.bls_schema import BlsResponse, BlsCreate
from database.models import BLS

class BlsRepository(IRepository[BLS, BlsCreate]):
    db: AsyncSession

    def __init__(self, model: type[BLS], schema: type[BlsResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)

    async def get_buque_by_name(self, name: str) -> Optional[BlsResponse]:
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

    # async def create_bl_if_not_exits(self, nombre: str) -> BlsResponse:
    #     """
    #                         Check if a Buque already exists. If not, create a new Buque.
    #
    #                         Args:
    #                             buque_create: The buque object.
    #
    #                         Returns:
    #                             The existing or newly created buque
    #                         """
    #     existing_buque = await self.get_buque_by_name(nombre)
    #     if existing_buque:
    #         return existing_buque
    #     else:
    #         # Create a Buques object
    #         new_buque = Buques(
    #             nombre=nombre,
    #             estado=False  # You might want to set a default value or get this from somewhere
    #         )
    #         return await self.create(new_buque)

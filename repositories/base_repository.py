from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, TypeVar, Generic, List
from pydantic import BaseModel
from sqlalchemy.future import select
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page, Params
from sqlalchemy.exc import NoResultFound
from core.exceptions.entity_exceptions import EntityNotFoundException
from utils.any_utils import AnyUtils

ModelType = TypeVar("ModelType")
SchemaType = TypeVar("SchemaType")

class IRepository(Generic[ModelType, SchemaType]):
    def __init__(self, model: type[ModelType], schema: type[SchemaType], db: AsyncSession) -> None:
        self.model = model
        self.schema = schema
        self.db = db

    async def get_all(self) -> List[SchemaType]:
        query = select(self.model)
        result = await self.db.execute(query)
        items = result.scalars().all()
        return [self.schema.model_validate(item) for item in items]

    async def get_all_paginated(self, query=None, params: Params = Params()) -> Page[SchemaType]:
        """
        Get paginated result based on query (optional)
        if query is not supplied, then return all items paginated.
        """
        if query is None:
            query = select(self.model)

        paginated_result = await paginate(self.db, query, params)

        paginated_result.items = [self.schema.model_validate(item) for item in paginated_result.items]

        return paginated_result



    
    async def find_many(self, **kwargs) -> List[SchemaType]:
        try:
            query = select(self.model)
            for attribute_name, attribute_value in kwargs.items():
                attribute = getattr(self.model, attribute_name)
                query = query.filter(attribute == attribute_value)
            result = await self.db.execute(query)
            items = result.scalars().all()
            return [self.schema.model_validate(item) for item in items]
        except AttributeError as e:
            raise ValueError(f"Invalid attribute in filter: {e}")

    async def get_by_id(self, id: int) -> Optional[SchemaType]:
        try:
            result = await self.db.execute(select(self.model).filter(self.model.id == id))
            item = result.scalar_one()
            return self.schema.model_validate(item)
        except NoResultFound:
            return None
        
    async def find_one(self, **kwargs) -> Optional[SchemaType]:
        try:
            query = select(self.model)
            for attribute_name, attribute_value in kwargs.items():
                attribute = getattr(self.model, attribute_name)
                query = query.filter(attribute == attribute_value)
            result = await self.db.execute(query)
            item = result.scalar_one()
            return self.schema.model_validate(item)
        except NoResultFound:
            return None
        except AttributeError as e:
            raise ValueError(f"Invalid attribute in filter: {e}")

    async def create(self, obj: BaseModel) -> BaseModel:
        # Asynchronously adding and committing a new object to the DB
        db_obj = self.model(**obj.model_dump())  # Assuming obj is a BaseModel with `model_dump`
        self.db.add(db_obj)
        await self.db.commit()  # Commit transaction
        await self.db.refresh(db_obj)  # Refresh object state after commit
        return self.schema.model_validate(db_obj)

    async def count(self) -> int:
        query = select(func.count()).select_from(self.model)
        result = await self.db.execute(query)
        return result.scalar()

    async def update(self, id: int, obj: BaseModel) -> BaseModel:
        try:
            # Fetch the object to update asynchronously
            result = await self.db.execute(select(self.model).filter(self.model.id == id))
            db_obj = result.scalar_one()

            # Update fields
            for key, value in obj.model_dump(exclude_unset=True).items():
                if key == 'clave' and value:
                    value = AnyUtils.generate_password_hash(value)
                setattr(db_obj, key, value)

            await self.db.commit()  # Commit changes
            await self.db.refresh(db_obj)  # Refresh object state
            return self.schema.model_validate(db_obj)
        except NoResultFound:
            raise EntityNotFoundException(self.model.__name__, id)

    async def delete(self, id: int) -> bool:
        try:
            # Fetch and delete the object asynchronously
            result = await self.db.execute(select(self.model).filter(self.model.id == id))
            db_obj = result.scalar_one()
            await self.db.delete(db_obj)
            await self.db.commit()  # Commit the deletion
            return True
        except NoResultFound:
            raise EntityNotFoundException(self.model.__name__, id)
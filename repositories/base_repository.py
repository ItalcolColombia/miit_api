from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, TypeVar, Generic, List
from pydantic import BaseModel
from sqlalchemy.future import select
from fastapi_pagination.ext.sqlalchemy import paginate
from fastapi_pagination import Page, Params
from sqlalchemy.exc import NoResultFound
from core.contracts.auditor import Auditor
from core.exceptions.entity_exceptions import EntityNotFoundException
from core.config.context import current_user_id
from schemas.logs_auditoria_schema import LogsAuditoriaCreate
from utils.any_utils import AnyUtils

ModelType = TypeVar("ModelType")
SchemaType = TypeVar("SchemaType")

class IRepository(Generic[ModelType, SchemaType]):
    def __init__(self, model: type[ModelType], schema: type[SchemaType], db: AsyncSession, auditor: Auditor) -> None:
        self.model = model
        self.schema = schema
        self.db = db
        self.auditor = auditor

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
        try:
            if query is None:
                query = select(self.model)

            paginated_result = await paginate(self.db, query, params)
            paginated_result.items = [self.schema.model_validate(item) for item in paginated_result.items]
            return paginated_result
        except AttributeError as e:
            raise ValueError(f"Invalid attribute in filter: {e}")

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

    async def get_by_id(self, entity_id: int) -> Optional[SchemaType]:
        try:
            result = await self.db.execute(select(self.model).filter(self.model.id == entity_id))
            db_obj = result.scalar_one()
            return self.schema.model_validate(db_obj)
        except NoResultFound:
            raise EntityNotFoundException(self.model.__name__, entity_id)
        
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
        """
        Create a new entity in the database and log the action in LogsAuditoria.

        Args:
            obj: Pydantic model containing the data to create the entity.

        Returns:
            BaseModel: The created entity, validated against the schema.

        Raises:
            ValueError: If user_id is None and the model requires it.
        """


        # Capture affected columns
        obj_data = obj.model_dump(exclude_unset=True)
        affected_columns = list(obj_data.keys())

        # Explicitly set usuario_id column
        if hasattr(self.model, 'usuario_id'):
            obj_data['usuario_id'] = current_user_id.get()
        # Asynchronously adding and committing a new object to the DB
        db_obj = self.model(**obj_data)
        self.db.add(db_obj)
        await self.db.commit()  # Commit transaction
        await self.db.refresh(db_obj)  # Refresh object state after commit

        # Capture values for affected columns
        valor_new = {
            key: getattr(db_obj, key) for key in affected_columns if hasattr(db_obj, key)
        }

        # Build audit object
        audit_data = LogsAuditoriaCreate(
            entidad=self.model.__tablename__,
            entidad_id=str(db_obj.id),
            accion='CREATE',
            valor_anterior=None,
            valor_nuevo=AnyUtils.serialize_data(valor_new),
            usuario_id=current_user_id.get()
        )

        # Insert the audit object register
        await self.auditor.log_audit(audit_log_data=audit_data)

        return self.schema.model_validate(db_obj)

    async def count(self) -> int:
        query = select(func.count()).select_from(self.model)
        result = await self.db.execute(query)
        return result.scalar()

    async def update(self, entity_id: int, obj: BaseModel) -> BaseModel:
        try:
            # Fetch the object to update asynchronously
            result = await self.db.execute(select(self.model).filter(self.model.id == entity_id))
            db_obj = result.scalar_one()

            #Capture affected columns
            update_data = obj.model_dump(exclude_unset=True)
            affected_columns = list(update_data.keys())
            affected_columns.append('usuario_id')

            valor_prev = {
                key: getattr(db_obj, key) for key in affected_columns if hasattr(db_obj, key)
            }

            # Update fields
            for key, value in update_data.items():
                # Hard-coding value encryption when is update password
                if key == 'clave' and value:
                    value = AnyUtils.generate_password_hash(value)
                setattr(db_obj, key, value)

            # Explicitly set usuario_id  column
            if hasattr(db_obj, 'usuario_id'):
                setattr(db_obj, 'usuario_id', current_user_id.get())

            # Capture new values for affected columns
            valor_new = {
                key: getattr(db_obj, key) for key in affected_columns if hasattr(db_obj, key)
            }
            await self.db.commit()  # Commit changes
            await self.db.refresh(db_obj)  # Refresh object state

            # Build and insert object register
            await self.auditor.log_audit(LogsAuditoriaCreate(
                entidad=self.model.__tablename__,
                entidad_id=str(db_obj.id),
                accion='UPDATE',
                valor_anterior=AnyUtils.serialize_data(valor_prev),
                valor_nuevo=AnyUtils.serialize_data(valor_new),
                usuario_id=current_user_id.get()
            ))

            return self.schema.model_validate(db_obj)
        except NoResultFound:
            raise EntityNotFoundException(self.model.__name__, entity_id)

    async def delete(self, entity_id: int) -> bool:
        try:
            # Fetch and delete the object asynchronously
            result = await self.db.execute(select(self.model).filter(self.model.id == entity_id))
            db_obj = result.scalar_one()
            db_obj_old = db_obj


            await self.db.delete(db_obj)
            await self.db.commit()  # Commit the deletion

            # Build audit object
            audit_data = LogsAuditoriaCreate(
                entidad=self.model.__tablename__,
                entidad_id=str(db_obj.id),
                accion='DELETE',
                valor_anterior=AnyUtils.serialize_data(db_obj_old),
                usuario_id=current_user_id.get()
            )

            # Insert the audit object register
            await self.auditor.log_audit(audit_log_data=audit_data)

            return True
        except NoResultFound:
            raise EntityNotFoundException(self.model.__name__, entity_id)
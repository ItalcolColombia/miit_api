from datetime import datetime
from typing import Optional, TypeVar, Generic, List, Any, Dict

from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from core.config.context import current_user_id
from core.contracts.auditor import Auditor
from core.exceptions.entity_exceptions import EntityNotFoundException
from schemas.logs_auditoria_schema import LogsAuditoriaCreate
from utils.any_utils import AnyUtils
from utils.logger_util import LoggerUtil

log = LoggerUtil()

ModelType = TypeVar("ModelType")
SchemaType = TypeVar("SchemaType")


def _normalize_datetimes(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recorre el dict y convierte objetos datetime o ISO strings a datetime aware en APP_TIMEZONE."""
    normalized = {}
    # importar una vez fuera del bucle
    # Guardar en UTC para persistencia consistente; convertir a zona de app solo al presentar
    from utils.time_util import normalize_to_utc
    for k, v in data.items():
        try:
            # Detectar objetos datetime y strings ISO
            if isinstance(v, datetime):
                # convertir a UTC antes de persistir
                normalized[k] = normalize_to_utc(v)
            elif isinstance(v, str):
                # intentar parsear ISO string y normalizar a UTC
                try:
                    normalized[k] = normalize_to_utc(v)
                except Exception:
                    normalized[k] = v
            else:
                normalized[k] = v
        except Exception:
            normalized[k] = v
    return normalized


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
            query = query.limit(1)  # Limitar a un solo resultado para evitar error de múltiples filas
            result = await self.db.execute(query)
            item = result.scalar_one_or_none()
            if item is None:
                return None
            return self.schema.model_validate(item)
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
        db_obj = self.model(**_normalize_datetimes(obj.model_dump()))  # Normalize datetimes before creating

        # Debug: log datetime fields of db_obj before persisting
        try:
            table = getattr(self.model, '__table__', None)
            if table is not None:
                for col in table.columns:
                    name = col.key
                    val = getattr(db_obj, name, None)
                    if isinstance(val, datetime):
                        log.info(f"[DEBUG repo.create] {self.model.__tablename__}.{name} = {val} (tzinfo={getattr(val, 'tzinfo', None)})")
        except Exception as e:
            log.warning(f"[DEBUG repo.create] No se pudieron inspeccionar columnas de {self.model.__name__}: {e}")

        # Explicitly set usuario_id column
        if hasattr(self.model, 'usuario_id'):
            setattr(db_obj, 'usuario_id', current_user_id.get())

        # Asynchronously adding and committing a new object to the DB
        self.db.add(db_obj)
        await self.db.commit()  # Commit transaction
        await self.db.refresh(db_obj)  # Refresh object state after commit

        # Build audit object
        audit_data = LogsAuditoriaCreate(
            entidad=self.model.__tablename__,
            entidad_id=str(db_obj.id),
            accion='CREATE',
            valor_anterior=None,
            valor_nuevo=AnyUtils.serialize_orm_object(db_obj),
            usuario_id=current_user_id.get()
        )

        # Insert the audit object register
        await self.auditor.log_audit(audit_log_data=audit_data)

        return self.schema.model_validate(db_obj)

    async def create_bulk(self, objects: List[BaseModel]) -> List[SchemaType]:
        """
        Create multiple entities in the database in a single transaction and log each creation in LogsAuditoria.

        Args:
            objects: List of Pydantic models containing the data for entities to create.

        Returns:
            List[SchemaType]: List of created entities, validated against the schema.

        Raises:
            ValueError: If user_id is None and the model requires it, or if the input list is empty.
        """
        if not objects:
            return []

        db_objects = []
        for obj in objects:
            normalized = _normalize_datetimes(obj.model_dump())
            db_obj = self.model(**normalized)
            if hasattr(self.model, 'usuario_id'):
                setattr(db_obj, 'usuario_id', current_user_id.get())
            db_objects.append(db_obj)

        try:
            self.db.add_all(db_objects)
            await self.db.commit()

            for db_obj in db_objects:
                await self.db.refresh(db_obj)
                audit_data = LogsAuditoriaCreate(
                    entidad=self.model.__tablename__,
                    entidad_id=str(db_obj.id),
                    accion='CREATE',
                    valor_anterior=None,
                    valor_nuevo=AnyUtils.serialize_orm_object(db_obj),
                    usuario_id=current_user_id.get()
                )
                await self.auditor.log_audit(audit_log_data=audit_data)

            return [self.schema.model_validate(db_obj) for db_obj in db_objects]
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error en create_bulk: {e}")




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
            normalized_update = _normalize_datetimes(update_data)
            for key, value in normalized_update.items():
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

    async def update_bulk(self, entity_ids: List[int], update_data: Dict[str, Any]) -> List[SchemaType]:
        """
        Update multiple entities in the database in a single transaction and log each update in LogsAuditoria.

        Args:
            entity_ids: List of entity IDs to update.
            update_data: Dictionary of column names and values to update.

        Returns:
            List[SchemaType]: List of updated entities, validated against the schema.

        Raises:
            EntityNotFoundException: If any entity ID is not found.
            ValueError: If the input list is empty or update_data is invalid.
        """
        if not entity_ids or not update_data:
            return []

        try:
            # Fetch entities to update
            query = select(self.model).filter(self.model.id.in_(entity_ids))
            result = await self.db.execute(query)
            db_objects = result.scalars().all()

            if len(db_objects) != len(entity_ids):
                missing_ids = set(entity_ids) - {db_obj.id for db_obj in db_objects}
                raise EntityNotFoundException(self.model.__name__, missing_ids)

            affected_columns = list(update_data.keys())
            if hasattr(self.model, 'usuario_id'):
                affected_columns.append('usuario_id')
                update_data['usuario_id'] = current_user_id.get()

            for db_obj in db_objects:
                valor_prev = {
                    key: getattr(db_obj, key) for key in affected_columns if hasattr(db_obj, key)
                }

                for key, value in update_data.items():
                    if key == 'clave' and value:
                        value = AnyUtils.generate_password_hash(value)
                    setattr(db_obj, key, value)

                valor_new = {
                    key: getattr(db_obj, key) for key in affected_columns if hasattr(db_obj, key)
                }

                await self.auditor.log_audit(LogsAuditoriaCreate(
                    entidad=self.model.__tablename__,
                    entidad_id=str(db_obj.id),
                    accion='UPDATE',
                    valor_anterior=AnyUtils.serialize_data(valor_prev),
                    valor_nuevo=AnyUtils.serialize_data(valor_new),
                    usuario_id=current_user_id.get()
                ))

            await self.db.commit()
            for db_obj in db_objects:
                await self.db.refresh(db_obj)

            return [self.schema.model_validate(db_obj) for db_obj in db_objects]
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error en update_bulk: {e}")

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

    async def delete_bulk(self, entity_ids: List[int]) -> bool:
        """
        Delete multiple entities from the database in a single transaction and log each deletion in LogsAuditoria.

        Args:
            entity_ids: List of entity IDs to delete.

        Returns:
            bool: True if deletion was successful, False if no entities were provided.

        Raises:
            EntityNotFoundException: If any entity ID is not found.
        """
        if not entity_ids:
            return False

        try:
            query = select(self.model).filter(self.model.id.in_(entity_ids))
            result = await self.db.execute(query)
            db_objects = result.scalars().all()

            if len(db_objects) != len(entity_ids):
                missing_ids = set(entity_ids) - {db_obj.id for db_obj in db_objects}
                raise EntityNotFoundException(self.model.__name__, missing_ids)

            for db_obj in db_objects:
                await self.db.delete(db_obj)
                audit_data = LogsAuditoriaCreate(
                    entidad=self.model.__tablename__,
                    entidad_id=str(db_obj.id),
                    accion='DELETE',
                    valor_anterior=AnyUtils.serialize_orm_object(db_obj),
                    usuario_id=current_user_id.get()
                )
                await self.auditor.log_audit(audit_log_data=audit_data)

            await self.db.commit()
            return True
        except Exception as e:
            await self.db.rollback()
            raise ValueError(f"Error en delete_bulk: {e}")
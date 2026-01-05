from datetime import datetime
from typing import Any

from utils.any_utils import AnyUtils
from utils.time_util import ensure_aware_local


def safe_serialize(obj: Any):
    """Serializa recursivamente una estructura o un objeto a tipos JSON-serializables.

    - Convierte datetimes a ISO 8601 respetando la zona local configurada por TZ cuando son naive.
    - Maneja Pydantic (model_dump), dicts, listas/tuplas/sets y objetos ORM (intentando AnyUtils.serialize_orm_object).
    - En caso de fallo, aplica fallback seguro (vars() y str()).
    """
    if obj is None:
        return None

    # Datetime -> ISO 8601 (respetando la zona si es aware o usando TZ si es naive)
    if isinstance(obj, datetime):
        try:
            if obj.tzinfo is None:
                # Asumir naive como hora local (según TZ) y devolver iso con offset
                aware = ensure_aware_local(obj)
                return aware.isoformat()
            # Si ya tiene tzinfo, devolver con su offset
            return obj.isoformat()
        except Exception:
            try:
                return obj.isoformat()
            except Exception:
                return None

    # Pydantic model
    if hasattr(obj, "model_dump"):
        try:
            dumped = obj.model_dump()
            return safe_serialize(dumped)
        except Exception:
            pass

    # Dict-like
    if isinstance(obj, dict):
        serialized = {}
        for k, v in obj.items():
            try:
                serialized[k] = safe_serialize(v)
            except Exception:
                serialized[k] = None
        return serialized

    # List / tuple / set
    if isinstance(obj, (list, tuple, set)):
        return [safe_serialize(i) for i in obj]

    # Try ORM serialization via AnyUtils (SQLAlchemy)
    try:
        orm_serialized = AnyUtils.serialize_orm_object(obj)
        if orm_serialized is not None:
            return orm_serialized
    except Exception:
        # Fallback: try to build from __dict__ without private attrs
        try:
            obj_vars = getattr(obj, "__dict__", None)
            if obj_vars:
                result = {}
                for k, v in obj_vars.items():
                    if k.startswith("_"):
                        continue
                    result[k] = safe_serialize(v)
                return result
        except Exception:
            pass

    # Primitives
    if isinstance(obj, (int, float, str, bool)):
        return obj

    # Ultimo recurso
    try:
        return str(obj)
    except Exception:
        return None

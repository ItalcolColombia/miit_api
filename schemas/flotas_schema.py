from datetime import datetime
from typing import Optional

from pydantic import Field, ConfigDict

from schemas.base_schema import BaseSchema


class FlotasResponse(BaseSchema):
    id: int
    tipo: str
    referencia: str
    puntos: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None
    estado_puerto: Optional[bool] = False
    estado_operador: Optional[bool] = False


model_config = ConfigDict(from_attributes=True)


class FlotaCreate(BaseSchema):
    tipo: Optional[str]
    referencia: str = Field(..., max_length=255)
    puntos: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None
    estado_puerto: Optional[bool] = True
    estado_operador: Optional[bool] = True


    model_config = ConfigDict(
        extra='ignore',
        json_schema_extra={
            "example": {
                "tipo": "buque",
                "referencia": "LIBERTY ISLAND",
                "puntos": None,
                "estado_puerto": True,
                "estado_operador": True,
            }
        }
    )

class FlotaUpdate(BaseSchema):
    referencia: Optional[str] = Field(None, max_length=255)
    puntos: Optional[int] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None
    estado_puerto: Optional[bool] = True
    estado_operador: Optional[bool] = True


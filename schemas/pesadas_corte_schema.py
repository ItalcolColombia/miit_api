from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field, ConfigDict

from schemas.base_schema import BaseSchema


class PesadasCorteResponse(BaseSchema):
    id: int
    puerto_id: str
    transaccion: int
    consecutivo: int
    pit: Optional[int] = None
    material: Optional[str] = None
    peso: Optional[Decimal] = None
    ref: Optional[str]
    enviado: Optional[bool] = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

model_config = ConfigDict(from_attributes=True)


class PesadasCorteCreate(BaseSchema):
    puerto_id: str
    transaccion: int
    consecutivo: int
    pit: Optional[int] = None
    material: Optional[str] = None
    peso: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    ref: str = Field(..., max_length=255)
    enviado: Optional[bool] = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "puerto_id" : "VOY2024008",
                "transaccion": 225123,
                "consecutivo": 2,
                "pit": 1,
                "material": "FSARG",
                "peso" : 500.00,
                "ref": "LDLR-8FD8E582",
                "enviado": True,
            }
        }

class PesadaCorteUpdate(BaseSchema):
    puerto_id: Optional[str] = None
    transaccion: Optional[int] = None
    consecutivo: Optional[float] = None
    pit: Optional[int] = None
    material: Optional[str] = None
    peso: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    ref: Optional[str] = None
    enviado: Optional[bool] = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

class PesadaCorteRetrieve(BaseSchema):
    puerto_id: Optional[str] = None
    transaccion: Optional[int] = None

class PesadasCalculate (BaseSchema):
    puerto_id: str
    referencia: str
    consecutivo: Optional[float] = None
    transaccion: Optional[int] = None
    pit: Optional[int] = None
    material: str
    peso: Optional[Decimal] = None
    fecha_hora: Optional[datetime] = None
    primera: Optional[int] = None
    ultima: Optional[int] = None
    usuario_id: Optional[int] = None

class PesadasRange (BaseSchema):
    primera: Optional[int] = None
    ultima: Optional[int] = None
    transaccion: Optional[int] = None

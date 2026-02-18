from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import Field, ConfigDict

from schemas.base_schema import BaseSchema


class BlsResponse(BaseSchema):
    id: int
    viaje_id : int
    material_id : int
    cliente_id: int
    no_bl: str
    peso_bl: Decimal
    peso_real: Optional[Decimal] = None
    cargue_directo: Optional[bool] = False
    estado_puerto: Optional[bool] = False
    estado_operador: Optional[bool] = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class BlsCreate(BaseSchema):
    viaje_id: int
    material_id: int
    cliente_id: int
    no_bl: str = Field(..., max_length=100)
    peso_bl: Decimal = Field(..., max_digits=10, decimal_places=2)
    cargue_directo: Optional[bool] = False
    estado_puerto: Optional[bool] = False
    estado_operador: Optional[bool] = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "viaje_id": 24330,
                "material_id": "1",
                "cliente_id" : "1",
                "no_bl": "SSF010448001",
                "peso_bl": 50478.00,
                "cargue_directo" : False,
                "estado_puerto": False,
                "estado_operador": False
            }
        }

class BlsUpdate(BaseSchema):
    viaje_id: Optional[int] = None
    material_id: Optional[int] = None
    cliente_id: Optional[int] = None
    no_bl: Optional[str] = Field(None, max_length=100)
    peso_bl: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_real: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    cargue_directo: Optional[bool] = None
    estado_puerto: Optional[bool] = None
    estado_operador: Optional[bool] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

class BlsExtCreate(BaseSchema):
    puerto_id: str
    viaje_id: Optional[int] = None
    material_name: Optional[str] = None
    material_id: Optional[int] = None
    cliente_name: Optional[str] = None
    cliente_id: Optional[int] = None
    no_bl: str = Field(..., max_length=100)
    peso_bl: Decimal = Field(..., max_digits=10, decimal_places=2)
    cargue_directo: Optional[bool] = False
    estado_puerto: Optional[bool] = False
    estado_operador: Optional[bool] = False

    class Config:
        json_schema_extra = {
            "example": {
                "puerto_id": "VOY2024001",
                "material_name": "TORTA DE SOYA USA",
                "cliente_name": "CUSTOMER COMPANY NAME",
                "no_bl": "SSF034576272",
                "peso_bl": 462000.00,
                "cargue_directo": False,
                "estado_puerto": False,
                "estado_operador": False
            }
        }

class VBlsResponse(BaseSchema):
    id: int
    no_bl:str
    transaccion:int
    viaje_id:int
    viaje:str
    referencia: str
    material_id: int
    material: str
    cliente_id : int
    cliente: str
    peso_bl: Decimal
    peso_real: Decimal
    cargue_directo : bool
    estado_puerto: bool
    estado_operador: bool
    fecha_hora: datetime
    usuario_id: int
    usuario:str

    class Config:
        from_attributes = True
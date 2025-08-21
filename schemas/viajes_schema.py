from pydantic import BaseModel, Field, field_validator, ConfigDict
from schemas.base_schema import BaseSchema
from datetime import datetime
from decimal import Decimal
from typing import Optional



class ViajesResponse(BaseSchema):
    id: int
    flota_id: int
    puerto_id: str
    peso_meta: Decimal
    peso_real: Decimal
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_id: Optional[int] = None
    viaje_origen: Optional[str] = None
    despacho_directo: Optional[bool] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

class ViajesActResponse(ViajesResponse):
    estado: Optional[bool] = None


class VViajesResponse(ViajesResponse):
    referencia: str
    estado: Optional[bool] = None

class ViajeCreate(BaseSchema):
    flota_id: int
    puerto_id: str = Field(..., max_length=300)
    peso_meta: Decimal = Field(..., max_digits=10, decimal_places=2)
    peso_real: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_id: Optional[int] = None
    viaje_origen: Optional[str] = None
    despacho_directo: Optional[bool] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None


    class Config:
        json_schema_extra = {
            "example": {
                "flota_id": 6232,
                "puerto_id": "24128",
                "peso": 30000.50,
                "fecha_llegada": "2025-04-27T10:00:00",
                "fecha_salida": "2025-04-29T14:30:00",
                "material_id": 10,
                "viaje_origen": 43,
                "despacho_directo": False,
            }
        }


class ViajeBuqueExtCreate(BaseModel):
    tipo: str = Field(..., max_length=6)
    referencia: str = Field(..., max_length=300)
    puerto_id: str = Field(..., max_length=300)
    peso_meta: Optional[Decimal] = 0
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    estado: Optional[bool] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    @field_validator('tipo')
    def tipo_valido(cls, value):
        if len(value) > 6:
            raise ValueError("Tipo debe tener máximo 6 caracteres")
        return value

    @field_validator('peso_meta')
    def peso_positivo(cls, value):
        if value < 0:
            raise ValueError("Peso debe ser positivo")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "buque",
                "referencia": "LIBERTY ISLAND",
                "puerto_id" : "VOY2024044",
                "peso_meta": 954000.50,
                "fecha_llegada": "2023-10-27T10:00:00",
                "fecha_salida": "2023-10-29T14:30:00",
                "estado": False
            }
        }


class ViajeCamionExtCreate(BaseModel):
    tipo: str = Field(..., max_length=6)
    referencia: str = Field(..., max_length=300)
    puerto_id: str = Field(..., max_length=300)
    peso_meta: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_name: Optional[str] = None
    viaje_origen: Optional[str] = None
    despacho_directo: Optional[bool] = None
    puntos: Optional[int] = 1
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    @field_validator('material_name')
    def material_name_not_empty(cls, value):
        if not value.strip():
            raise ValueError("Material no puede estar vacio")
        return value

    @field_validator('tipo')
    def tipo_valido(cls, value):
        if len(value) > 6:
            raise ValueError("Tipo debe tener máximo 6 caracteres")
        return value

    @field_validator('peso_meta')
    def peso_positivo(cls, value):
        if value <= 0:
            raise ValueError("Peso debe ser positivo")
        return value

    @field_validator('puntos')
    def puntos_valido(cls, value):
        if value <= 1:
            raise ValueError("Puntos debe ser mayor a  1")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "camion",
                "referencia": "XVZ479",
                "puerto_id": "24128",
                "peso_meta": 30000.50,
                "fecha_llegada": "2025-04-27T10:00:00",
                "fecha_salida": "2025-04-29T14:30:00",
                "material_name": "MAIZ USA",
                "viaje_origen": "VOY2024044",
                "despacho_directo": True
            }
        }



class FlotaExtLoadCreate(ViajeBuqueExtCreate):
    id: int
    bl_id: str = Field(..., max_length=100)
    razon_social: str = Field(..., max_length=300)
    material : str = Field(..., max_length=200)
    peso_bl: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None


    class Config:
        json_schema_extra = {
            "example": {
                "id" : 24230,
                "bl_id": "SSF034576272",
                "razon_social": "ITALCOL VILLAVICENCIO",
                "material_name": "TORTA DE SOYA USA",
                "peso_bl": 1345810.50
            }
        }

class ViajeUpdate(BaseSchema):
    flota_id: Optional[int] = None
    puerto_id: Optional[str] = Field(None, max_length=300)
    peso_meta: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_real: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_id: Optional[int] = None
    viaje_origen: Optional[int] = None
    despacho_directo: Optional[bool] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

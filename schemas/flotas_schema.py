from pydantic import BaseModel, Field, field_validator
from schemas.base_schema import BaseSchema
from datetime import datetime
from decimal import Decimal
from typing import Optional



class FlotasResponse(BaseSchema):
    id: int
    tipo: str
    referencia: str
    consecutivo: float
    peso: Decimal
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_id: Optional[int] = None
    despacho_directo: Optional[bool] = None

    class Config:
        from_attributes  = True

class FlotasActResponse(FlotasResponse):
    estado: Optional[bool] = None

class FlotaCreate(BaseSchema):
    id: int
    tipo: str = Field(..., max_length=6)
    referencia: str = Field(..., max_length=300)
    consecutivo: int
    peso: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_id: int
    despacho_directo: bool

    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "Buque",
                "referencia": "LIBERTY ISLAND",
                "consecutivo": 24157,
                "peso": 1000.50,
                "fecha_llegada": "2023-10-27T10:00:00",
                "fecha_salida": "2023-10-29T14:30:00",
                "material_id": 1,
                "despacho_directo": True,
            }
        }


class FlotaBuqueExtCreate(BaseModel):
    id: int
    tipo: str = Field(..., max_length=6)
    referencia: str = Field(..., max_length=300)
    consecutivo: int
    peso: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_name: str

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

    @field_validator('peso')
    def peso_positivo(cls, value):
        if value <= 0:
            raise ValueError("Peso debe ser positivo")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "id" : 24230,
                "tipo": "Buque",
                "referencia": "LIBERTY ISLAND",
                "consecutivo": 24157,
                "peso": 1000.50,
                "fecha_llegada": "2023-10-27T10:00:00",
                "fecha_salida": "2023-10-29T14:30:00",
                "material_name": "TORTA DE SOYA USA",
            }
        }


class FlotaCamionExtCreate(BaseModel):
    id: int
    tipo: str = Field(..., max_length=6)
    referencia: str = Field(..., max_length=300)
    consecutivo: int
    peso: Decimal = Field(..., max_digits=10, decimal_places=2)
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_name: str
    despacho_directo: bool
    puntos: int

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

    @field_validator('peso')
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
                "id" : 24231,
                "tipo": "Camion",
                "referencia": "XVU278",
                "consecutivo": 24158,
                "peso": 30000.50,
                "fecha_llegada": "2023-10-28T13:00:00",
                "fecha_salida": "2023-10-28T15:10:00",
                "material_name": "MAIZ USA",
                "despacho_directo": True,
                "puntos": 6
            }
        }



class FlotaExtLoadCreate(FlotaBuqueExtCreate):
    id: int
    bl_id: str = Field(..., max_length=100)
    razon_social: str = Field(..., max_length=300)
    material : str = Field(..., max_length=200)
    peso_bl: Decimal = Field(..., max_digits=10, decimal_places=2)


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

class FlotaUpdate(BaseSchema):
    tipo: Optional[str] = Field(None, max_length=6)
    referencia: Optional[str] = Field(None, max_length=300)
    consecutivo: Optional[float] = None
    peso: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    fecha_llegada: Optional[datetime] = None
    fecha_salida: Optional[datetime] = None
    material_id: Optional[int] = None


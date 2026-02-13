from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ConfigDict

from schemas.base_schema import BaseSchema


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
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    @field_validator('tipo')
    def tipo_valido(cls, value):
        # Acepta cualquier combinación de mayúsculas/minúsculas y normaliza a 'buque'
        if not isinstance(value, str):
            raise TypeError("Tipo debe ser una cadena")
        val = value.strip()
        if len(val) > 6:
            raise ValueError("Tipo debe tener máximo 6 caracteres")
        if val.lower() != 'buque':
            raise ValueError("Tipo debe ser 'buque'")
        return 'buque'

    @field_validator('peso_meta')
    def peso_positivo(cls, value):
        if value < 0:
            raise ValueError("Peso debe ser positivo")
        return value

    # Normalizar datetimes naive a APP_TIMEZONE
    @field_validator('fecha_llegada', 'fecha_salida', 'fecha_hora', mode='before')
    def _normalize_datetimes(cls, v):
        from utils.time_util import normalize_to_app_tz
        if v is None:
            return None
        return normalize_to_app_tz(v)

    class Config:
        json_schema_extra = {
            "example": {
                "tipo": "buque",
                "referencia": "LIBERTY ISLAND",
                "puerto_id" : "VOY2024044",
                "peso_meta": 954000.50,
                "fecha_llegada": "2023-10-27T10:00:00",
                "fecha_salida": "2023-10-29T14:30:00",
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
        # Acepta cualquier combinación de mayúsculas/minúsculas y normaliza a 'camion'
        if not isinstance(value, str):
            raise TypeError("Tipo debe ser una cadena")
        val = value.strip()
        if len(val) > 6:
            raise ValueError("Tipo debe tener máximo 6 caracteres")
        if val.lower() != 'camion':
            raise ValueError("Tipo debe ser 'camion'")
        return 'camion'

    @field_validator('peso_meta')
    def peso_positivo(cls, value):
        if value < 0:
            raise ValueError("Peso debe ser positivo")
        return value

    # Normalizar datetimes naive a APP_TIMEZONE
    @field_validator('fecha_llegada', 'fecha_salida', 'fecha_hora', mode='before')
    def _normalize_datetimes(cls, v):
        from utils.time_util import normalize_to_app_tz
        if v is None:
            return None
        return normalize_to_app_tz(v)

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


class ViajesActivosPorMaterialResponse(BaseModel):
    consecutivo: int
    nombre: str
    material: str
    puntos_cargue: Optional[int] = None
    peso: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


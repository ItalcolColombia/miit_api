from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
from typing import Optional
from decimal import Decimal


class TransaccionResponse(BaseModel):
    id: Optional[int] = None
    material_id: int
    tipo: str
    viaje_id: Optional[int] = None
    pit: Optional[int] = None
    ref1: Optional[str] = None
    ref2: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    origen_id: Optional[int] = None
    destino_id: Optional[int] = None
    peso_meta: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_real: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    estado: Optional[str] = None
    leido: Optional[bool] = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None


    class Config:
        from_attributes = True


class TransaccionCreate(TransaccionResponse):
    material_id: int
    tipo: str
    viaje_id: int
    pit: int
    ref1: Optional[str] = None
    ref2: Optional[str] = None
    fecha_inicio: datetime = None
    fecha_fin: Optional[datetime] = None
    origen_id: int
    destino_id: Optional[int] = None
    peso_meta: Decimal = Field( max_digits=10, decimal_places=2)
    peso_real: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    estado: Optional[str] = Field(default="Registrada", min_length=1)
    leido: Optional[bool] = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    @field_validator('tipo')
    def tipo_valido(cls, value):
        if len(value) > 9:
            raise ValueError("Tipo debe tener máximo 8 carácteres")
        return value

    @field_validator('peso_meta')
    def peso_positivo(cls, value):
        if value <= 0:
            raise ValueError("Peso debe ser positivo")
        return value

    class Config:
        json_schema_extra = {
            "example": {
                "material_id": 2,
                "tipo": "Despacho",
                "viaje_id": 11182,
                "pit": 4,
                "ref1": "24126",
                "fecha_inicio": datetime(2025, 5, 10, 13, 25),
                "origen_id": 102,
                "peso_meta": 34230
            }
        }

class TransaccionUpdate(BaseModel):
    material_id: Optional[int] = None
    tipo: Optional[str] = None
    viaje_id: Optional[int] = None
    pit: Optional[int] = None
    ref1: Optional[str] = None
    ref2: Optional[str] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    origen_id: Optional[int] = None
    destino_id: Optional[int] = None
    peso_meta: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    peso_real: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    estado: Optional[str] = None
    leido: Optional[bool] = None
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

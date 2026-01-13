from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


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
    bl_id: Optional[int] = None


    class Config:
        from_attributes = True


class TransaccionCreate(TransaccionResponse):
    material_id: int
    tipo: str
    viaje_id: Optional[int] = None  # Opcional para tipo Traslado
    pit: Optional[int] = None  # Opcional para tipo Traslado
    ref1: Optional[str] = None
    ref2: Optional[str] = None
    fecha_inicio: datetime = None
    fecha_fin: Optional[datetime] = None
    origen_id: Optional[int] = None
    destino_id: Optional[int] = None
    peso_meta: Decimal = Field( max_digits=10, decimal_places=2)
    peso_real: Optional[Decimal] = Field(None, max_digits=10, decimal_places=2)
    estado: Optional[str] = Field(default="Registrada", min_length=1)
    leido: Optional[bool] = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None
    bl_id: Optional[int] = None

    @field_validator('tipo')
    def tipo_valido(cls, value):
        if len(value) > 10:
            raise ValueError("Tipo debe tener máximo 10 carácteres")
        return value

    @field_validator('peso_meta')
    def peso_positivo(cls, value):
        if value <= 0:
            raise ValueError("Peso debe ser positivo")
        return value

    @model_validator(mode='after')
    def validar_campos_por_tipo(self):
        tipo_lower = (self.tipo or '').strip().lower()

        if tipo_lower == 'traslado':
            # Para Traslado: origen_id y destino_id son obligatorios
            if self.origen_id is None:
                raise ValueError("origen_id es obligatorio para transacciones de tipo Traslado")
            if self.destino_id is None:
                raise ValueError("destino_id es obligatorio para transacciones de tipo Traslado")
        else:
            # Para Despacho/Recibo: viaje_id y pit son obligatorios
            if self.viaje_id is None:
                raise ValueError("viaje_id es obligatorio para transacciones de tipo Despacho/Recibo")
            if self.pit is None:
                raise ValueError("pit es obligatorio para transacciones de tipo Despacho/Recibo")

        return self

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Ejemplo Despacho",
                    "value": {
                        "material_id": 2,
                        "tipo": "Despacho",
                        "viaje_id": 11182,
                        "pit": 4,
                        "ref1": "24126",
                        "fecha_inicio": "2025-05-10T13:25:00",
                        "origen_id": 102,
                        "destino_id": 301,
                        "peso_meta": 34230
                    }
                },
                {
                    "summary": "Ejemplo Traslado",
                    "value": {
                        "material_id": 24,
                        "tipo": "Traslado",
                        "origen_id": 102,
                        "destino_id": 103,
                        "peso_meta": 30000,
                        "estado": "Registrada"
                    }
                }
            ]
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
    bl_id: Optional[int] = None

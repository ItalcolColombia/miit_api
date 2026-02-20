from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator

from utils.time_util import now_local


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
    fecha_inicio: datetime = Field(default_factory=now_local)
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
            # Solo para Despacho: peso_meta debe ser positivo
            if tipo_lower == 'despacho' and self.peso_meta is not None and self.peso_meta <= 0:
                raise ValueError("peso_meta debe ser positivo para transacciones de tipo Despacho")

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


class TransaccionCreateExt(BaseModel):
    """
    Schema simplificado para la creación de transacciones desde el endpoint refactorizado.
    Los IDs se resuelven internamente a partir de los nombres.
    """
    tipo: str = Field(..., description="Tipo de transacción: 'Recibo', 'Despacho' o 'Traslado'")
    viaje_id: Optional[int] = Field(None, description="ID del viaje (buque/camión). Se omite en Traslado")
    material: str = Field(..., description="Nombre del material")
    destino: Optional[str] = Field(None, description="Nombre del almacenamiento destino. Se omite en Despacho")
    origen: Optional[str] = Field(None, description="Nombre del almacenamiento origen. Se omite en Recibo")
    pit: Optional[int] = Field(default=1, description="Número del pit de cargue. Por defecto es 1. Se omite en Traslado")

    @field_validator('tipo')
    def tipo_valido(cls, value):
        tipos_validos = ['recibo', 'despacho', 'traslado']
        if value.strip().lower() not in tipos_validos:
            raise ValueError(f"Tipo debe ser uno de: Recibo, Despacho, Traslado")
        # Capitalizar primera letra
        return value.strip().capitalize()

    @model_validator(mode='after')
    def validar_campos_por_tipo(self):
        tipo_lower = (self.tipo or '').strip().lower()

        if tipo_lower == 'traslado':
            # Para Traslado: origen y destino son obligatorios, viaje_id y pit no aplican
            if not self.origen:
                raise ValueError("origen es obligatorio para transacciones de tipo Traslado")
            if not self.destino:
                raise ValueError("destino es obligatorio para transacciones de tipo Traslado")
        elif tipo_lower == 'recibo':
            # Para Recibo: viaje_id y destino son obligatorios, pit es opcional (default 1)
            if self.viaje_id is None:
                raise ValueError("viaje_id es obligatorio para transacciones de tipo Recibo")
            if not self.destino:
                raise ValueError("destino es obligatorio para transacciones de tipo Recibo")
        elif tipo_lower == 'despacho':
            # Para Despacho: viaje_id y origen son obligatorios, pit es opcional (default 1)
            if self.viaje_id is None:
                raise ValueError("viaje_id es obligatorio para transacciones de tipo Despacho")
            if not self.origen:
                raise ValueError("origen es obligatorio para transacciones de tipo Despacho")

        return self

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "summary": "Ejemplo Recibo (buque a silo) - pit opcional, default 1",
                    "value": {
                        "tipo": "Recibo",
                        "viaje_id": 25843,
                        "material": "AMERICAN YELLOW CORN",
                        "destino": "SILO 1"
                    }
                },
                {
                    "summary": "Ejemplo Despacho (silo a camión) - con pit explícito",
                    "value": {
                        "tipo": "Despacho",
                        "viaje_id": 11182,
                        "material": "TORTA DE SOYA USA",
                        "origen": "SILO 2",
                        "pit": 4
                    }
                },
                {
                    "summary": "Ejemplo Traslado (silo a silo)",
                    "value": {
                        "tipo": "Traslado",
                        "material": "MAIZ AMARILLO",
                        "origen": "SILO 1",
                        "destino": "SILO 3"
                    }
                }
            ]
        }


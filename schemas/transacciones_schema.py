from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TransaccionBase(BaseModel):
    material_id: int
    tipo: str
    ref1: Optional[str] = None
    ref2: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    origen_id: Optional[int] = None
    destino_id: Optional[int] = None
    estado: str
    leido: bool
    viaje_id: Optional[int] = None
    pit: Optional[int] = None

class TransaccionCreate(TransaccionBase):
    material_id: int
    tipo: str
    ref1: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    origen_id: Optional[int] = None
    destino_id: Optional[int] = None
    estado: str = "Registrada"
    leido: bool = False
    viaje_id: Optional[int] = None
    pit: Optional[int] = None


    class Config:
        json_schema_extra = {
            "example": {
                "material_id": 2,
                "tipo": "Despacho",
                "ref1": "24126",
                "fecha_creacion": datetime(2025, 5, 10, 13, 10),
                "fecha_inicio": datetime(2025, 5, 10, 13, 25),
                "fecha_fin": datetime(2025, 5, 10, 13, 41),
                "origen_id": 102,
                "viaje_id": 11182,
                "pit": 4
            }
        }

class TransaccionUpdate(TransaccionBase):
    material_id: Optional[int] = None
    tipo: Optional[str] = None
    ref1: Optional[str] = None
    ref2: Optional[str] = None
    fecha_creacion: Optional[datetime] = None
    fecha_inicio: Optional[datetime] = None
    fecha_fin: Optional[datetime] = None
    origen_id: Optional[int] = None
    destino_id: Optional[int] = None
    estado: Optional[str] = None
    leido: Optional[bool] = None
    viaje_id: Optional[int] = None
    pit: Optional[int] = None

class TransaccionResponse(TransaccionBase):
    id: int

    class Config:
        from_attributes = True


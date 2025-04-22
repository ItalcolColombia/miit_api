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
    buque_id: Optional[int] = None
    camion_id: Optional[int] = None
    pit: Optional[int] = None

class TransaccionCreate(TransaccionBase):
    pass

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
    buque_id: Optional[int] = None
    camion_id: Optional[int] = None
    pit: Optional[int] = None

class TransaccionResponse(TransaccionBase):
    id: int

    class Config:
        from_attributes = True


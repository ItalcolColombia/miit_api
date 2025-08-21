from typing import Optional

from pydantic import BaseModel, ConfigDict
import datetime

class RolBase(BaseModel):
    nombre: str
    estado: bool
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Administrador",
                "estado": "true"
            }
        }

class RolCreate(RolBase):
    pass

class RolResponse(RolBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
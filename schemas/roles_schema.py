from pydantic import BaseModel, ConfigDict
import datetime

class RolBase(BaseModel):
    nombre: str
    estado: bool

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
from typing import Optional

from pydantic import BaseModel, Field

class BuquesResponse(BaseModel):
    id: int
    nombre: str
    estado: bool

    class Config:
        from_attributes  = True

class BuqueCreate(BaseModel):
    nombre: str = Field(..., max_length=255)
    estado: bool = True
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "LIBERTY ISLAND",
                "estado": True,
            }
        }

class BuqueUpdate(BaseModel):
    nombre: Optional[str] = Field(None, max_length=255)
    estado: Optional[bool] = None

# class BuqueEstadoUpdate(BaseModel):
#     flota_id: int
#     class Config:
#         json_schema_extra = {
#             "example": {
#                 "flota_id": "24230"
#             }
#         }
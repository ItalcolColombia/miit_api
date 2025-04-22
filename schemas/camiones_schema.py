from typing import Optional

from pydantic import BaseModel, Field

class CamionResponse(BaseModel):
    id: int
    placa: str
    puntos: int

    class Config:
        from_attributes  = True

class CamionCreate(BaseModel):
    placa: str = Field(..., max_length=6)
    puntos: int

    class Config:
        json_schema_extra = {
            "example": {
                "placa": "XVU276",
                "puntos": 6,
            }
        }

class CamionUpdate(BaseModel):
    placa: str = Field(..., max_length=6)
    puntos: Optional[int] = 6


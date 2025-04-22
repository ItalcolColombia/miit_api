from pydantic import BaseModel, Field, field_validator
from schemas.base_schema import BaseSchema
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, List, Any


class BaseResponse(BaseModel):
    status_code: str = Field(..., description="The HTTP status code")
    status_name: str = Field(..., description="The name of the HTTP status")
    message: Optional[str] = Field(None, description="A descriptive message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")

class CreateResponse(BaseResponse):
    class Config:
        validate_by_name = True
        json_schema_extra = {
            "example": {
                "status_code": "201",
                "status_name": "Created",
                "message": "Creación exitosa",
            }
        }

class UpdateResponse(BaseResponse):
    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "200",
                "status_name": "OK",
                "message": "Actualización exitosa",
            }
        }

class ErrorResponse(BaseResponse):
    class Config:
        validate_by_name = True
        json_schema_extra = {
            "example": {
                "status_code": "400",
                "status_name": "Bad Request",
                "message": "Detalles Error",
            }
        }

class ValidationErrorResponse(BaseResponse):
    class Config:
        validate_by_name = True
        json_schema_extra = {
            "example": {
                "status_code": "422",
                "status_name": "Entidad no procesable",
                "message": "Errror de validación",
                "data": [{"loc": ["body", "field_name"], "msg": "Field required", "type": "value_error.missing"}],
            }
        }
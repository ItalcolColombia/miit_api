from pydantic import BaseModel, Field
from typing import Optional


class BaseSchema(BaseModel):
    class Config:
        from_attributes = True

class CreateSuccessResponse(BaseModel):
    status_code: str
    status_name: str
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "201",
                "status_name": "Created",
                "message": "registro exitoso"
            }
        }

class CustomErrorResponse(BaseModel):
    status_code: str = Field(..., description="The HTTP status code for the error")
    status_name: str = Field(..., description="The name of the HTTP status")
    message: Optional[str] = Field(..., description="Details about the error")

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "422",
                "status_name": "Unprocessable request",
                "message": "Validation error"
            }
        }

class ValidationErrorDetail(BaseModel):
    field: str = Field(..., description="The field that caused the validation error")
    error: str = Field(..., description="The error message for the field")

    class Config:
        json_schema_extra = {
            "example": {
                "field": "id",
                "error": "Field required"
            }
        }
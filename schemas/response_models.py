from datetime import datetime
from typing import Optional, Dict, List, Any

from pydantic import Field

from schemas.base_schema import BaseSchema
from schemas.pesadas_corte_schema import PesadasCorteResponse
from schemas.transacciones_schema import TransaccionResponse


class BaseResponse(BaseSchema):
    """
    Base response model for API responses.

    This model defines the common structure for all API response schemas, including
    HTTP status code, status name, an optional message, and optional additional data.

    Attributes:
        status_code (str): The HTTP status code (e.g., "200", "404").
        status_name (str): The name of the HTTP status (e.g., "OK", "Not Found").
        message (Optional[str]): A descriptive message about the response.
        meta (Optional[Dict[str, Any]]): Metadata included in the response.
        data (Optional[Dict[str, Any]]): Additional data included in the response.
    """

    status_code: str = Field(..., description="The HTTP status code")
    status_name: str = Field(..., description="The name of the HTTP status")
    timestamp: datetime = Field(default_factory=datetime.timestamp, description="Response generation timestamp")
    message: Optional[str] = Field(None, description="A descriptive message")
    meta: Optional[Dict[str, Any]] = Field(None, description="Metadata (e.g., request_id)")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")


class SuccessResponse(BaseResponse):
    """
    Response model for generic successful operations (e.g., GET requests).

    Extends BaseResponse with a default configuration for successful responses, typically
    returning a 200 OK status.

    Attributes:
        Inherits all attributes from BaseResponse.
    """
    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "200",
                "status_name": "OK",
                "timestamp": "2025-09-12T10:40:00Z",
                "message": "Request successful",
                "data": {}
            }
        }

class CreateResponse(BaseResponse):
    """
    Response model for successful creation operations.

    Extends BaseResponse with specific configuration for creation responses, typically
    returning a 201 Created status.

    Attributes:
        Inherits all attributes from BaseResponse.
    """

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "201",
                "status_name": "Created",
                "timestamp": "2025-09-12T10:40:00Z",
                "message": "Creación exitosa",
                "data": {}
            }
        }

class UpdateResponse(BaseResponse):
    """
    Response model for successful update operations.

    Extends BaseResponse with specific configuration for update responses, typically
    returning a 200 OK status.

    Attributes:
        Inherits all attributes from BaseResponse.
    """

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "200",
                "status_name": "OK",
                "timestamp": "2025-09-12T10:40:00Z",
                "message": "Actualización exitosa",
                "data": {}
            }
        }

class ErrorResponse(BaseResponse):
    """
    Response model for error responses.

    Extends BaseResponse with specific configuration for error responses, typically
    returning a 400 Bad Request or other error status.

    Attributes:
        Inherits all attributes from BaseResponse.
    """

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "400",
                "status_name": "Bad Request",
                "timestamp": "2025-09-12T10:40:00Z",
                "message": "Detalles Error",
                "data": {}
            }
        }

class ValidationErrorResponse(BaseResponse):
    """
    Response model for validation error responses.

    Extends BaseResponse to include a list of validation error details, typically
    returning a 422 Unprocessable Entity status.

    Attributes:
        details (Optional[List[str]]): A list of validation error messages.
        Inherits all attributes from BaseResponse.
    """

    details: Optional[List[str]] = Field(None, description="List of validation error messages")

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "422",
                "status_name": "Unprocessable Entity",
                "timestamp": "2025-09-12T10:40:00Z",
                "message": "Error de validación",
                "meta": {"request_id": "abc123"},
                "details": ["Id: Field required"],
                "data": None
            }
        }


class EndBuqueData(BaseSchema):
    transaccion: Optional[TransaccionResponse] = None
    ultima_pesada: Optional[PesadasCorteResponse] = None


class EndBuqueResponse(BaseResponse):
    data: Optional[EndBuqueData] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status_code": "200",
                "status_name": "OK",
                "message": "estado actualizado",
                "data": {
                    "transaccion": None,
                    "ultima_pesada": None
                }
            }
        }

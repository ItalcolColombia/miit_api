# /src/contracts/response_util.py

from http import HTTPStatus
from typing import Optional, Dict, Union, Any

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from utils.any_utils import AnyUtils
from utils.serialize_util import safe_serialize


class ResponseUtil:
    """
    Class responsible for handling JSON responses.

    This class provides a method to generate consistent JSON responses with
    status codes, messages, and optional data.

    Class Args:
        None
    """

    @staticmethod
    def _prepare_data(data: Any) -> Any:
        """Normalize response data converting datetimes to America/Bogota ISO strings.

        Supports dicts, lists, Pydantic models (model_dump), and SQLAlchemy ORM objects.
        """
        if data is None:
            return None

        # Use safe_serialize as the central normalizer (handles pydantic, orm, dicts, lists)
        try:
            return safe_serialize(data)
        except Exception:
            pass

        # Fallbacks (existing logic):
        # Pydantic model
        if hasattr(data, 'model_dump'):
            try:
                dumped = data.model_dump()
                return AnyUtils.serialize_data(dumped)
            except Exception:
                pass

        # SQLAlchemy ORM object
        try:
            # AnyUtils.serialize_orm_object handles None and ORM objects
            orm_serialized = AnyUtils.serialize_orm_object(data)
            if orm_serialized is not None:
                return orm_serialized
        except Exception:
            pass

        # List of items
        if isinstance(data, list):
            processed = []
            for item in data:
                if hasattr(item, 'model_dump'):
                    processed.append(AnyUtils.serialize_data(item.model_dump()))
                else:
                    orm_item = AnyUtils.serialize_orm_object(item)
                    if orm_item is not None:
                        processed.append(orm_item)
                    elif isinstance(item, dict):
                        processed.append(AnyUtils.serialize_data(item))
                    else:
                        processed.append(item)
            return processed

        # Dict-like
        if isinstance(data, dict):
            return AnyUtils.serialize_data(data)

        # Fallback: try to serialize primitives or unknown objects via jsonable_encoder later
        return data

    @staticmethod
    def json_response(
            status_code: int,
            message: str | None = None,
            data: Optional[Dict[str, Any]] = None,
            token: Optional[str]  = None,
            headers: Optional[Dict[str, str]] = None
    ) -> JSONResponse:
        """
        Public method responsible for generating a standardized JSON response.

        This method creates a response containing a status code, a status name,
        an optional message, and optional data.

        Args:
            status_code (int): The HTTP status code for the response.
            message (str, optional): A message describing the response. Defaults to None.
            data (Dict[str, str], optional): Additional data to include in the response. Defaults to None.
            token (str, optional): Authentication token to include in the response. Defaults to None.
            headers (Dict[str, str], optional): HTTP headers to include in the response. Defaults to None.


        Returns:
            JSONResponse: A formatted JSON response containing the specified status code, message, and data.
        """

        response_content: Dict[str, Union[str, Dict[str, str]]] = {
            "status_code": str(status_code),
            "status_name": HTTPStatus(status_code).phrase,
        }

        if message is not None:
            response_content["message"] = message

        if token is not None:
            response_content["token"] = token

        if data is not None:
            response_content["data"] = ResponseUtil._prepare_data(data)

        # Ensure content is JSON serializable (datetimes, decimals, pydantic models, etc.)
        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=status_code, content=encoded)

# /src/contracts/response_util.py

from http import HTTPStatus
from typing import Optional, Dict, Union, Any

from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


class ResponseUtil:
    """
    Class responsible for handling JSON responses.

    This class provides a method to generate consistent JSON responses with
    status codes, messages, and optional data.

    Class Args:
        None
    """

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
            response_content["data"] = data

        # Ensure content is JSON serializable (datetimes, decimals, pydantic models, etc.)
        encoded = jsonable_encoder(response_content)
        return JSONResponse(status_code=status_code, content=encoded)

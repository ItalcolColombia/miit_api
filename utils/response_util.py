# /src/utils/response_util.py

from http import HTTPStatus
from typing import Dict, Union, Any

from fastapi.responses import JSONResponse


class ResponseUtil:
    """
    Class responsible for handling JSON responses.

    This class provides a method to generate consistent JSON responses with
    status codes, messages, and optional data.

    Class Args:
        None
    """

    def json_response(
        self,
        status_code: int,
        message: str | None = None,
        data: Dict[str, Any]| None = None,
    ) -> JSONResponse:
        """
        Public method responsible for generating a standardized JSON response.

        This method creates a response containing a status code, a status name,
        an optional message, and optional data.

        Args:
            status_code (int): The HTTP status code for the response.
            message (str, optional): A message describing the response. Defaults to None.
            data (Dict[str, str], optional): Additional data to include in the response. Defaults to None.

        Returns:
            JSONResponse: A formatted JSON response containing the specified status code, message, and data.
        """

        response_content: Dict[str, Union[str, Dict[str, str]]] = {
            "status_code": str(status_code),
            "status_name": HTTPStatus(status_code).phrase,
        }

        if message is not None:
            response_content["message"] = message

        if data is not None:
            response_content["data"] = data

        return JSONResponse(status_code=status_code, content=response_content)
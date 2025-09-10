
import httpx
from typing import Dict, Any, Optional
from fastapi import status
from core.config.external_api import get_token
from core.exceptions.entity_exceptions import BasedException
from utils.any_utils import AnyUtils
from utils.logger_util import LoggerUtil

log = LoggerUtil()

class ExtApiService:
    def __init__(self):
        self._http_client = httpx.AsyncClient()

    async def get(self, url: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Retrieve data from an external API via a GET request.

        Sends a GET request to the specified URL, using the injected JWT token for authentication.
        Optional query parameters can be provided.

        Args:
            url (str): The URL to send the GET request to.
            params (Optional[Dict[str, Any]]): Query parameters to include in the request.

        Returns:
            Dict[str, Any]: The response from the external API.

        Raises:
            BasedException: If the request fails due to invalid parameters or server issues.
            httpx.HTTPStatusError: If the API returns an HTTP error status.
            httpx.RequestError: If a network error occurs during the request.
        """
        try:
            # Obtener token válido (refresca si expiró)
            jwt_token = await get_token()

            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }

            response = await self._http_client.get(
                url,
                params=params,
                headers=headers
            )
            response.raise_for_status()

            response_data = response.json()
            log.info(f"GET request successful for URL: {url}")
            return response_data
        except httpx.HTTPStatusError as e:
            log.error(f"GET request failed (status: {e.response.status_code}): {e.response.text}")
            raise
        except httpx.RequestError as e:
            log.error(f"Connection error during GET request: {e}")
            raise BasedException(
                message=f"Error de conexión al realizar GET: {str(e)}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            log.error(f"Unexpected error during GET request: {e}")
            raise BasedException(
                message="Error inesperado al realizar la solicitud GET.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def post(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Send a generic notification to an external API via a POST request.

        Sends the provided notification data in a POST request to the external API, using the
        injected JWT token for authentication.

        Args:
            data (Dict[str, Any]): A dictionary containing the notification data to send.
            url (str): The URL to send the data to.

        Returns:
            Dict[str, Any]: The response from the external API.

        Raises:
            BasedException: If the notification data is invalid or the request fails.
            httpx.HTTPStatusError: If the API returns an HTTP error status.
            httpx.RequestError: If a network error occurs during the request.
        """
        try:
            if not data:
                log.error("Los datos de notificación están vacíos.")
                raise BasedException(
                    message="Los datos de notificación no pueden estar vacíos.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            # Obtener token válido (refresca si expiró)
            jwt_token = await get_token()
            if not jwt_token:
                log.error("No se pudo obtener un token JWT válido.")
                raise BasedException(
                    message="No se pudo obtener un token JWT válido.",
                    status_code=status.HTTP_401_UNAUTHORIZED
                )

            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }

            response = await self._http_client.post(
                url=url,
                json=data,
                headers=headers
            )
            response.raise_for_status()

            response_data = response.json()
            log.info(f"Notificación enviada con éxito: {data}")
            return response_data
        except httpx.HTTPStatusError as e:
            log.error(f"Fallo en la notificación a la API (status: {e.response.status_code}): {e.response.text}")
            raise
        except httpx.RequestError as e:
            log.error(f"Error de conexión al intentar notificar a la API: {e}")
            raise BasedException(
                message=f"Error de conexión al notificar: {str(e)}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            log.error(f"Error inesperado al enviar notificación: {e}")
            raise BasedException(
                message="Error inesperado al enviar la notificación.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def put(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Update data on an external API via a PUT request.

        Sends the provided data in a PUT request to the external API, using the injected JWT token
        for authentication.

        Args:
            data (Dict[str, Any]): A dictionary containing the data to update.
            url (str): The URL to send the data to.

        Returns:
            Dict[str, Any]: The response from the external API.

        Raises:
            BasedException: If the data is invalid or the request fails.
            httpx.HTTPStatusError: If the API returns an HTTP error status.
            httpx.RequestError: If a network error occurs during the request.
        """
        try:
            if not data:
                log.error("Los datos de actualización están vacíos.")
                raise BasedException(
                    message="Los datos de actualización no pueden estar vacíos.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            # Obtener token válido (refresca si expiró)
            jwt_token = await get_token()

            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }

            response = await self._http_client.put(
                url=url,
                json=AnyUtils.serialize_dict(data),
                headers=headers
            )
            response.raise_for_status()

            response_data = response.json()
            log.info(f"PUT request successful: {data}")
            return response_data
        except httpx.HTTPStatusError as e:
            log.error(f"PUT request failed (status: {e.response.status_code}): {e.response.text}")
            raise
        except httpx.RequestError as e:
            log.error(f"Connection error during PUT request: {e}")
            raise BasedException(
                message=f"Error de conexión al realizar PUT: {str(e)}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            log.error(f"Unexpected error during PUT request: {e}")
            raise BasedException(
                message="Error inesperado al realizar la solicitud PUT.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    async def patch(self, data: Dict[str, Any], url: str) -> Dict[str, Any]:
        """Partially update data on an external API via a PATCH request.

        Sends the provided data in a PATCH request to the external API, using the injected JWT token
        for authentication.

        Args:
            data (Dict[str, Any]): A dictionary containing the data to partially update.
            url (str): The URL to send the data to.

        Returns:
            Dict[str, Any]: The response from the external API.

        Raises:
            BasedException: If the data is invalid or the request fails.
            httpx.HTTPStatusError: If the API returns an HTTP error status.
            httpx.RequestError: If a network error occurs during the request.
        """
        try:
            if not data:
                log.error("Los datos de actualización parcial están vacíos.")
                raise BasedException(
                    message="Los datos de actualización parcial no pueden estar vacíos.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )
            # Obtener token válido (refresca si expiró)
            jwt_token = await get_token()

            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }

            response = await self._http_client.patch(
                url=url,
                json=AnyUtils.serialize_dict(data),
                headers=headers
            )
            response.raise_for_status()

            response_data = response.json()
            log.info(f"PATCH request successful: {data}")
            return response_data
        except httpx.HTTPStatusError as e:
            log.error(f"PATCH request failed (status: {e.response.status_code}): {e.response.text}")
            raise
        except httpx.RequestError as e:
            log.error(f"Connection error during PATCH request: {e}")
            raise BasedException(
                message=f"Error de conexión al realizar PATCH: {str(e)}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            log.error(f"Unexpected error during PATCH request: {e}")
            raise BasedException(
                message="Error inesperado al realizar la solicitud PATCH.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


import httpx
from typing import Dict, Any, Optional
from fastapi import Depends, status
from core.settings import get_settings
from core.exceptions.entity_exceptions import BasedException
from utils.logger_util import LoggerUtil

log = LoggerUtil()

class FeedbackService:
    """
    Service for sending notifications to an external API.

    This class handles authentication with an external API to obtain a JWT token and sends
    generic notifications using the provided token and notification data.

    Attributes:
        _jwt_token (Optional[str]): The JWT token used for authenticating requests to the external API.
    """

    def __init__(self):
        self._jwt_token: Optional[str] = None


    async def _get_jwt_token(self) -> str:
        """
        Obtain a new JWT token from the authentication API.

        Sends a POST request to the authentication endpoint with the configured username and password
        to retrieve a JWT token for subsequent API requests.

        Returns:
            str: The obtained JWT token.

        Raises:
            BasedException: If authentication fails or the token is not found in the response.
            httpx.HTTPStatusError: If the API returns an HTTP error status.
            httpx.RequestError: If a network error occurs during the request.
        """
        try:
            auth_payload = {
                "username": get_settings().TG_API_USER,
                "password": get_settings().TG_API_PASS
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(get_settings().TG_API_AUTH, json=auth_payload)
                response.raise_for_status()

                token_data = response.json()
                self._jwt_token = token_data.get("access_token")

                if not self._jwt_token:
                    log.error("El token no se encontró en la respuesta de autenticación.")
                    raise BasedException(
                        message="El token no se encontró en la respuesta de autenticación.",
                        status_code=status.HTTP_401_UNAUTHORIZED
                    )

                log.info("Token JWT obtenido exitosamente.")
                return self._jwt_token
        except httpx.HTTPStatusError as e:
            log.error(f"Fallo en la autenticación a la API (status: {e.response.status_code}): {e.response.text}")
            raise
        except httpx.RequestError as e:
            log.error(f"Error de conexión al autenticar: {e}")
            raise BasedException(
                message=f"Error de conexión al autenticar: {str(e)}",
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        except Exception as e:
            log.error(f"Error inesperado al obtener el token JWT: {e}")
            raise BasedException(
                message="Error inesperado al obtener el token JWT.",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @staticmethod
    async def notify(notification_data: Dict[str, Any],jwt_token: str = Depends(_get_jwt_token)) -> Dict[str, Any]:
        """
        Send a generic notification to an external API.

        Sends the provided notification data in a POST request to the external API, using the
        injected JWT token for authentication.

        Args:
            notification_data (Dict[str, Any]): A dictionary containing the notification data to send.
            jwt_token (str): The JWT token for authenticating the request. Injected via Depends.

        Returns:
            Dict[str, Any]: The response from the external API.

        Raises:
            BasedException: If the notification data is invalid or the request fails.
            httpx.HTTPStatusError: If the API returns an HTTP error status.
            httpx.RequestError: If a network error occurs during the request.
        """
        try:
            if not notification_data:
                log.error("Los datos de notificación están vacíos.")
                raise BasedException(
                    message="Los datos de notificación no pueden estar vacíos.",
                    status_code=status.HTTP_400_BAD_REQUEST
                )

            headers = {
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    get_settings().TG_API_URL,
                    json=notification_data,
                    headers=headers
                )
                response.raise_for_status()

                response_data = response.json()
                log.info(f"Notificación enviada con éxito: {notification_data}")
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
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx

from core.config.settings import get_settings


class ExternalAPI:
    """
        Manages authentication state and HTTP client for API interactions.

        This class retrieves validity external api JWT Token or get a new one through login endpoint.

    """
    def __init__(self):
        self._http_client = httpx.AsyncClient()
        self.token: Optional[str] = None
        self.expires_at: Optional[datetime] = None

    @property
    def http_client(self):
        return self._http_client


auth_state = ExternalAPI()

async def login_and_get_token() -> str:
    """Authenticate with the external API and retrieve a JWT token.

    Sends a POST request to the authentication endpoint with email and password
    credentials to obtain a JWT token for subsequent API requests.

    Returns:
        str: The JWT token from the external API.

    Raises:
        ValueError: If authentication fails or the token is not found in the response.
        httpx.HTTPStatusError: If the API returns an HTTP error status.
        httpx.RequestError: If a network error occurs during the request.
    """
    try:
        response = await auth_state.http_client.post(
            f"{get_settings().TG_API_URL}/account/login",
            json={"email": get_settings().TG_API_USER, "password": get_settings().TG_API_PASS},
            headers={"Content-Type": "application/json"},
        )
        response.raise_for_status()
        data = response.json()

        token = data.get("accessToken")
        if not token:
            raise ValueError("Error Autenticación de API externa: No se encontró token en la respuesta")

        expires_in = data.get("expiresIn", 3600)
        auth_state.token = token
        auth_state.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        return token

    except httpx.HTTPStatusError as e:
        raise httpx.HTTPStatusError(
            f"Error Autenticación de API externa con estado {e.response.status_code}: {e.response.text}",
            request=e.request,
            response=e.response,
        )
    except httpx.RequestError as e:
        raise httpx.RequestError(f"Error de conexión en la autenticación: {str(e)}", request=e.request)


async def get_token() -> str:
    """Retrieve a valid JWT token, refreshing it if necessary.

    Checks if the current token is missing or expired. If so, it obtains a fresh token.
    Otherwise, returns the existing valid token.

    Returns:
        str: A valid JWT token.

    Raises:
        ValueError: If authentication fails or the token is not found.
        httpx.HTTPStatusError: If the API returns an HTTP error status during login.
        httpx.RequestError: If a network error occurs during the login request.
    """
    try:
        if (
            not auth_state.token
            or not auth_state.expires_at
            or datetime.now(timezone.utc) >= auth_state.expires_at - timedelta(minutes=5)
        ):
            return await login_and_get_token()
        return auth_state.token
    except (ValueError, httpx.HTTPStatusError, httpx.RequestError) as e:
        raise e
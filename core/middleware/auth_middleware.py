
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

from core.settings import Settings
from utils.jwt_util import JWTUtil
from utils.logger_util import LoggerUtil
from utils.response_util import ResponseUtil

# Env variables Setup
API_VERSION = Settings().API_VERSION

# Utils Setup
json_response = ResponseUtil().json_response
log = LoggerUtil()


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Class responsible for handling authentication middleware.

    This middleware intercepts incoming requests to enforce authentication by verifying
    JWT tokens. Requests to public paths are allowed without authentication.

    If a request does not contain a valid JWT token in the `Authorization` header,
    an HTTP 401 Unauthorized error is returned.

    Class Args:
        None
    """

    async def dispatch(self, request: Request, call_next):
        """
        Public asynchronous method responsible for processing incoming requests.

        This method verifies if a request requires authentication and checks
        the validity of the JWT token.

        Args:
            request (Request): The incoming HTTP request to be processed.
            call_next: The next middleware or route handler in the pipeline.

        Returns:
            Response: The processed response after authentication.

        Raises:
            HTTPException: If the authentication token is missing or invalid.
            Exception: If an unexpected error occurs during processing.
        """

        try:

            PUBLIC_PATHS = [
                f"/api-{API_VERSION}/login",
                f"/api-{API_VERSION}/register",
                "/docs",
                "/openapi.json",
            ]

            if any(request.url.path.startswith(path) for path in PUBLIC_PATHS):
                response = await call_next(request)
                return response

            auth_header = request.headers.get("Authorization")

            if not auth_header or not auth_header.startswith("Bearer "):
                raise HTTPException(
                    status_code=401, detail="Token not provided!"
                )

            token = auth_header.split(" ")[1]

            JWTUtil.verify_token(token)

            request.state.token = token

            response = await call_next(request)

            if response is None:
                return json_response(500, "Internal server error")

            return response

        except HTTPException as error:
            log.error(f"Token validation error: {error.detail}")
            return json_response(error.status_code, str(error.detail))

        except Exception as error:
            log.error(f"Unexpected error in JWT Middleware: {error}")
            return json_response(500, str(error))
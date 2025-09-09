from http.client import HTTPException
from urllib import request

from fastapi.security import HTTPBearer
from core.di.repository_injection import get_user_repository
from core.di.service_injection import get_user_service
from services.usuarios_service import UsuariosService
from utils.jwt_util import JWTUtil
from repositories.usuarios_repository import UsuariosRepository
from services.auth_service import AuthService
from fastapi import Depends, status
from core.exceptions.auth_exception import InvalidCredentialsException, InvalidTokenCredentialsException
from core.config.settings import get_settings
from core.config import context
from starlette.types import ASGIApp
from fastapi import Request
from http import HTTPStatus
from starlette.responses import Response, JSONResponse


from starlette.middleware.base import BaseHTTPMiddleware

from utils.logger_util import LoggerUtil
log = LoggerUtil()

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):
    PUBLIC_PATHS = {
        "/docs",
        "/openapi/v1.json",
        "/redoc",
        "/api/v1/auth",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
    }

    def __init__(self, app: ASGIApp ):
        super().__init__(app)
    """
    Class responsible for handling auth middleware.

    This middleware intercepts incoming HTTP request and manages the authentication flow and pass to the context.

    If an error occurs during request processing, the middleware raise error details.

    Class Args:
        None
    """

    async def dispatch(self, req: Request, call_next,
                       user_service: UsuariosService = Depends(get_user_service)) -> Response:
        # Check if the request path is public
        if req.url.path in self.PUBLIC_PATHS:
            log.info(f"Bypassing authentication for public path: {req.url.path}")
            return await call_next(req)

        try:
            # Check access permissions for non-public paths
            check_access: Response | None = await self.__check_access(req, user_service)
            if check_access is not None:
                return check_access

            # Proceed to the next middleware or endpoint
            return await call_next(req)

        except InvalidTokenCredentialsException as ite:
            log.error("Invalid Token {}", str(ite))
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid token"},
                headers={"WWW-Authenticate": "Bearer"},
            )
        except InvalidCredentialsException as ice:
            log.error("Invalid Credentials {}", str(ice))
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": str(ice)},
            )
        except Exception as e:
            log.error("Error in AuthMiddleware: {}", str(e))
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": f"Server error: {str(e)}"},
            )

    @staticmethod
    async def __check_access(req: Request, user_service: UsuariosService) -> Response | None:
        try:
            # Extract the token from the Authorization header
            auth_header: str = req.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Authorization header missing or malformed"}
                )

            access_token = auth_header.split(" ")[1]

            # Decode the access token
            payload = JWTUtil.verify_token(access_token)
            username: str | None = payload.get("sub")
            userid: str | None = payload.get("uid")

            if username is None:
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content={"detail": "Invalid Client ID"}
                )

            # Log username for debugging
            log.info(f"Fetching user with username: {username}")

            # Fetch user from repository
            #user = await user_service.get_username(username)
            #if user is None:
               # log.error(f"User not found:")
               # return JSONResponse(
               #     status_code=status.HTTP_401_UNAUTHORIZED,
               #     content={"detail": "Invalid credentials"}
              #  )

            # Set user_id in context
            if username == get_settings().API_USER_ADMINISTRATOR:
                user_id = 999
            else:
                if userid is None:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={"detail": "Invalid Access Token"}
                    )
                user_id = userid

            context.current_user_id.set(user_id)
            log.info(f"User authenticated: {username}, user_id: {user_id}")
            return None

        except InvalidTokenCredentialsException as ite:
            log.error(f"Invalid token: {str(ite)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": str(ite)}
            )
        except InvalidCredentialsException as e:
            log.error(f"Invalid credentials: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": str(e)}
            )
        except Exception as e:
            log.error(f"Error in __check_access: {str(e)}", exc_info=True)
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"detail": f"Error: {str(e)}"}
            )
        # token = request.headers.get("Authorization")
        # user_id = None
        #
        # if token and token.startswith("Bearer "):
        #     token = token.split(" ")[1]
        #     try:
        #         payload = JWTUtil.verify_token(token)
        #         username: str = payload.get("sub")
        #         userid: str = payload.get("uid")
        #
        #         if username is None:
        #             context.current_user_id.set(None)
        #             raise InvalidTokenCredentialsException()
        #
        #         if username == get_settings().API_USER_ADMINISTRATOR:
        #             user_id = 999
        #         else:
        #             user_id = userid
        #
        #         context.current_user_id.set(user_id)
        #         response = await call_next(request)
        #         return response
        #
        #     except InvalidTokenCredentialsException as e:
        #         raise e
        #     except Exception as e:
        #         log.error(f"Error al obtener usuario actual: {e}")
        #         raise BasedException("Error inesperado al obtener usuario actual")
        # # Set the user ID for the request's lifespan
        # context.current_user_id.set(user_id)
        #
        # response = await call_next(request)
        # return response




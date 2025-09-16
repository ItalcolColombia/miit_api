from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


from fastapi.security import HTTPBearer
from core.di.service_injection import get_user_service
from core.exceptions.base_exception import BasedException
from services.usuarios_service import UsuariosService
from utils.jwt_util import JWTUtil
from fastapi import Depends, status
from core.exceptions.auth_exception import InvalidCredentialsException, InvalidTokenCredentialsException
from core.config.settings import get_settings
from core.config import context
from starlette.types import ASGIApp
from fastapi import Request
from http import HTTPStatus
from starlette.responses import Response, JSONResponse



from utils.logger_util import LoggerUtil
from utils.response_util import ResponseUtil

# Env variables Setup
API_VERSION = get_settings().API_V1_STR
# Utils Setup
json_response = ResponseUtil().json_response

log = LoggerUtil()

security = HTTPBearer()


class AuthMiddleware(BaseHTTPMiddleware):


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
        try:
            public_paths = [
                f"/api/{API_VERSION}/auth",
                "/docs",
                "/redoc",
                f"/openapi/{API_VERSION}.json",
            ]

            # Public patch Checking
            if any(req.url.path.startswith(path) for path in public_paths):
                return await call_next(req)

            # Check access permissions for non-public paths
            check_access: Response | None = await self.__check_access(req, user_service)
            if check_access is not None:
                return check_access

            # Proceed to the next middleware or endpoint
            return await call_next(req)


        except (InvalidTokenCredentialsException, InvalidCredentialsException):
            pass
        except Exception as e:
            log.error("Error in AuthMiddleware:", str(e))
            return json_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Error servidor: {str(e)}",
            )

    @staticmethod
    async def __check_access(req: Request, user_service: UsuariosService) -> Response | None:
        try:
            # Extract the token from the Authorization header
            auth_header: str = req.headers.get("Authorization")
            if not auth_header or not auth_header.startswith("Bearer "):
                return json_response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Falta o está mal formado el encabezado de autorización",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            access_token = auth_header.split(" ")[1]

            # Decode the access token
            payload = JWTUtil.verify_token(access_token)
            username: str | None = payload.get("sub")
            userid: str | None = payload.get("uid")

            if username is None:
                return json_response(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    message="Usuario no valido",
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
                    return json_response(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        message="Token de acesso invalido"
                    )
                user_id = userid

            context.current_user_id.set(user_id)
            log.info(f"User authenticated: {username}, user_id: {user_id}")
            return None

        except BasedException as e:
            log.error(f"Token verify error: {str(e.detail)}")
            return json_response(
                status_code= e.status_code,
                message = str(e.detail),
            )
        except Exception as e:
            log.error(f"Error in __check_access: {str(e)}", exc_info=True)
            return json_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                message=f"Error: {str(e)}"
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




from contextlib import asynccontextmanager
from urllib.request import Request

import uvicorn

from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination

from core.exceptions.base_exception import BasedException
from core.middleware.auth_middleware import AuthMiddleware
from core.middleware.error_middleware import ErrorMiddleware
from core.middleware.time_middleware import TimeMiddleware
from api.v1.routes import routers as v1_routers
from core.config.settings import get_settings
from core.handlers.exception_handler import ExceptionHandler
from core.middleware.logger_middleware import LoggerMiddleware
from utils.database_util import DatabaseUtil
from utils.logger_util import LoggerUtil
from utils.message_util import MessageUtil

# Env variables Setup
API_HOST = get_settings().API_HOST
API_PORT = get_settings().API_PORT
API_VERSION_STR = get_settings().API_V1_STR
API_VERSION = get_settings().API_VERSION_NUM
API_STAGE = get_settings().API_LOG_LEVEL
ALLOWED_HOSTS = get_settings().ALLOWED_HOSTS

SECRET_KEY = get_settings().JWT_SECRET_KEY

# Logger Setup
log = LoggerUtil()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    await startup_event()
    yield
    # Shutdown logic
    log.info("Application shutdown")
app = FastAPI(
    title="Servicio Interconsulta MIIT",
    description="API para el manejo de información en el repositorio central por parte de los stackholders: operador portuario y automatizador. ",
    version=API_VERSION,
    openapi_tags=[
        {"name": "Autenticación", "description": "Operaciones relacionadas con la autenticación"},
        {"name": "Automatizador", "description": "Operaciones de interés para la automatización."},
        {"name": "Integrador", "description": "Operaciones de interés para el operador portuario."},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi/v1.json",
    swagger_ui_parameters={
        "filter": True,
        "defaultModelsExpandDepth": -1,
        "docExpansion": "none"
    },
    default_response_class=JSONResponse,
    lifespan=lifespan
)


# Manejadores de excepciones
app.add_exception_handler(BasedException, ExceptionHandler.http_exception_handler)
app.add_exception_handler(StarletteHTTPException, ExceptionHandler.http_exception_handler)
app.add_exception_handler(RequestValidationError, ExceptionHandler.json_decode_error_handler)


# Middlewares
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in ALLOWED_HOSTS] or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(AuthMiddleware)
app.add_middleware(ErrorMiddleware)
app.add_middleware(LoggerMiddleware)
app.add_middleware(TimeMiddleware)

# Rutas
app.include_router(v1_routers, prefix="/api/" + API_VERSION_STR)

# Libreria de paginación
add_pagination(app)


#Urls
@app.get('/', include_in_schema=False)
async def root():
    return JSONResponse({'service': app.title, 'version': API_VERSION_STR, 'env': API_STAGE})

async def startup_event():
    """
        Application startup sequence.

        This section ensures that essential configurations are checked before
        running the FastAPI server.
    """
    # On Startup Message
    MessageUtil().on_startup()

    # # Check ENV variables
    # DotEnvUtil().check_dot_env()

    # Check Database Connection
    await DatabaseUtil().check_connection()

if __name__ == "__main__":
    width = 80
    border = "=" * width

    uvicorn.run("main:app", host=API_HOST, port=API_PORT, log_config=None)

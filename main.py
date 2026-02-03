from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from api.v1.routes import routers as v1_routers
from core.config.settings import get_settings
from core.exceptions.base_exception import BasedException
from core.handlers.exception_handler import ExceptionHandler
from core.middleware.auth_middleware import AuthMiddleware
from core.middleware.error_middleware import ErrorMiddleware
from core.middleware.logger_middleware import LoggerMiddleware
from core.middleware.time_middleware import TimeMiddleware
from utils.database_util import DatabaseUtil
from utils.logger_util import LoggerUtil
from utils.message_util import MessageUtil
from utils.time_util import get_app_timezone, now_utc, now_local

# Env variables Setup
API_HOST = get_settings().API_HOST
API_PORT = get_settings().API_PORT
API_VERSION_STR = get_settings().API_V1_STR
API_VERSION = get_settings().API_VERSION_NUM
API_STAGE = get_settings().API_LOG_LEVEL
ALLOWED_HOSTS = get_settings().ALLOWED_HOSTS
CORS_ORIGINS = get_settings().CORS_ORIGINS

SECRET_KEY = get_settings().JWT_SECRET_KEY

# Logger Setup
log = LoggerUtil()

@asynccontextmanager
async def lifespan(app: FastAPI):

    try:
        # Startup logic
        log.info("Application startup")
        # Log timezone and current times for debugging
        try:
            tz = get_app_timezone()
            log.info(f"APP_TIMEZONE={tz}")
            log.info(f"now_utc={now_utc().isoformat()} now_local={now_local().isoformat()}")
        except Exception as e:
            log.warning(f"No se pudo leer APP_TIMEZONE en startup: {e}")
        await startup_event()
        yield
    finally:
        # Shutdown
        log.info("Application shutdown")
app = FastAPI(
    title="Servicio Interconsulta MIIT",
    description="API para el manejo de información en el repositorio central por parte de los stackholders: operador portuario y automatizador. ",
    version=API_VERSION,
    openapi_tags=[
        {"name": "Autenticación", "description": "Operaciones relacionadas con la autenticación"},
        {"name": "Automatizador", "description": "Operaciones de interés para la automatización."},
        {"name": "Integrador", "description": "Operaciones de interés para el operador portuario."},
        {"name": "Reportes", "description": "Operaciones relacionadas con la generación de reportes."},
        {"name": "Admin - Reportes", "description": "Operaciones de administración relacionadas con los reportes."},
        {"name": "Admin - Roles", "description": "Operaciones de administración relacionadas con los roles."},
        {"name": "Administrador", "description": "Operaciones de administración del sistema."},
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
# IMPORTANTE: Los middlewares se ejecutan en orden INVERSO al que se agregan
# El último agregado se ejecuta primero en la solicitud entrante
# Por eso CORSMiddleware debe ser el ÚLTIMO en agregarse para procesar primero las solicitudes preflight

app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(AuthMiddleware)
app.add_middleware(ErrorMiddleware)
app.add_middleware(LoggerMiddleware)
app.add_middleware(TimeMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Rutas
app.include_router(v1_routers, prefix="/api/" + API_VERSION_STR)

# Libreria de paginación
add_pagination(app)


#Urls
@app.get('/', include_in_schema=False)
async def root():
    return JSONResponse({'service': 'MIIT_API', 'version': API_VERSION_STR, 'env': API_STAGE})

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

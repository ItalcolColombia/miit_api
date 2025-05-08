
import uvicorn

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi_pagination import add_pagination

from core.middleware.time_middleware import ProcessTimeHeaderMiddleware
from api.v1.routes import routers as v1_routers
from core.settings import Settings
from core.exceptions.exception_handler import ExceptionHandler
from core.middleware.logger_middleware import LoggerMiddleware
from utils.database_util import DatabaseUtil
from utils.dot_env_util import DotEnvUtil
from utils.logger_util import LoggerUtil
from utils.message_util import MessageUtil


# Env variables Setup
API_HOST = Settings().API_HOST
API_PORT = Settings().API_PORT
API_VERSION_STR = Settings().API_V1_STR
API_VERSION = Settings().API_VERSION
API_STAGE = Settings().API_LOG_LEVEL

SECRET_KEY = Settings().JWT_SECRET_KEY

app = FastAPI(

    title= "Servicio Interconsulta MIIT",
    description="API para el manejo de información en el repositorio central por parte de los stackholders: operador portuario y automatizador. ",
    version=API_VERSION,
     openapi_tags=[
        {"name": "Autenticación", "description": "Operaciones relacionadas con la autenticación"},
        {"name": "Automatizador", "description": "Operaciones de interés para la automatización."},
        {"name": "Integrador", "description": "Operaciones de interés para el operador portuario."},
    ],
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={
        "filter": True,
        "defaultModelsExpandDepth": -1,
        "docExpansion": "none"  
    },
    default_response_class=JSONResponse
 )


#Cargar estaticos

#app.mount("/static", StaticFiles(directory="static"), name="static")


# Logger Setup

log = LoggerUtil()



#Exceptions Handlers
app.add_exception_handler(HTTPException, ExceptionHandler.http_exception_handler)  # type: ignore
app.add_exception_handler(RequestValidationError, ExceptionHandler.json_decode_error_handler)  # type: ignore


# Middlewares
app.add_middleware(LoggerMiddleware)
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(ProcessTimeHeaderMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas
app.include_router(v1_routers, prefix="/api/" + API_VERSION_STR)

# Libreria de paginación
add_pagination(app)

#Urls
@app.get('/', include_in_schema=False)
async def root():
    return JSONResponse({'service': app.title, 'version': API_VERSION_STR, 'env': API_STAGE})


# @app.get("/docs", include_in_schema=False)
# async def custom_swagger_ui_html():
#     return get_swagger_ui_html(
#         openapi_url=app.openapi_url,
#         title= "MIIT API - Swagger UI",
#         swagger_favicon_url="/static/favicon.png",  # Ruta a tu favicon
#     )

@app.on_event("startup")
async def startup_event():
    """
        Application startup sequence.

        This section ensures that essential configurations are checked before
        running the FastAPI server.
    """
    # On Startup Message
    MessageUtil().on_startup()

    # Check ENV variables
    DotEnvUtil().check_dot_env()

    # Check Database Connection
    await DatabaseUtil().check_connection()

@app.on_event("shutdown")
async def shutdown_event():

    print("Application shutdown")


if __name__ == "__main__":
    width = 80
    border = "=" * width

    uvicorn.run("main:app", host=API_HOST, port=API_PORT, log_config=None)
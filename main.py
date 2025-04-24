from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from core.middleware.time_middleware import ProcessTimeHeaderMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.middleware.gzip import GZipMiddleware
from api.v1.routes import routers as v1_routers
from core.settings import Settings
from core.middleware.auth_middleware import AuthMiddleware
from core.middleware.logger_middleware import LoggerMiddleware
from utils.database_util import DatabaseUtil
from utils.dot_env_util import DotEnvUtil
from utils.logger_util import LoggerUtil
from utils.message_util import MessageUtil
import uvicorn

# Env variables Setup
API_HOST = Settings().API_HOST
API_NAME = Settings().API_NAME
API_PORT = Settings().API_PORT
API_VERSION = Settings().API_VERSION
SECRET_KEY = Settings().JWT_SECRET_KEY


app = FastAPI(

    title= API_NAME,
    description="API interconsulta de la data almacenada en el repositorio central por parte de los stackholders: operador portuario y automatizador. ",
    version=API_VERSION,
    docs_url="/docs",   # Swagger UI endpoint
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    docExpansion="None"
 )

# Middlewares
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

app.add_middleware(ProcessTimeHeaderMiddleware)

app.add_middleware(LoggerMiddleware)
#app.add_middleware(AuthMiddleware)

app.include_router(v1_routers, prefix="/api/"+API_VERSION)

app.get("/")
async def root():
    return {"message": "MIIT API"}



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
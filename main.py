from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from api.v1.routes import routers as v1_routers
import uvicorn



app = FastAPI(

    title="API_MIIT BDC API",
    description="API dispuesta para el flujo de información entre el ERP y ETL con la Base de Datos Central. ",
    version="0.0.5",
    docs_url="/docs",   # Swagger UI endpoint
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    swagger_ui_parameters={"defaultModelsExpandDepth": -1},
    docExpansion="None"
 )

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

app.include_router(v1_routers, prefix="/api/v1")

app.get("/")
async def root():
    return {"message": "MIIT API"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="localhost",
        port=8000,
        reload=True
    )
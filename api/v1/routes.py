from fastapi import APIRouter

from api.v1.endpoints import auth, etl, operador, reportes
from api.v1.endpoints.admin.admin_reportes import router as admin_reportes_router

routers = APIRouter()

def include_main_routes():
    """Include the main application routes."""
    router_list: list[APIRouter] = [
        auth.router,
        etl.router,
        operador.router,
        reportes.router,
        admin_reportes_router,
    ]
    for router in router_list:
        routers.include_router(router)

# Apply the route inclusions
include_main_routes()
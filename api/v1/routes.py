from fastapi import APIRouter

from api.v1.endpoints import  auth, etl, operador
from api.v1.endpoints.admin import admin

routers = APIRouter()

def include_main_routes():
    """Include the main application routes."""
    router_list = [auth.router, etl.router, operador.router]
    for router in router_list:
        routers.include_router(router)

# Apply the route inclusions
include_main_routes()




from fastapi import APIRouter

from api.v1.endpoints import  auth, etl, operador

routers = APIRouter()
router_list = [auth.router, etl.router, operador.router]

for router in router_list:
    routers.include_router(router)

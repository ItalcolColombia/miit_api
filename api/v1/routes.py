from fastapi import APIRouter

from api.v1.endpoints.auth import router as auth_router
from api.v1.endpoints.users import router as user_router
from api.v1.endpoints.etl import router as etl_router

routers = APIRouter()
router_list = [auth_router, user_router]

for router in router_list:
    routers.include_router(router)

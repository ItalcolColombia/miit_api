from fastapi import Depends
from repositories.base_repository import IRepository
from repositories.user_repository import UsuarioRepository
from services.user_service import UserService
from services.employee_service import EmployeeService
from services.auth_service import AuthService
from services.employee_reports_service import EmployeeReportsService
from .repositories import get_user_repository, get_employee_repository

async def get_user_service(
    user_repository: UsuarioRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(user_repository)

async def get_employee_service(
    employee_repository: IRepository = Depends(get_employee_repository)
) -> EmployeeService:
    return EmployeeService(employee_repository)

async def get_auth_service(
    user_repository: IRepository = Depends(get_user_repository)
) -> AuthService:
    return AuthService(user_repository)

async def get_employee_reports_service(
    employee_repository: IRepository = Depends(get_employee_repository)
) -> EmployeeReportsService:
    return EmployeeReportsService(employee_repository)
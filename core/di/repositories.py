from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from repositories.base_repository import IRepository
from repositories.user_repository import UsuarioRepository
from repositories.employee_repository import EmployeeRepository
from database.models import Usuarios, EmployeeModel  # Import your models
from schemas.usuarios_schema import UsuarioResponse  # Import your schemas
from schemas.employee import EmployeeBase
from .database import get_db

async def get_user_repository(
    session: AsyncSession = Depends(get_db)
) -> UsuarioRepository:
    return UsuarioRepository(Usuarios, UsuarioResponse, session)

async def get_employee_repository(
    session: AsyncSession = Depends(get_db)
) -> EmployeeRepository:
    return EmployeeRepository(EmployeeModel, EmployeeBase, session)
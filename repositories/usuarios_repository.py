from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from fastapi import HTTPException, status
from repositories.base_repository import IRepository
from schemas.usuarios_schema import UsuariosResponse, UsuariosResponseWithPassword, UsuarioCreate, UsuarioUpdate
from database.models import Usuarios, Roles

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class UsuariosRepository(IRepository[Usuarios, UsuariosResponse]):
    db: AsyncSession


    def __init__(self, model: type[Usuarios], schema: type[UsuariosResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db) 
    
    async def get_by_username(self, username:str) -> Optional[UsuariosResponse]:

        try:
            query = select(Usuarios).options(joinedload(Usuarios.rol)).where(Usuarios.nick_name == username)
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return None

            return UsuariosResponse.model_validate(user)
        except ProgrammingError as e:
            log.error(f"Error al consultar a la BD: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de configuración de la base de datos. Las tablas necesarias no están presentes. Inicializar la base de datos."
            ) from e
        except SQLAlchemyError as e:
            log.error(f"No hay conexión con la BD: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de conexión con la base de datos. Inténtalo de nuevo más tarde."
            ) from e
        except Exception as e:
            log.error(f"Ocurrió un error inesperado en la consulta: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Ocurrió un error inesperado en la consulta."
            ) from e

    async def get_by_email(self, email: str) -> Optional[UsuariosResponse]:
       query = select(Usuarios).where(Usuarios.email == email)
       result = await self.db.execute(query)
       user = result.scalar_one_or_none()

       if not user:
          return None
       return UsuariosResponse.model_validate(user)


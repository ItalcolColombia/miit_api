from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import ProgrammingError, SQLAlchemyError
from fastapi import HTTPException, status
from repositories.base_repository import IRepository
from schemas.usuarios_schema import UsuariosResponse, VUsuariosRolResponse, VRolesPermResponse
from database.models import Usuarios, VUsuariosRoles, VRolesPermisos

from utils.logger_util import LoggerUtil

log = LoggerUtil()


class UsuariosRepository(IRepository[Usuarios, UsuariosResponse]):
    db: AsyncSession

    def __init__(self, model: type[Usuarios], schema: type[UsuariosResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db)

    async def get_by_username(self, username: str) -> Optional[VUsuariosRolResponse]:

        try:
            query = (
                select(VUsuariosRoles)
                .where(VUsuariosRoles.nick_name == username)
            )
            result = await self.db.execute(query)
            user = result.scalar_one_or_none()

            if not user:
                return None

            return VUsuariosRolResponse.model_validate(user)
        except ProgrammingError as e:
            log.error(f"Error al consultar a la BD: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de configuración del modelo de datos."
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

    async def get_rol_permission(self, rol_id: int) -> Optional[VRolesPermResponse]:
        try:
            query = (
                select(VRolesPermisos)
                .where(VRolesPermisos.rol_id == rol_id)
            )
            result = await self.db.execute(query)
            permisos = result.scalars().all()

            if not permisos:
                return None

            return [VRolesPermResponse.model_validate(permiso) for permiso in permisos]

        except ProgrammingError as e:
            log.error(f"Error al consultar a la BD: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error de configuración del modelo de datos asociados a los roles."
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

    async def get_by_email(self, email: str) -> Optional[VUsuariosRolResponse]:
        query = select(VUsuariosRoles).where(Usuarios.email == email)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None
        return VUsuariosRolResponse.model_validate(user)




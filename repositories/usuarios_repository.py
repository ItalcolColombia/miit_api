from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select,func
from repositories.base_repository import IRepository
from schemas.usuarios_schema import UsuariosResponse, UsuariosResponseWithPassword, UsuarioCreate, UsuarioUpdate
from database.models import Usuarios, Roles


class UsuariosRepository(IRepository[Usuarios, UsuariosResponse]):
    db: AsyncSession


    def __init__(self, model: type[Usuarios], schema: type[UsuariosResponse], db: AsyncSession) -> None:
        self.db = db
        super().__init__(model, schema, db) 
    
    async def get_by_username(self, username:str) -> Optional[UsuariosResponse]:
        query = select(Usuarios).where(Usuarios.nick_name == username)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None

        return UsuariosResponse.model_validate(user)

    async def get_by_email(self, email: str) -> Optional[UsuariosResponse]:
       query = select(Usuarios).where(Usuarios.email == email)
       result = await self.db.execute(query)
       user = result.scalar_one_or_none()

       if not user:
          return None
       return UsuariosResponse.model_validate(user)


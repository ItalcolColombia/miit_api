from typing import List, Optional
from sqlalchemy import func
from utils.any_utils import AnyUtils
from repositories.usuarios_repository import UsuariosRepository
from core.exceptions.entity_exceptions import EntityAlreadyRegisteredException
from schemas.usuarios_schema import UsuariosResponse, UsuarioCreate, UsuarioUpdate

class UsuariosService:

    def __init__(self, usuario_repository: UsuariosRepository) -> None:
        self._repo = usuario_repository


    async def validate_username(self, username: str) -> None:
        if await self.get_username(username):
            raise EntityAlreadyRegisteredException('nick_name')
        
    async def get_username(self, username: str) -> UsuariosResponse | None:
        return await self._repo.get_by_username(username)
    
    async def get_user(self, usr_id: int) -> Optional[UsuariosResponse]:
        return await self._repo.get_by_id(usr_id)

    async def get_all_users(self) -> List[UsuariosResponse]:
        return await self._repo.get_all()

    async def get_paginated_users(self, skip_number: int, limit_number: int):
        return await self._repo.get_all_paginated(skip=skip_number, limit=limit_number)
    
    async def create_user(self, user: UsuarioCreate) -> UsuariosResponse:

        # Validamos si el usuario existe
        await self.validate_username(user.nick_name)

        # Se hashea la contraseña
        user.clave = AnyUtils.generate_password_hash(user.clave)
        user.fecha_modificado = func.now()

        # Se crea el usuario
        return await self._repo.create(user)
    

    async def update_user(self, usr_id: int, user: UsuarioUpdate) -> Optional[UsuariosResponse]:
        return await self._repo.update(usr_id, user)
    
    async def delete_user(self, usr_id: int) -> bool:
        return await self._repo.delete(usr_id)
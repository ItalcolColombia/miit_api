from typing import List, Optional
from sqlalchemy import func
from utils.any_utils import AnyUtils
from repositories.user_repository import UsuarioRepository
from core.exceptions.entity_exceptions import EntityAlreadyRegisteredException
from schemas.usuarios_schema import UsuarioResponse, UsuarioCreate, UsuarioUpdate

class UserService:

    def __init__(self, usuario_repository: UsuarioRepository) -> None:
        self._repo = usuario_repository


    async def validate_username(self, username: str) -> None:
        if await self.get_username(username):
            raise EntityAlreadyRegisteredException('nick_name')
        
    async def get_username(self, username: str) -> UsuarioResponse | None:
        return await self._repo.get_by_username(username)
    
    async def get_user(self, usr_id: int) -> Optional[UsuarioResponse]:
        return await self._repo.get_by_id(usr_id)

    async def get_all_users(self) -> List[UsuarioResponse]:
        return await self._repo.get_all()
    
    async def create_user(self, user: UsuarioCreate) -> UsuarioResponse:

        # Validamos si el usuario existe
        await self.validate_username(user.nick_name)

        # Se hashea la contraseña
        user.clave = AnyUtils.generate_password_hash(user.clave)
        user.fecha_modificado = func.now()

        # Se crea el usuario
        return await self._repo.create(user)
    

    async def update_user(self, usr_id: int, user: UsuarioUpdate) -> Optional[UsuarioResponse]:
        return await self._repo.update(usr_id, user)
    
    async def delete_user(self, usr_id: int) -> bool:
        return await self._repo.delete(usr_id)
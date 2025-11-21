from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from schemas.base_schema import BaseSchema


class UsuariosResponse(BaseSchema):
    id: int
    nick_name: str
    full_name: str
    cedula: int
    email: str
    clave: str
    rol_id: int
    estado: bool = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
     from_attributes = True



class UsuarioCreate(BaseSchema):
    nick_name: str = Field(..., min_length=5, max_length=10)
    full_name: str = Field(..., min_length=20, max_length=100)
    cedula: int  # Required field
    email: str = Field(..., min_length=5, max_length=100)
    clave: str
    rol_id: int
    estado: bool = False
    fecha_hora: Optional[datetime] = None
    usuario_id: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "nick_name": "sysadmin",
                "full_name": "Administrador del Sistema",
                "cedula": "2222222",
                "email" : "sysadmin@mail.com",
                "clave" : "admin1234",
                "rol_id" : "1",
                "estado": "true"
            }
        }
    

class UsuarioUpdate(BaseSchema):
    nick_name: str = Field(..., min_length=5, max_length=10)
    full_name: str = Field(..., min_length=20, max_length=100)
    cedula: int  # Required field
    email: str = Field(..., min_length=5, max_length=100)
    clave: str
    rol_id: int
    estado: bool = False


class UsuariosResponseWithPassword(UsuariosResponse):
    clave: str

class Token(BaseSchema):
    access_token: str
    token_type: str

class UserAuth(BaseSchema):
    nick_name: str = "nombre_usuario"
    clave: str = "P4$$w0rd"

class VUsuariosRolResponse(BaseModel):
    id: int
    nick_name: str
    full_name: str
    cedula: int
    email: str
    clave: str
    rol_id: int
    rol: str
    recuperacion: Optional[str]= None
    estado: Optional[bool] = False
    estado_rol: Optional[bool] = False
    fecha_hora: datetime
    usuario_id: int
    usuario: str

    class Config:
        from_attributes = True

class VRolesPermResponse(BaseModel):
    rol_id: int
    rol: str
    permiso_id: int
    permiso: str
    fecha_hora: datetime
    usuario_id: int
    usuario: str

    class Config:
        from_attributes = True



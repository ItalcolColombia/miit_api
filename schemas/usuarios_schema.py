from pydantic import BaseModel, EmailStr, Field
from schemas.base_schema import BaseSchema
from typing import Optional
from datetime import datetime  


class UsuariosResponse(BaseSchema):
    id: int
    nick_name: str
    full_name: str
    cedula: int
    email: str
    clave: str
    rol_id: int
    estado: bool = False


   

    # class Config:
    #     from_attributes = True

class UsuarioCreate(BaseSchema):
    nick_name: str = Field(..., min_length=5, max_length=10)
    full_name: str = Field(..., min_length=20, max_length=100)
    cedula: int  # Required field
    email: str = Field(..., min_length=5, max_length=100)
    clave: str
    fecha_modificado: Optional[datetime] = None
    rol_id: int
    estado: bool = False

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

class UsuarioResponseWithToken(BaseSchema):
    access_token: str
    refresh_token :str
    #token_type: str = "bearer"
    expires_in: int

class UserAuth(BaseSchema):
    nick_name: str = "admin"
    clave: str = "admin"


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
    rol_nombre: str  
    estado: bool = False

    class Config:
     from_attributes = True

    @classmethod
    def model_validate(cls, obj):
        kwargs = {
            "id": obj.id,
            "nick_name": obj.nick_name,
            "full_name": obj.full_name,
            "cedula": obj.cedula,
            "email": obj.email,
            "clave": obj.clave,
            "rol_id": obj.rol_id,
            "rol_nombre": obj.rol.nombre if obj.rol else None,  
            "estado": obj.estado
        }
        return cls(**kwargs)

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

class Token(BaseSchema):
    access_token: str
    token_type: str

class UserAuth(BaseSchema):
    nick_name: str = "admin"
    clave: str = "admin"


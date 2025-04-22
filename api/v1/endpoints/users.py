from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from core.di.service_injection import get_user_service
from services.usuarios_service import UsuariosService
from api.v1.middleware.auth_middleware import get_current_user
from schemas.usuarios_schema import UsuarioCreate, UsuariosResponse, UsuarioUpdate

router = APIRouter(prefix="/usuarios", tags=["Usuarios - Crud"])

@router.post("/create", response_model=UsuariosResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
	user_data: UsuarioCreate,
	user_service: UsuariosService = Depends(get_user_service)
):
	created_user = await user_service.create_user(user_data)
	return created_user

@router.get("/{user_id}", response_model=UsuariosResponse)
async def get_user(
	user_id: int,
	user_service: UsuariosService = Depends(get_user_service),
	current_user: UsuariosResponse = Depends(get_current_user)
):
	user = await user_service.get_user(user_id)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	return user

@router.get("/", response_model=List[UsuariosResponse])
async def list_users(
	user_service: UsuariosService = Depends(get_user_service),
	current_user: UsuariosResponse = Depends(get_current_user)
):
	all_users = await user_service.get_all_users()
	return all_users

@router.put("/{user_id}", response_model=UsuariosResponse)
async def update_user(
	user_id: int,
	user_data: UsuarioUpdate,
	user_service: UsuariosService = Depends(get_user_service),
	current_user: UsuariosResponse = Depends(get_current_user)
):
	user = await user_service.update_user(user_id, user_data)
	if not user:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
	user_id: int,
	user_service: UsuariosService = Depends(get_user_service),
	current_user: UsuariosResponse = Depends(get_current_user)
):
	user_deleted = await user_service.delete_user(user_id)
	if not user_deleted:
		raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
	return {"message": "User deleted successfully"}
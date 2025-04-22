from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from core.di.service_injection import get_flotas_service, get_mat_service, get_alm_service, get_mov_service, \
    get_pesadas_service, get_transacciones_service
from schemas.almacenamientos_schema import AlmacenamientoResponse
from schemas.materiales_schema import MaterialesResponse
from schemas.movimientos_schema import MovimientosResponse
from schemas.pesadas_schema import PesadaResponse
from schemas.transacciones_schema import TransaccionResponse
from services.almacenamientos_service import AlmacenamientosService
from services.flotas_service import FlotasService
from services.movimientos_service import MovimientosService
from services.transacciones_service import TransaccionesService
from services.pesadas_service import PesadasService
from api.v1.middleware.auth_middleware import get_current_user
from schemas.usuarios_schema import UsuariosResponse
from schemas.flotas_schema import (
    FlotasResponse,
    FlotaCreate,
    FlotaUpdate,
    FlotasActResponse
)
from services.materiales_service import MaterialesService

router = APIRouter(prefix="/scada", tags=["SCADA - Operaciones de interés para la automatización"])



# @router.get("/flotas_listado/", response_model=List[FlotaResponse])
# async def list_flotas(
#     flotas_service: FlotasService = Depends(get_flotas_service),
#     current_user: UsuarioResponse = Depends(get_current_user)
# ):
#     all_flotas = await flotas_service.get_all_flotas()
#     return all_flotas
#
# @router.post("/", response_model=FlotaResponse, status_code=status.HTTP_201_CREATED)
# async def create_flota(
#     flota: FlotaCreate,
#     service: FlotasService = Depends(get_flotas_service),
#     current_user: UsuarioResponse = Depends(get_current_user)
# ):
#     created_flota = await service.create_flota(flota)
#     return created_flota

@router.get("/AlmacenamientosListado/",
            summary="Obtener listado de almacenamientos",
            description="",
            response_model=List[AlmacenamientoResponse])
async def get_almacenamientos_listado(
    alm_service: AlmacenamientosService = Depends(get_alm_service),
    current_user: UsuariosResponse = Depends(get_current_user)
):
    return  await alm_service.get_all_alm()


@router.get("/BuquesListado/",
            summary="Obtener listado de buques habilitados para recibo",
            description="Este listado se actualiza cuando PBCU confirma el atraco del buque al puerto.",
            response_model=List[FlotasActResponse])
async def get_buques_listado(
    flotas_service: FlotasService = Depends(get_flotas_service),
    current_user: UsuariosResponse = Depends(get_current_user)
):
    flotas = await flotas_service.get_buques_activos()
    return flotas


@router.get("/CamionesListado/",
            summary="Obtener listado de camiones registrados para despacho",
            description="Este listado se actualiza cuando PBCU confirma la llegada del camión al puerto.",
            response_model=List[FlotasActResponse])
async def get_camiones_listado(
    skip: int = 0,
    limit: int = 20,
    flotas_service: FlotasService = Depends(get_flotas_service),
    current_user: UsuariosResponse = Depends(get_current_user)
):
    return await flotas_service.get_paginated_flotas(skip, limit)

@router.get("/MaterialesListado/",
            summary="Obtener listado de materiales",
            description="",
            response_model=List[MaterialesResponse])
async def get_materiales_listado(
    mat_service: MaterialesService = Depends(get_mat_service),
    current_user: UsuariosResponse = Depends(get_current_user)
):
    return  await mat_service.get_all_mat()


@router.get("/MovimientosListado/",
            summary="Obtener listado páginado de movimientos",
            description="",
            response_model=List[MovimientosResponse])
async def get_movs_listado(
    skip: int = 0,
    limit: int = 20,
    mov_service: MovimientosService = Depends(get_mov_service),
    current_user: UsuariosResponse = Depends(get_current_user)
):
    return  await mov_service.get_paginated_mov(skip, limit)


@router.get("/Pesadas/{transaccion_id}",
    summary="Obtener pesadas de transacción específica",
    description="Devuelve un listado de pesadas asociadas a una transacción",
    response_model=List[PesadaResponse]
)
async def get_pesadas_listado(
    transaccion_id: int,
    pesada_service: PesadasService = Depends(get_pesadas_service),
    current_user: UsuariosResponse = Depends(get_current_user)
):
    return await pesada_service.get_pesada_by_idtrans(transaccion_id)

@router.get("/TransaccionesListado/",
            summary="Obtener listado páginado de transacciones",
            description="",
            response_model=List[TransaccionResponse])
async def get_trans_listado(
    skip: int = 0,
    limit: int = 20,
    tran_service: TransaccionesService = Depends(get_transacciones_service),
    current_user: UsuariosResponse = Depends(get_current_user)
):
    return  await tran_service.get_paginated_transacciones(skip, limit)


# @router.get("/{flota_id}", response_model=FlotaResponse)
# async def get_flota(
#     flota_id: int,
#     service: FlotasService = Depends(get_flotas_service),
#     current_user: UsuarioResponse = Depends(get_current_user)
# ):
#     flota = await service.get_flota(flota_id)
#     if not flota:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Flota not found"
#         )
#     return flota
#
# @router.put("/{flota_id}", response_model=FlotaResponse)
# async def update_flota(
#     flota_id: int,
#     flota: FlotaUpdate,
#     service: FlotasService = Depends(get_flotas_service),
#     current_user: UsuarioResponse = Depends(get_current_user)
# ):
#     updated_flota = await service.update_flota(flota_id, flota)
#     if not updated_flota:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Flota not found"
#         )
#     return updated_flota
#
# @router.delete("/{flota_id}", status_code=status.HTTP_204_NO_CONTENT)
# async def delete_flota(
#     flota_id: int,
#     service: FlotasService = Depends(get_flotas_service),
#     current_user: UsuarioResponse = Depends(get_current_user)
# ):
#     deleted_flota = await service.delete_flota(flota_id)
#     if not deleted_flota:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Flota not found"
#         )
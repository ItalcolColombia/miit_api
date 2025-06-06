from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi_pagination import Page, Params
from fastapi_pagination.ext.sqlalchemy import paginate
from core.di.service_injection import get_viajes_service, get_mat_service, get_alm_service, get_mov_service, \
    get_pesadas_service, get_transacciones_service, get_flotas_service

from schemas.almacenamientos_schema import AlmacenamientoResponse
from schemas.materiales_schema import MaterialesResponse
from schemas.movimientos_schema import MovimientosResponse
from schemas.pesadas_schema import PesadaResponse, PesadaCreate
from schemas.transacciones_schema import TransaccionResponse
from services.almacenamientos_service import AlmacenamientosService
from services.auth_service import AuthService
from services.flotas_service import FlotasService
from services.viajes_service import ViajesService
from services.movimientos_service import MovimientosService
from services.materiales_service import MaterialesService
from services.transacciones_service import TransaccionesService
from services.pesadas_service import PesadasService
from utils.response_util import ResponseUtil
from utils.schema_util import CreateResponse, ErrorResponse, ValidationErrorResponse, UpdateResponse
from schemas.viajes_schema import (
    ViajesActResponse
)

response_json = ResponseUtil().json_response
router = APIRouter(prefix="/scada", tags=["Automatizador"], dependencies=[Depends(AuthService.get_current_user)]) #



# @router.get("/flotas_listado/", response_model=List[FlotaResponse])
# async def list_flotas(
#     viajes_service: FlotasService = Depends(get_viajes_service),
#     current_user: UsuarioResponse = Depends(get_current_user)
# ):
#     all_flotas = await viajes_service.get_all_flotas()
#     return all_flotas
#
# @router.post("/", response_model=FlotaResponse, status_code=status.HTTP_201_CREATED)
# async def create_flota(
#     flota: FlotaCreate,
#     service: FlotasService = Depends(get_viajes_service),
#     current_user: UsuarioResponse = Depends(get_current_user)
# ):
#     created_flota = await service.create_flota(flota)
#     return created_flota

@router.get("/almacenamientos-listado/",
            summary="Obtener listado de almacenamientos",
            description="",
            response_model=List[AlmacenamientoResponse])
async def get_almacenamientos_listado(
    alm_service: AlmacenamientosService = Depends(get_alm_service)):
    return  await alm_service.get_all_alm()


@router.get("/buques-listado/",
            summary="Obtener listado de buques habilitados para recibo",
            description="Este listado se actualiza cuando PBCU confirma el atraco del buque al puerto.",
            response_model=List[ViajesActResponse])
async def get_buques_listado(
    viajes_service: ViajesService = Depends(get_viajes_service)):
    flotas = await viajes_service.get_buques_activos()
    return flotas


@router.get("/camiones-listado/",
            summary="Obtener listado de camiones registrados para despacho",
            description="Este listado se actualiza cuando PBCU confirma la llegada del camión al puerto.",
            response_model=Page[ViajesActResponse])
async def get_camiones_listado(
        viajes_service: ViajesService = Depends(get_viajes_service),
        params: Params = Depends()):
    flotas = await viajes_service.get_camiones_activos()
    return paginate(flotas, params)


@router.put("/camion-ajuste/{ref}",
            status_code=status.HTTP_200_OK,
            summary="Modificar puntos camion",
            description="Evento realizado por automatización de acuerdo a parametros de pits de despacho.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
                # Use ValidationErrorResponse
            })
async def points_camion(
        ref: str,
        points: int,
        service: FlotasService = Depends(get_flotas_service)):
    try:

        await service.chg_points(ref, points)
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"puntos actualizados",
        )

    except HTTPException as http_exc:
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.get("/materiales-listado/",
            summary="Obtener listado de materiales",
            description="",
            response_model=List[MaterialesResponse])
async def get_materiales_listado(
    mat_service: MaterialesService = Depends(get_mat_service)):
    return  await mat_service.get_all_mat()


# @router.get("/movimientos-listado/",
#             summary="Obtener listado páginado de movimientos",
#             description="",
#             response_model=List[MovimientosResponse])
# async def get_movs_listado(
#     skip: int = 0,
#     limit: int = 20,
#     mov_service: MovimientosService = Depends(get_mov_service)):
#     return  await mov_service.get_paginated_mov(skip, limit)


@router.get("/movimientos-listado/",
            summary="Obtener listado páginado de movimientos",
            description="",
            response_model=Page[MovimientosResponse])
async def get_movs_listado(
    mov_service: MovimientosService = Depends(get_mov_service),
    params: Params = Depends()):
    movimientos = await  mov_service.get_all_mov()
    return paginate(movimientos, params)




@router.post("/pesada-registro",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar pesada",
             description="Evento para registrar la información de una pesada.",
             response_model=PesadaCreate,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def create_pesada(
    pesada: PesadaCreate,
    service: PesadasService = Depends(get_pesadas_service),
):
    try:
        db_pesada = await service.create_pesada(pesada.model_dump())
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message="Registro de pesada exitoso",
            data={"id": db_pesada.id}
        )
    except HTTPException as http_exc:
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )
    except Exception as e:
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )


@router.get("/pesada-obtener/{transaccion_id}",
    summary="Obtener pesadas de una transacción específica",
    description="Devuelve listado paginado de pesadas asociadas a una transacción",
    response_model=Page[PesadaResponse]
)
async def get_pesadas_listado(
    transaccion_id: int,
    pesada_service: PesadasService = Depends(get_pesadas_service),
    params: Params = Depends()):
    pesadas = await pesada_service.get_pesada_by_idtrans(transaccion_id)
    return paginate(pesadas, params)

@router.get("/transacciones-listado/",
            summary="Obtener listado páginado de transacciones",
            description="",
            response_model=List[TransaccionResponse])
async def get_trans_listado(
    skip: int = 0,
    limit: int = 20,
    tran_service: TransaccionesService = Depends(get_transacciones_service),
):
    return  await tran_service.get_paginated_transacciones(skip, limit)


# @router.get("/{flota_id}", response_model=FlotaResponse)
# async def get_flota(
#     flota_id: int,
#     service: FlotasService = Depends(get_viajes_service),
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
#     service: FlotasService = Depends(get_viajes_service),
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
#     service: FlotasService = Depends(get_viajes_service),
#     current_user: UsuarioResponse = Depends(get_current_user)
# ):
#     deleted_flota = await service.delete_flota(flota_id)
#     if not deleted_flota:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Flota not found"
#         )
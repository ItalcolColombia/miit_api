from fastapi import APIRouter, Depends, HTTPException, status

from utils.response_util import ResponseUtil
from core.di.service_injection import get_flotas_service
from services.flotas_service import FlotasService
#from api.v1.middleware.auth_middleware import get_current_user
from schemas.usuarios_schema import UsuariosResponse
from utils.schema_util import CreateResponse, ErrorResponse, ValidationErrorResponse, UpdateResponse
from schemas.flotas_schema import (
    FlotasResponse,
    FlotaCreate,
    FlotaBuqueExtCreate,
    FlotaCamionExtCreate,
    FlotaExtLoadCreate,
    FlotaUpdate,
    FlotasActResponse
)

response_json = ResponseUtil().json_response
router = APIRouter(prefix="/operador", tags=["Integrador"])


@router.post("/BuqueRegistro",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar nuevo buque",
             description="Evento efectuado por el operador posterior al anuncio de nueva visita obtenida a traves de la interfaz de PBCU.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
                 # Use ValidationErrorResponse
             })
async def create_flota(
        flota: FlotaBuqueExtCreate,
        service: FlotasService = Depends(get_flotas_service),
    # current_user: UsuariosResponse = Depends(get_current_user)
):
    try:

        await service.create_buque_nuevo(flota)
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message=f"registro exitoso",
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


@router.post("/BuqueCarga",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar Bl de buque",
             description="Evento efectuado por el operador con la data obtenida a traves de la interfaz de PBCU.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
                 # Use ValidationErrorResponse
             })
async def load_flota(
        flota: FlotaExtLoadCreate,
        service: FlotasService = Depends(get_flotas_service),
    # current_user: UsuariosResponse = Depends(get_current_user)
):
    try:

        await service.create_buque_nuevo(flota)
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message=f"registro exitoso",
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


@router.put("/BuqueArribo/{flota_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar estado buque",
            description="Evento realizado por el operador post confirmación del arribo de la motonave a traves de la interfaz de PBCU.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
                # Use ValidationErrorResponse
            })
async def status_buque(
        flota_id: int,
        service: FlotasService = Depends(get_flotas_service),
    # current_user: UsuariosResponse = Depends(get_current_user)
):
    try:

        await service.chg_estado_buque(flota_id, True)
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"estado actualizado",
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

@router.post("/CamionRegistro",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar camión",
             description="Evento realizado por el operador con la cita de enturnamiento notificada a traves de la interfaz de PBCU.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def create_new_camion(
        camion: FlotaCamionExtCreate,
        service: FlotasService = Depends(get_flotas_service),
    # current_user: UsuariosResponse = Depends(get_current_user)
):
    try:

        await service.create_camion(camion)
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message=f"registro exitoso",
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
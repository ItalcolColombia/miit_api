from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from utils.response_util import ResponseUtil
from core.di.service_injection import get_viajes_service
from services.viajes_service import ViajesService
#from api.v1.middleware.auth_middleware import get_current_user
from utils.schema_util import CreateResponse, ErrorResponse, ValidationErrorResponse, UpdateResponse
from schemas.viajes_schema import (
    ViajesResponse,
    ViajeCreate,
    ViajeBuqueExtCreate,
    ViajeCamionExtCreate,
    FlotaExtLoadCreate,
    ViajeUpdate,
    ViajesActResponse
)
from schemas.bls_schema import BlsExtCreate, BlsCreate

from utils.logger_util import LoggerUtil
log = LoggerUtil()



response_json = ResponseUtil().json_response
router = APIRouter(prefix="/integrador", tags=["Integrador"])


@router.post("/buque-registro/",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar nuevo buque",
             description="Evento efectuado por el operador posterior al anuncio de nueva visita obtenida a traves de la interfaz de PBCU.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def create_buque(
        flota: ViajeBuqueExtCreate,
        service: ViajesService = Depends(get_viajes_service)):
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


@router.post("/buque-carga/",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar carga de buque",
             description="Evento efectuado por el operador con la información obtenida a traves de la interfaz de PBCU.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def set_load(
        bl: BlsExtCreate,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: {bl}")
    try:

        log.info("Iniciando creación de carga de buque")
        await service.create_buque_load(bl)
        log.info("Carga de buque completada")
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
        log.error(f"Error al procesar petición de registro BL: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )


@router.put("/buque-arribo/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar estado de un buque",
            description="Evento realizado por el operador post confirmación del arribo de la motonave a traves de la interfaz de PBCU.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def buque_in(
        puerto_id: str,
        service: ViajesService = Depends(get_viajes_service)):
    try:

        await service.chg_estado_buque(puerto_id, True)
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

@router.post("/camion-registro/",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar camión",
             description="Evento realizado por el operador con la cita de enturnamiento notificada a traves de la interfaz de PBCU.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def create_camion(
        camion: ViajeCamionExtCreate,
        service: ViajesService = Depends(get_viajes_service)):
    try:

        await service.create_camion_nuevo(camion)
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
@router.put("/camion-ingreso/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar cita del camion",
            description="Evento realizado por el operador post confirmación del ingreso del camión a báscula a traves de la interfaz de PBCU.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def in_camion(
        puerto_id: str,
        fecha_ingreso: datetime,
        service: ViajesService = Depends(get_viajes_service)):
    try:

        await service.chg_camion_ingreso(puerto_id, fecha_ingreso)
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Registró de cita de camión actualizada exitosamente",
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

@router.put("/camion-egreso/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar cita del camion",
            description="Evento realizado por el operador post confirmación del egreso del camión a báscula a traves de la interfaz de PBCU.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
                # Use ValidationErrorResponse
            })
async def out_camion(
        puerto_id: str,
        fecha_salida: datetime,
        peso_real: Decimal,
        service: ViajesService = Depends(get_viajes_service)):
    try:

        await service.chg_camion_salida(puerto_id, fecha_salida, peso_real)
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Registro cita camión actualizada exitosamente",
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
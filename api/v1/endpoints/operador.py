from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime

from schemas.pesadas_schema import VPesadasAcumResponse
from services.auth_service import AuthService
from utils.response_util import ResponseUtil
from core.di.service_injection import get_viajes_service, get_pesadas_service
from services.viajes_service import ViajesService
from services.pesadas_service import PesadasService
from schemas.response_models import CreateResponse, ErrorResponse, ValidationErrorResponse, UpdateResponse
from schemas.viajes_schema import (
    ViajeBuqueExtCreate,
    ViajeCamionExtCreate
)
from schemas.bls_schema import BlsExtCreate

from utils.logger_util import LoggerUtil
log = LoggerUtil()



response_json = ResponseUtil.json_response
router = APIRouter(prefix="/integrador", tags=["Integrador"], dependencies=[Depends(AuthService.get_current_user)])


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
    log.info(f"Payload recibido: Buque {flota}")
    try:
        await service.create_buque_nuevo(flota)
        log.info(f"Buque {flota.puerto_id} registrado")
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message=f"registro exitoso",
        )

    except HTTPException as http_exc:
        log.error(f"Buque {flota.puerto_id} no registrado: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar petición de registro de Buque {flota.puerto_id}: {e}")
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
        await service.create_buque_load(bl)
        log.info(f"BL {bl.no_bl} de buque {bl.puerto_id} registrado")
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message=f"registro exitoso",
        )

    except HTTPException as http_exc:
        log.error(f"BL {bl.no_bl} de buque {bl.puerto_id} no registrado: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar petición de registro BL {bl.no_bl} de buque {bl.puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )


@router.put("/buque-arribo/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar estado de un buque por arribo",
            description="Evento realizado por el operador post confirmación del arribo de la motonave a traves de la interfaz de PBCU.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def buque_in(
        puerto_id: str,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: Flota {puerto_id} - Arribo")
    try:
        await service.chg_estado_buque(puerto_id, True)
        log.info(f"Arribo de buque {puerto_id} marcado exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"estado actualizado",
        )

    except HTTPException as http_exc:
        log.error(f"El arribo de buque {puerto_id} no pudo marcarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado de arribo de buque {puerto_id}: {e}")
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
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def create_camion(
        flota: ViajeCamionExtCreate,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: Flota {flota}")
    try:

        await service.create_camion_nuevo(flota)
        log.info(f"Flota {flota.puerto_id} registrada")
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message=f"registro exitoso",
        )

    except HTTPException as http_exc:
        log.error(f"Flota {flota.puerto_id} no registrada: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar petición de registro de Flota {flota.puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )
@router.put("/camion-ingreso/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar cita del camion para actualizar ingreso",
            description="Evento realizado por el operador post confirmación del ingreso del camión a báscula a traves de la interfaz de PBCU.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def in_camion(
        puerto_id: str,
        fecha_ingreso: datetime,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: Flota {puerto_id} - Ingreso ")
    try:

        await service.chg_camion_ingreso(puerto_id, fecha_ingreso)
        log.info(f"Ingreso de flota {puerto_id} marcada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Registró de cita de camión actualizada exitosamente",
        )

    except HTTPException as http_exc:
        log.error(f"El ingreso de flota {puerto_id} no pudo marcarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado de ingreso de Flota {puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.put("/camion-egreso/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar cita del camion para actualizar el egreso",
            description="Evento realizado por el operador post confirmación del egreso del camión a báscula a traves de la interfaz de PBCU.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def out_camion(
        puerto_id: str,
        fecha_salida: datetime,
        peso_real: Decimal,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: Camion {puerto_id} - Salida")
    try:

        await service.chg_camion_salida(puerto_id, fecha_salida, peso_real)
        log.info(f"Salida de camion {puerto_id} marcada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Registro cita camión actualizada exitosamente",
        )

    except HTTPException as http_exc:
        log.error(f"La salida de camion {puerto_id} no pudo marcarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado de salida de camion {puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.post("/pesadas-parciales/{puerto_id}",
             status_code=status.HTTP_200_OK,
             summary="Obtener acumulado de pesadas",
             description="Evento realizado por el operador post petición de consulta recibida a traves de la interfaz de PBCU.",
             response_model=VPesadasAcumResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},  # Use CustomErrorResponse
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
                 status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
             })
async def get_acum_pesadas(
        service: PesadasService = Depends(get_pesadas_service),
        puerto_id: str = None):
    try:
        await service.get_pesada_acumulada(puerto_id)
        log.info(f"Consulta de pesadas para flota {puerto_id} realizada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"estado actualizado",
        )

    except HTTPException as http_exc:
        log.error(f"Consulta de flota {puerto_id} no pudo realizarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al consultar pesadas de flota {puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )



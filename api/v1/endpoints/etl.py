from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi_pagination import Page, Params
from core.di.service_injection import get_viajes_service, get_mat_service, get_alm_service, get_mov_service, \
    get_pesadas_service, get_transacciones_service, get_flotas_service

from schemas.almacenamientos_schema import AlmacenamientoResponse
from schemas.materiales_schema import MaterialesResponse
from schemas.movimientos_schema import MovimientosResponse
from schemas.pesadas_schema import PesadaResponse, PesadaCreate
from schemas.transacciones_schema import TransaccionResponse, TransaccionCreate
from schemas.viajes_schema import ViajesActResponse, VViajesResponse
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

from utils.logger_util import LoggerUtil
log = LoggerUtil()

response_json = ResponseUtil().json_response
router = APIRouter(prefix="/scada", tags=["Automatizador"], dependencies=[Depends(AuthService.get_current_user)]) #

@router.get("/almacenamientos-listado/",
            summary="Obtener listado de almacenamientos",
            description="Retorna listado de los almacenamientos disponibles en el repositorio central",
            response_model=List[AlmacenamientoResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_almacenamientos_listado(
    alm_service: AlmacenamientosService = Depends(get_alm_service)
):
    try:
        return await alm_service.get_all_alm()

    except HTTPException as http_exc:
        log.warning(f"No se encontraron los almacenamientos: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener listado de almacenamientos")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )


@router.get("/buques-listado/",
            summary="Obtener listado de buques habilitados para recibo",
            description="Este listado se actualiza cuando PBCU confirma el atraco del buque al puerto.",
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_buques_listado(
    viajes_service: ViajesService = Depends(get_viajes_service)
):
    try:
        return await viajes_service.get_buques_activos()

    except HTTPException as http_exc:
        log.warning(f"No se encontraron buques disponibles: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener listado de buques")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )


@router.get("/camiones-listado/{placa}",
            summary="Obtener listado paginado de camiones con filtro opcional por placa",
            description="Retorna camiones en modo páginado, filtradas opcionalmente por placa específica",
            response_model=Page[VViajesResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_camiones_paginado(
    viajes_service: ViajesService = Depends(get_viajes_service),
    truck_plate: Optional[str] = Query(None, description="Placa específica a buscar")
):
    if truck_plate is None:
        log.info(f"Payload recibido: Obtener camión con id {truck_plate}")
    try:
        return await viajes_service.get_pag_camiones_activos(truck_plate)

    except HTTPException as http_exc:
        log.warning(f"No se encontraron camiones: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener listado de camiones")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.put("/camion-ajuste/{placa}",
            status_code=status.HTTP_200_OK,
            summary="Modificar puntos camion",
            description="Evento realizado por automatización de acuerdo a parametros de pits de despacho.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def set_points_camion(
        truck_plate: str,
        points: int,
        service: FlotasService = Depends(get_flotas_service)
):
    log.info(f"Payload recibido: Ajustar puntos de camión {truck_plate} a {points} puntos")
    try:

        await service.chg_points(truck_plate, points)
        log.info(f"Los puntos del camión {truck_plate} ajustado a {points} exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"puntos actualizados",
        )

    except HTTPException as http_exc:
        log.error(f"Los puntos del camión {truck_plate} no pudieron ajustarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error interno: {e}"
        )

@router.get("/materiales-listado/",
            summary="Obtener listado de materiales",
            description="Método de consulta de materiales empleados en el puerto",
            response_model=List[MaterialesResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_materiales_listado(
    mat_service: MaterialesService = Depends(get_mat_service)
):
    try:
        return  await mat_service.get_all_mat()

    except HTTPException as http_exc:
        log.warning(f"No se encontraron materiales: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener listado de materiales")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )


@router.get("/movimientos-listado/{transaccion_id}",
            summary="Obtener listado paginado de movimientos con filtro opcional por transacción",
            description="Retorna movimientos en modo páginado, filtradas opcionalmente por un id de transacción específico",
            response_model=Page[MovimientosResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_movs_listado(
    mov_service: MovimientosService = Depends(get_mov_service),
    tran_id: Optional[int] = Query(None, description="Id de Transacción específico a buscar")
):
    if tran_id is None:
        log.info(f"Payload recibido: Obtener movimientos de transacción {tran_id}")
    try:
        return await mov_service.get_pag_movimientos(tran_id)

    except HTTPException as http_exc:
        log.warning(f"No se encontraron movimientos: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener movimientos")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )


@router.post("/pesada-registro/",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar pesada",
             description="Evento para registrar la información de una pesada.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def create_pesada(
    pesada: PesadaCreate,
    service: PesadasService = Depends(get_pesadas_service),
):
    log.info(f"Payload recibido: Pesada {pesada} - Crear")
    try:
       await service.create_pesada_if_not_exists(pesada)
       return response_json(
            status_code=status.HTTP_201_CREATED,
            message="registro exitoso."
       )

    except HTTPException as http_exc:
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )
    except Exception as e:
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error interno: {e}"
        )

@router.get("/pesadas-listado/{transaccion_id}",
            summary="Obtener listado paginado de pesadas con filtro opcional por transacción",
            description="Retorna pesadas en modo páginado, filtradas opcionalmente por un id de transacción específico",
            response_model=Page[PesadaResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_pesadas_listado(
    pesada_service: PesadasService  = Depends(get_pesadas_service),
    tran_id: Optional[int] = Query(None, description="Id de Transacción específico a buscar")
):
    if tran_id is None:
        log.info(f"Payload recibido: Obtener pesadas de transacción {tran_id}")
    try:
        return await pesada_service.get_pag_pesadas(tran_id)

    except HTTPException as http_exc:
        log.warning(f"No se encontraron pesadas: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener pesadas")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.get("/transacciones-listado/{transaccion_id}",
            summary="Obtener listado paginado de transacciones con filtro opcional",
            description="Retorna transacciones en modo páginado, filtradas opcionalmente por un id de transacción específico",
            response_model=Page[TransaccionResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_trans_listado(
    tran_service: TransaccionesService = Depends(get_transacciones_service),
    tran_id: Optional[int] = Query(None, description="Id de Transacción específico a buscar")
):
    if tran_id is None:
        log.info(f"Payload recibido: Obtener transacción filtrado por id {tran_id}")
    try:
        return  await tran_service.get_pag_transacciones(tran_id)

    except HTTPException as http_exc:
        log.warning(f"No se encontraron transacciones: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener transacciones")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.post("/transacciones-registro/",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar nueva transacción",
             description="Evento para registrar la información de una transacción.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def create_transaccion(
    tran: TransaccionCreate,
    service: TransaccionesService = Depends(get_transacciones_service),
):
    log.info(f"Payload recibido: Transacción {tran} - Crear")
    try:
        await service.create_transaccion_if_not_exists(tran)
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message="registro exitoso."
        )

    except HTTPException as http_exc:
        log.error(f"La transacción con viaje {tran.viaje_id} no fue registrada: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar petición de registro de transacción con viaje {tran.viaje_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.put("/transaccion-finalizar/{transaccion_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar puntos camion",
            description="Evento realizado por automatización de acuerdo a parametros de pits de despacho.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def set_points_camion(
        tran_id: str,
        points: int,
        service: FlotasService = Depends(get_flotas_service)
):

    try:

        await service.chg_points(tran_id, points)
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
            message=f"Error interno: {e}"
        )
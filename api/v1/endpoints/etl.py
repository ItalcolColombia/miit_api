from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi_pagination import Page
from core.di.service_injection import get_viajes_service, get_mat_service, get_alm_service, get_mov_service, \
    get_pesadas_service, get_transacciones_service, get_flotas_service, get_alm_mat_service
from schemas.almacenamientos_materiales_schema import VAlmMaterialesResponse

from schemas.almacenamientos_schema import AlmacenamientoResponse
from schemas.materiales_schema import MaterialesResponse
from schemas.movimientos_schema import MovimientosResponse
from schemas.pesadas_schema import PesadaResponse, PesadaCreate
from schemas.transacciones_schema import TransaccionResponse, TransaccionCreate
from schemas.viajes_schema import VViajesResponse
from services.almacenamientos_materiales_service import AlmacenamientosMaterialesService
from services.almacenamientos_service import AlmacenamientosService
from services.auth_service import AuthService
from services.flotas_service import FlotasService
from services.viajes_service import ViajesService
from services.movimientos_service import MovimientosService
from services.materiales_service import MaterialesService
from services.transacciones_service import TransaccionesService
from services.pesadas_service import PesadasService
from utils.response_util import ResponseUtil
from schemas.response_models import CreateResponse, ErrorResponse, ValidationErrorResponse, UpdateResponse

from utils.logger_util import LoggerUtil
log = LoggerUtil()

response_json = ResponseUtil().json_response
router = APIRouter(prefix="/scada", tags=["Automatizador"], dependencies=[Depends(AuthService.get_current_user)]) #

@router.get("/almacenamientos-saldos",
            summary="Obtener listado paginado de almacenamientos saldos con filtro opcional por nombre.",
            description="Retorna almacenamientos en modo páginado, filtrados opcionalmente por nombre específico",
            response_model=Page[VAlmMaterialesResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_almacenamientos_paginado(
    alm_mat_service: AlmacenamientosMaterialesService = Depends(get_alm_mat_service),
    nombre_alm: Optional[str] = Query(None, description="Nombre específico a buscar")
):
    if nombre_alm is None:
        log.info(f"Payload recibido: Obtener alm. con nombre {nombre_alm}")
    try:
        return await alm_mat_service.get_pag_alm_mat(nombre_alm)

    except HTTPException as http_exc:
        log.warning(f"No se encontraron alm_mat: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener listado de alm_mat")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.get("/buques-listado",
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

@router.put("/buque-finalizar/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar estado de un buque por partida",
            description="Evento realizado por la automatización al dar por finalizado el recibo de buque.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def end_buque(
        puerto_id: str,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: Flota {puerto_id} - Partida")
    try:

        await service.chg_estado_flota(puerto_id, False)
        log.info(f"La Partida de buque {puerto_id} marcada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"estado actualizado",
        )

    except HTTPException as http_exc:
        log.error(f"La partida de buque {puerto_id} no pudo marcarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado de partida de buque {puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.get("/camiones-listado",
            summary="Obtener listado paginado de camiones disponibles para despacho con filtro opcional por placa",
            description="Retorna camiones a despachar en modo páginado, filtradas opcionalmente por placa específica",
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

@router.put("/camion-ajuste",
            status_code=status.HTTP_200_OK,
            summary="Modificar el número de puntos de descargue de un camión ",
            description="Evento realizado por la automatización de acuerdo a parámetros de pits de despacho.",
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

@router.get("/materiales-listado",
            summary="Obtener listado de materiales",
            description="Método de consulta por la automatización para obtener listado de materiales empleados en el puerto",
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


@router.get("/movimientos-listado",
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


@router.post("/pesada-registro",
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

@router.get("/pesadas-listado",
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

@router.get("/transacciones-listado",
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

@router.post("/transacciones-registro",
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

@router.put("/transaccion-finalizar/{tran_id}",
            status_code=status.HTTP_200_OK,
            summary="Modifica el estado de una transacción en curso",
            description="Evento realizado por la automatización cuando se detiene una ruta en proceso.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def end_transaction(
        tran_id: str,
        service: TransaccionesService = Depends(get_transacciones_service)):
    log.info(f"Payload recibido: Transacción {tran_id} - Finalizar")

    try:

        await service.transaccion_finalizar(tran_id)
        log.info(f"La Transacción {tran_id} finalizada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Transacción finalizada",
        )

    except HTTPException as http_exc:
        log.error(f"La Transacción {tran_id} no pudo finalizarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar finalización de transacción {tran_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=f"Error interno: {e}"
        )

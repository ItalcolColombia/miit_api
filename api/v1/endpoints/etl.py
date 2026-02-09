from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi_pagination import Page

from core.di.service_injection import get_viajes_service, get_mat_service, get_mov_service, \
    get_pesadas_service, get_transacciones_service, get_flotas_service, get_alm_mat_service, get_ajustes_service
from core.enums.user_role_enum import UserRoleEnum
from schemas.almacenamientos_materiales_schema import VAlmMaterialesResponse
from schemas.materiales_schema import MaterialesResponse
from schemas.movimientos_schema import MovimientosResponse
from schemas.pesadas_schema import PesadaResponse, PesadaCreate
from schemas.response_models import CreateResponse, ErrorResponse, ValidationErrorResponse, UpdateResponse, TransaccionRegistroResponse
from schemas.transacciones_schema import TransaccionResponse, TransaccionCreate, TransaccionCreateExt
from schemas.viajes_schema import ViajesActivosPorMaterialResponse
from services.almacenamientos_materiales_service import AlmacenamientosMaterialesService
from services.auth_service import AuthService
from services.flotas_service import FlotasService
from services.materiales_service import MaterialesService
from services.movimientos_service import MovimientosService
from services.pesadas_service import PesadasService
from services.transacciones_service import TransaccionesService
from services.viajes_service import ViajesService
from services.ajustes_service import AjustesService
from utils.logger_util import LoggerUtil
from utils.response_util import ResponseUtil
from schemas.ajustes_schema import AjusteCreate

log = LoggerUtil()

response_json = ResponseUtil().json_response
router = APIRouter(prefix="/scada", tags=["Automatizador"], dependencies=[Depends(AuthService.require_access(roles=[UserRoleEnum.ADMINISTRADOR, UserRoleEnum.AUTOMATIZADOR]))])

@router.get("/almacenamientos-listado",
            summary="Obtener listado paginado de almacenamientos con filtro opcional por nombre.",
            description="Retorna almacenamientos en modo páginado, filtrados opcionalmente por nombre específico",
            response_model=Page[VAlmMaterialesResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_almacenamientos_paginado(
    alm_mat_service: AlmacenamientosMaterialesService = Depends(get_alm_mat_service),
    id_alm: Optional[int] = Query(None, description="Id almacenamiento específico a buscar")
):
    if id_alm is None:
        log.info(f"Payload recibido: Obtener datos almacenamiento {id_alm}")
    try:
        return await alm_mat_service.get_pag_alm_mat(id_alm)

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

@router.get("/viajes-activos",
            summary="Obtener viajes activos agrupados por material",
            description="Retorna los viajes activos (estado_operador=true en flota) agrupados por material. "
                        "Para buques agrupa por materiales de BLs, para camiones usa el material del viaje.",
            response_model=List[ViajesActivosPorMaterialResponse],
            responses={
                status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
            },
)
async def get_viajes_activos_por_material(
    tipo_flota: str = Query(..., description="Tipo de flota: 'buque' o 'camion'"),
    viajes_service: ViajesService = Depends(get_viajes_service)
):
    log.info(f"Solicitud de viajes activos por material para tipo: {tipo_flota}")
    try:
        # Validar tipo de flota
        if tipo_flota.lower() not in ['buque', 'camion']:
            return response_json(
                status_code=status.HTTP_400_BAD_REQUEST,
                message="El parámetro tipo_flota debe ser 'buque' o 'camion'"
            )

        viajes = await viajes_service.get_viajes_activos_por_material(tipo_flota)

        if not viajes:
            return response_json(
                status_code=status.HTTP_404_NOT_FOUND,
                message=f"No se encontraron viajes activos para tipo {tipo_flota}"
            )

        return viajes

    except HTTPException as http_exc:
        log.warning(f"Error al obtener viajes activos por material: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error inesperado al obtener viajes activos por material: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.put("/buque-finalizar/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar viaje del buque para actualizar estado por partida",
            description="Evento realizado por la automatización al dar por finalizado el recibo de buque."
                        "Actualiza el estado_operador a False."
                        "Corresponde a FinalizaBuqueMT.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse},
            })
async def end_buque(
        puerto_id: str,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: Flota {puerto_id} - Partida")
    try:

        await service.chg_estado_flota(puerto_id, estado_operador=False)
        log.info(f"La Partida de buque {puerto_id} desde el puerto marcada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"estado actualizado",
        )

    except HTTPException as http_exc:
        log.error(f"La partida de buque {puerto_id} desde el puerto no pudo marcarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado de partida de buque {puerto_id} desde el puerto: {e}")
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
                status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse},
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

@router.put("/camion-finalizar/{viaje_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar estado de un camion por cargue",
            description="Evento realizado por la automatización al dar por finalizado el recibo de buque."
                        "Corresponde a CamionCargue (SendTruckFinalizationLoading).",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse},
            })
async def end_camion(
        viaje_id: int,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: Viaje {viaje_id} - Partida")
    try:

        await service.chg_estado_flota(viaje_id=viaje_id, estado_operador=False)
        log.info(f"Finalización de cargue para viaje {viaje_id} registrada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Finalización de cargue para viaje {viaje_id} registrada exitosamente.",
        )

    except HTTPException as http_exc:
        log.error(f"Finalización de cargue para viaje {viaje_id} falló: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado de partida de viaje {viaje_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
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
             description="Evento para registrar la información de una pesada. El consecutivo se calcula automáticamente por transacción si no se proporciona.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse},
             })
async def create_pesada(
    pesada: PesadaCreate,
    service: PesadasService = Depends(get_pesadas_service),
):
    log.info(f"Payload recibido: Pesada {pesada} - Crear")
    try:
       await service.create_pesada(pesada)
       return response_json(
            status_code=status.HTTP_201_CREATED,
            message="Registro exitoso."
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
                 status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse},
             })
async def create_transaccion(
    tran: TransaccionCreate,
    service: TransaccionesService = Depends(get_transacciones_service),
):
    # Identificador para logs: viaje_id para Despacho/Recibo, origen/destino para Traslado
    tran_identifier = f"viaje={tran.viaje_id}" if tran.viaje_id else f"origen={tran.origen_id}/destino={tran.destino_id}"
    log.info(f"Payload recibido: Transacción tipo={tran.tipo} {tran_identifier} - Crear")
    try:
        await service.create_transaccion_if_not_exists(tran)
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message="Registro exitoso."
        )

    except HTTPException as http_exc:
        log.error(f"La transacción {tran_identifier} no fue registrada: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar petición de registro de transacción {tran_identifier}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.post("/transacciones-registro-ext",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar nueva transacción (schema simplificado)",
             description="Endpoint para registrar transacciones usando nombres en lugar de IDs. "
                         "El peso_meta se calcula automáticamente de los BLs del viaje agrupados por material. "
                         "El ref1 se obtiene del puerto_id del viaje.",
             response_model=TransaccionRegistroResponse,
             responses={
                 status.HTTP_201_CREATED: {"model": TransaccionRegistroResponse},
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                 status.HTTP_409_CONFLICT: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse},
             })
async def create_transaccion_ext(
    tran: TransaccionCreateExt,
    service: TransaccionesService = Depends(get_transacciones_service),
):
    # Identificador para logs
    tran_identifier = f"viaje={tran.viaje_id}, material={tran.material}" if tran.viaje_id else f"origen={tran.origen}/destino={tran.destino}, material={tran.material}"
    log.info(f"Payload recibido: Transacción ext tipo={tran.tipo} {tran_identifier} - Crear")
    try:
        tran_creada = await service.create_transaccion_ext(tran)
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message="Registro exitoso.",
            data={"transaccion_id": tran_creada.id}
        )

    except HTTPException as http_exc:
        log.error(f"La transacción ext {tran_identifier} no fue registrada: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar petición de registro de transacción ext {tran_identifier}: {e}")
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
                status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse},
            })
async def end_transaction(
        tran_id: int,
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

@router.post("/ajustes",
             status_code=status.HTTP_201_CREATED,
             summary="Crear un ajuste de saldo de material en almacenamiento",
             description="Crea un ajuste de saldo y el movimiento asociado, actualizando el saldo en almacenamiento_materiales.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": ValidationErrorResponse},
             })
async def crear_ajuste(
    data: AjusteCreate,
    ajustes_service: AjustesService = Depends(get_ajustes_service),
):
    log.info(f"Payload recibido: Ajuste {data} - Crear")
    try:
        ajuste_resp = await ajustes_service.create_ajuste(data)
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message="Registro exitoso.",
            data={"ajuste": ajuste_resp}
        )

    except HTTPException as http_exc:
        log.error(f"El ajuste no pudo registrarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        # BasedException se mapea aquí porque el service lanza BasedException en casos esperados
        try:
            from core.exceptions.base_exception import BasedException
            if isinstance(e, BasedException):
                return response_json(
                    status_code=e.status_code,
                    message=e.message
                )
        except Exception:
            pass

        log.error(f"Error al procesar petición de registro de ajuste: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

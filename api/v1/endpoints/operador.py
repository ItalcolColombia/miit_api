from datetime import datetime
from decimal import Decimal
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from core.di.service_injection import get_viajes_service, get_pesadas_service
from core.enums.user_role_enum import UserRoleEnum
from core.exceptions.base_exception import BasedException
from core.exceptions.entity_exceptions import EntityNotFoundException
from schemas.bls_schema import BlsExtCreate
from schemas.pesadas_schema import VPesadasAcumResponse
from schemas.response_models import CreateResponse, ErrorResponse, ValidationErrorResponse, UpdateResponse, \
    CamionIngresoResponse, CamionRegistroResponse
from schemas.viajes_schema import (
    ViajeBuqueExtCreate,
    ViajeCamionExtCreate
)
from services.auth_service import AuthService
from services.envio_final_service import notify_envio_final
from services.pesadas_service import PesadasService
from services.viajes_service import ViajesService
from utils.logger_util import LoggerUtil
from utils.response_util import ResponseUtil
from utils.time_util import normalize_to_app_tz

log = LoggerUtil()
response_json = ResponseUtil.json_response
router = APIRouter(prefix="/integrador", tags=["Integrador"],  dependencies=[Depends(AuthService.require_access(roles=[UserRoleEnum.ADMINISTRADOR, UserRoleEnum.INTEGRADOR]))])


@router.post("/buque-registro",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar nuevo buque",
             description="Evento efectuado por el operador posterior al Anuncio MN obtenido a través de la interfaz de PBCU. "
                         "Corresponde a BuquesRegistro en el diagrama de flujo de proceso.",
             response_model=CreateResponse,
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
             })
async def create_buque(
        flota: ViajeBuqueExtCreate,
        service: ViajesService = Depends(get_viajes_service)):
    # Log de depuración: mostrar valores de fecha recibidos y su tzinfo
    # try:
    #     fecha_llegada = getattr(flota, 'fecha_llegada', None)
    #     fecha_salida = getattr(flota, 'fecha_salida', None)
    #     log.info(f"[DEBUG create_buque] fecha_llegada raw: {fecha_llegada} (tzinfo={getattr(fecha_llegada, 'tzinfo', None)})")
    #     log.info(f"[DEBUG create_buque] fecha_salida raw:  {fecha_salida} (tzinfo={getattr(fecha_salida, 'tzinfo', None)})")
    # except Exception as e:
    #     log.warning(f"[DEBUG create_buque] Error al inspeccionar fechas del payload: {e}")
    #
    # log.info(f"Payload recibido: Buque {flota}")
    try:
        await service.create_buque_nuevo(flota)
        log.info(f"Buque {flota.puerto_id} registrado")
        return response_json(
            status_code=status.HTTP_201_CREATED,
            message=f"Registro exitoso",
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


@router.post("/buque-carga",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar carga de buque",
             description="Evento efectuado por el operador con la información obtenida a través de la interfaz de PBCU. "
                         "Corresponde a BuquesCarga en el diagrama de flujo de proceso.",
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
            message=f"Registro exitoso",
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
            summary="Modificar viaje del buque para actualizar estado por arribo",
            description="Evento realizado por el operador post confirmación del arribo de la motonave a través de la interfaz de PBCU. "
                        "Actualiza del estado_puerto de la flota a True. "
                        "Corresponde a BuqueArrivo en el diagrama de flujo de proceso.",
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
        await service.chg_estado_flota(puerto_id, estado_puerto=True)
        log.info(f"Arribo de buque {puerto_id} marcado exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Estado actualizado",
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

@router.put("/buque-finalizar/{puerto_id}",
            status_code=status.HTTP_200_OK,
            summary="Modificar estado de un buque por partida",
            description="Evento realizado por la automatización al dar por finalizado el recibo de buque. "
                        "Actualiza el estado_puerto a False. "
                        "Corresponde a FinalizaBuqueOP.",
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

        await service.chg_estado_flota(puerto_id, estado_puerto=False)
        log.info(f"La Partida de buque {puerto_id} desde el operador marcada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Estado actualizado",
        )
    except HTTPException as http_exc:
        log.error(f"La partida de buque {puerto_id} desde el operador no pudo marcarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado de partida de buque {puerto_id} desde el operador: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.put("/levante-carga-puerto/{no_bl}",
            status_code=status.HTTP_200_OK,
            summary="Modificar bit del estado_puerto de un BL",
            description="Evento realizado por el operador posterior a confirmación de levante de carga la motonave a través de la interfaz de PBCU. "
                        "Corresponde a LevanteCargaPuerto en el diagrama de flujo de proceso.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def load_release_puerto(
        no_bl: str,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: BL {no_bl} - Levante de Carga")
    try:
        await service.chg_estado_carga(no_bl, estado_puerto=True)
        log.info(f"BL {no_bl}  estado_puerto marcado exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"estado_puerto actualizado",
        )

    except HTTPException as http_exc:
        log.error(f"BL {no_bl} el estado_puerto no pudo marcarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado de BL {no_bl}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.put("/levante-carga-operador/{no_bl}",
            status_code=status.HTTP_200_OK,
            summary="Modificar bit del estado_operador ",
            description="Evento realizado por el operador posterior a confirmación de levante de carga la motonave a través de la interfaz de Control Carga. "
                        "Corresponde a LevanteCargaOperador en el diagrama de flujo de proceso.",
            response_model=UpdateResponse,
            responses={
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def load_release_operador(
        no_bl: str,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: BL {no_bl} - Levante de Carga")
    try:
        await service.chg_estado_carga(no_bl,estado_operador=True)
        log.info(f"BL {no_bl}  estado_operador  marcado exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Estado_operador actualizado",
        )

    except HTTPException as http_exc:
        log.error(f"BL {no_bl} estado_operador no pudo marcarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )

    except Exception as e:
        log.error(f"Error al procesar marcado estado_operador de BL {no_bl}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.post("/camion-registro",
             status_code=status.HTTP_201_CREATED,
             summary="Registrar camión",
             description="Evento realizado por el operador con la cita de enturnamiento notificada a través de la interfaz de PBCU. "
                         "Corresponde a CamionRegistro en el diagrama de flujo de proceso.",
             response_model=CamionRegistroResponse,
             responses={
                 status.HTTP_201_CREATED: {"model": CamionRegistroResponse},
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
            message=f"Registró de cita de camión realizada exitosamente",
            data={"cargoPit": 1} # Valor por defecto del pit
        )

    except BasedException as be:
        # Manejar errores controlados desde el servicio (ej. violación de unicidad)
        log.error(f"Flota {flota.puerto_id} no registrada (BasedException): {be}")
        return response_json(
            status_code=getattr(be, 'status_code', status.HTTP_400_BAD_REQUEST),
            message=str(getattr(be, 'message', str(be)))
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
            description="Evento realizado por el operador post confirmación del ingreso del camión a báscula a través de la interfaz de PBCU. "
                        "Corresponde a CamionIngreso en el diagrama de flujo de proceso.",
            response_model=CamionIngresoResponse,
            responses={
                status.HTTP_200_OK: {"model": CamionIngresoResponse},
                status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                status.HTTP_422_UNPROCESSABLE_ENTITY: {"model": ValidationErrorResponse},
            })
async def in_camion(
        puerto_id: str,
        fecha_ingreso: datetime,
        service: ViajesService = Depends(get_viajes_service)):
    log.info(f"Payload recibido: Flota {puerto_id} - Ingreso ")
    try:
        fecha_ingreso_utc = normalize_to_app_tz(fecha_ingreso)

        service_data = await service.chg_camion_ingreso(puerto_id, fecha_ingreso_utc)

        try:
            await service.chg_estado_flota_simple(puerto_id, estado_puerto=True, estado_operador=True)
            log.info(f"Flags estado_puerto y estado_operador para {puerto_id} puestos en True tras ingreso de camión.")
        except Exception as e_flags:
            # No bloquear la respuesta por un fallo actualizando flags, pero loguear
            log.warning(f"No se pudo actualizar flags de flota para {puerto_id} tras ingreso de camión: {e_flags}")

        log.info(f"Ingreso de flota {puerto_id} marcado exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Modificación de cita de camión realizada exitosamente",
            data=service_data
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
            description="Evento realizado por el operador post confirmación del egreso del camión a báscula a través de la interfaz de PBCU. "
                        "Corresponde a CamionSalida en el diagrama de flujo de proceso.",
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
        # Normalizar fecha_salida a UTC
        fecha_salida_utc = normalize_to_app_tz(fecha_salida)

        await service.chg_camion_salida(puerto_id, fecha_salida_utc, peso_real)
        try:
            await service.chg_estado_flota(puerto_id, estado_puerto=False)
            log.info(f"Estado de puerto para flota {puerto_id} puesto en False tras egreso de camión.")
        except Exception as e_state:
            log.warning(f"No se pudo actualizar estado_puerto para {puerto_id} tras egreso de camión: {e_state}")

        log.info(f"Salida de camion {puerto_id} marcada exitosamente.")
        return response_json(
            status_code=status.HTTP_200_OK,
            message=f"Salida de camion {puerto_id} marcada exitosamente.",
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

@router.get("/pesadas-parciales/{puerto_id}",
             status_code=status.HTTP_200_OK,
             summary="Obtener acumulado de pesadas",
             description="Evento realizado por el operador post petición de consulta recibida a través de la interfaz de PBCU. "
                         "Consumo realizado por JOB del integrador para obtención de pesadas acumuladas por flota. "
                         "Corresponde a Envioparciales en el diagrama de flujo de proceso.",
             response_model=List[VPesadasAcumResponse],
             responses={
                 status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
             })
async def get_acum_pesadas(
        service: PesadasService = Depends(get_pesadas_service),
        puerto_id: str = None):
    try:
        pesadas = await service.get_pesadas_acumuladas(puerto_id=puerto_id)
        log.info(f"Consulta de pesadas para flota {puerto_id} realizada exitosamente.")
        return pesadas

    except HTTPException as http_exc:
        log.error(f"Consulta de flota {puerto_id} no pudo realizarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )
    except EntityNotFoundException as e:
        raise e
    except Exception as e:
        log.error(f"Error al consultar pesadas de flota {puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.get("/envio-final/{puerto_id}",
             status_code=status.HTTP_200_OK,
             summary="Envio final (previsión): mostrar la sumatoria de pesadas pendientes para la última transacción",
             description="Muestra qué sería enviado en el envio final: la sumatoria de las pesadas pendientes (leido=False) correspondiente a la última transacción del puerto. "
                         "No notifica a la API externa.",
             response_model=List[VPesadasAcumResponse],
             responses={
                 status.HTTP_404_NOT_FOUND: {"model": ErrorResponse},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
             })
async def envio_final(
        puerto_id: str,
        service: PesadasService = Depends(get_pesadas_service)):
    try:
        # Obtener sólo las pesadas pendientes (leido=False) correspondientes a la última transacción del puerto
        pesadas = await service.get_pending_for_last_transaccion(puerto_id=puerto_id)
        log.info(f"EnvioFinal (preview): consulta de pesadas pendientes para flota {puerto_id} realizada exitosamente. items={len(pesadas)}")

        if not pesadas:
            return response_json(status_code=status.HTTP_404_NOT_FOUND, message="No se encontraron pesadas pendientes para el puerto especificado")

        return pesadas

    except HTTPException as http_exc:
        log.error(f"EnvioFinal (preview): consulta de flota {puerto_id} no pudo realizarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )
    except EntityNotFoundException as e:
        raise e
    except Exception as e:
        log.error(f"EnvioFinal (preview): Error al consultar pesadas pendientes de flota {puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

@router.post("/envio-final/{puerto_id}/notify",
             status_code=status.HTTP_200_OK,
             summary="Notificar Envio Final a API externa",
             description="Obtiene la lista de envio final y la notifica a la API externa. "
                         "mode='auto' usa la configuración TG_API_ACCEPTS_LIST; "
                         "'list' fuerza envío único con lista; "
                         "'single' envía item-por-item."
                         "Corresponde a EnvioFinal en el diagrama de flujo de proceso.",
             responses={
                 status.HTTP_400_BAD_REQUEST: {"model": ErrorResponse},
                 status.HTTP_424_FAILED_DEPENDENCY: {"model": ErrorResponse},
                 status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": ErrorResponse},
             })
async def envio_final_notify(
        puerto_id: str,
        mode: str = 'last',
        service: PesadasService = Depends(get_pesadas_service),
        viajes_service: ViajesService = Depends(get_viajes_service)):
    try:
        # Obtener sólo las pesadas pendientes (leido=False) correspondientes a la última transacción del puerto
        pesadas = await service.get_pending_for_last_transaccion(puerto_id=puerto_id)
        log.info(f"EnvioFinal notify: obtenida lista de pendientes para {puerto_id} con {len(pesadas)} items (última transacción)")

        await notify_envio_final(puerto_id, pesadas, viajes_service, mode=mode)

        return response_json(status_code=status.HTTP_200_OK, message="Notificación enviada")

    except HTTPException as http_exc:
        log.error(f"EnvioFinal notify: consulta de flota {puerto_id} no pudo realizarse: {http_exc.detail}")
        return response_json(
            status_code=http_exc.status_code,
            message=http_exc.detail
        )
    except EntityNotFoundException as e:
        raise e
    except Exception as e:
        log.error(f"EnvioFinal notify: Error al notificar pesadas de flota {puerto_id}: {e}")
        return response_json(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message=str(e)
        )

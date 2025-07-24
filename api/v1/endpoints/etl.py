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


response_json = ResponseUtil().json_response
router = APIRouter(prefix="/scada", tags=["Automatizador"], dependencies=[Depends(AuthService.get_current_user)]) #

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


@router.get("/camiones-listado/{placa}",
            summary="Obtener listado paginado de camiones con filtro opcional por placa",
            description="Retorna camiones en modo páginado, filtradas opcionalmente por placa específica",
            response_model=Page[VViajesResponse])
async def get_camiones_paginado(
    viajes_service: ViajesService = Depends(get_viajes_service),
    truck_plate: Optional[str] = Query(None, description="Placa específica a buscar")
):
    return await viajes_service.get_pag_camiones_activos(truck_plate)

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
        service: FlotasService = Depends(get_flotas_service)):
    try:

        await service.chg_points(truck_plate, points)
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


@router.get("/materiales-listado/",
            summary="Obtener listado de materiales",
            description="Método de consulta de materiales empleados en el puerto",
            response_model=List[MaterialesResponse])
async def get_materiales_listado(
    mat_service: MaterialesService = Depends(get_mat_service)):
    return  await mat_service.get_all_mat()


@router.get("/movimientos-listado/{transaccion_id}",
            summary="Obtener listado paginado de movimientos con filtro opcional por transacción",
            description="Retorna movimientos en modo páginado, filtradas opcionalmente por un id de transacción específico",
            response_model=Page[MovimientosResponse])
async def get_movs_listado(
    mov_service: MovimientosService = Depends(get_mov_service),
    tran_id: Optional[int] = Query(None, description="Id de Transacción específico a buscar")
):
    movimientos = await mov_service.get_pag_movimientos(tran_id)
    return movimientos


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
    try:
        pesada_result, was_created = await service.create_pesada_if_not_exists(pesada)

        if was_created:
            return response_json(
                status_code=status.HTTP_201_CREATED,
                message="registro exitoso."
            )
        else:
            return response_json(
                status_code=status.HTTP_200_OK,
                message="registro fallído, la pesada ya existe."
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
    response_model=Page[PesadaResponse]
)
async def get_pesadas_listado(
    pesada_service: PesadasService = Depends(get_pesadas_service),
    tran_id: Optional[int] = Query(None, description="Id de Transacción específico a buscar")
):
    return await pesada_service.get_pag_pesadas(tran_id)



@router.get("/transacciones-listado/{transaccion_id}",
            summary="Obtener listado paginado de transacciones con filtro opcional",
            description="Retorna transacciones en modo páginado, filtradas opcionalmente por un id de transacción específico",
            response_model=Page[TransaccionResponse])
async def get_trans_listado(
    tran_service: TransaccionesService = Depends(get_transacciones_service),
    tran_id: Optional[int] = Query(None, description="Id de Transacción específico a buscar")

):
    return  await tran_service.get_pag_transacciones(tran_id)


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
    transaccion: TransaccionCreate,
    service: TransaccionesService = Depends(get_transacciones_service),
):
    try:
        transaccion_result, was_created = await service.create_transaccion_if_not_exists(transaccion)

        if was_created:
            return response_json(
                status_code=status.HTTP_201_CREATED,
                message="registro exitoso."
            )
        else:
            return response_json(
                status_code=status.HTTP_200_OK,
                message="registro fallído, la transacción ya existe."
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
        service: FlotasService = Depends(get_flotas_service)):
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
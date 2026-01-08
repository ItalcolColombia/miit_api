from typing import Annotated

from fastapi import Depends

from repositories.almacenamientos_materiales_repository import AlmacenamientosMaterialesRepository
# Repositories
from repositories.almacenamientos_repository import AlmacenamientosRepository
from repositories.bls_repository import BlsRepository
from repositories.clientes_repository import ClientesRepository
from repositories.flotas_repository import FlotasRepository
from repositories.materiales_repository import MaterialesRepository
from repositories.movimientos_repository import MovimientosRepository
from repositories.pesadas_corte_repository import PesadasCorteRepository
from repositories.pesadas_repository import PesadasRepository
from repositories.transacciones_repository import TransaccionesRepository
from repositories.usuarios_repository import UsuariosRepository
from repositories.viajes_repository import ViajesRepository
from repositories.ajustes_repository import AjustesRepository
from repositories.reportes.reportes_repository import ReportesRepository
from services.almacenamientos_materiales_service import AlmacenamientosMaterialesService
from services.almacenamientos_service import AlmacenamientosService
# Services
from services.auth_service import AuthService
from services.bls_service import BlsService
from services.clientes_service import ClientesService
from services.ext_api_service import ExtApiService
from services.flotas_service import FlotasService
from services.materiales_service import MaterialesService
from services.movimientos_service import MovimientosService
from services.pesadas_service import PesadasService
from services.transacciones_service import TransaccionesService
from services.usuarios_service import UsuariosService
from services.viajes_service import ViajesService
from services.ajustes_service import AjustesService
from services.reportes.reportes_service import ReportesService
from services.reportes.exportacion_service import ExportacionService
# InjectionRepo
from .repository_injection import (
    get_user_repository,
    get_bls_repository,
    get_clientes_repository,
    get_viajes_repository,
    get_flotas_repository,
    get_alm_repository,
    get_alm_mat_repository,
    get_materiales_repository,
    get_movimientos_repository,
    get_pesadas_repository,
    get_pesadas_corte_repository,
    get_transacciones_repository,
    get_ajustes_repository,
    get_auditor_service,
    get_reportes_repository,
)
from core.contracts.auditor import Auditor


async def get_auth_service(
        user_repository: UsuariosRepository = Depends(get_user_repository)
) -> AuthService:
    return AuthService(user_repository)


async def get_alm_service(
        alm_repository: AlmacenamientosRepository = Depends(get_alm_repository)
) -> AlmacenamientosService:
    return AlmacenamientosService(alm_repository)


async def get_alm_mat_service(
        alm_mat_repository: AlmacenamientosMaterialesRepository = Depends(get_alm_mat_repository)
) -> AlmacenamientosMaterialesService:
    return AlmacenamientosMaterialesService(alm_mat_repository)


async def get_flotas_service(
        flotas_repository: FlotasRepository = Depends(get_flotas_repository)
) -> FlotasService:
    return FlotasService(flotas_repository)


async def get_bls_service(
        bls_repository: BlsRepository = Depends(get_bls_repository)
) -> BlsService:
    return BlsService(bls_repository)


async def get_clientes_service(
        clientes_repository: ClientesRepository = Depends(get_clientes_repository),
) -> ClientesService:
    return ClientesService(clientes_repository)


async def get_mat_service(
        materiales_repository: MaterialesRepository = Depends(get_materiales_repository)
) -> MaterialesService:
    return MaterialesService(materiales_repository)


async def get_ext_api_service() -> ExtApiService:
    return ExtApiService()


async def get_mov_service(
        movimientos_repository: MovimientosRepository = Depends(get_movimientos_repository)
) -> MovimientosService:
    return MovimientosService(movimientos_repository)


async def get_pesadas_service(
        pesadas_repository: PesadasRepository = Depends(get_pesadas_repository),
        pesadas_corte_repository: PesadasCorteRepository = Depends(get_pesadas_corte_repository),
        trans_repository: TransaccionesRepository = Depends(get_transacciones_repository),
) -> PesadasService:
    return PesadasService(pesadas_repository, pesadas_corte_repository, trans_repository)


async def get_transacciones_service(
        trans_repository: Annotated[TransaccionesRepository, Depends(get_transacciones_repository)],
        pesadas_service: Annotated[PesadasService, Depends(get_pesadas_service)],
        mov_service: Annotated[MovimientosService, Depends(get_mov_service)],
) -> TransaccionesService:
    return TransaccionesService(
        tran_repository=trans_repository,
        pesadas_service=pesadas_service,
        mov_service=mov_service,
    )


async def get_viajes_service(
        viajes_repository: Annotated[ViajesRepository, Depends(get_viajes_repository)],
        materiales_service: Annotated[MaterialesService, Depends(get_mat_service)],
        bls_service: Annotated[BlsService, Depends(get_bls_service)],
        clientes_service: Annotated[ClientesService, Depends(get_clientes_service)],
        flotas_service: Annotated[FlotasService, Depends(get_flotas_service)],
        feedback_service: Annotated[ExtApiService, Depends(get_ext_api_service)],
        transacciones_service: Annotated[TransaccionesService, Depends(get_transacciones_service)],
) -> ViajesService:
    return ViajesService(
        viajes_repository=viajes_repository,
        mat_service=materiales_service,
        flotas_service=flotas_service,
        feedback_service=feedback_service,
        bl_service=bls_service,
        client_service=clientes_service,
        transacciones_service=transacciones_service
    )


async def get_user_service(
        user_repository: UsuariosRepository = Depends(get_user_repository)
) -> UsuariosService:
    return UsuariosService(user_repository)


async def get_ajustes_service(
        ajustes_repository: Annotated[AjustesRepository, Depends(get_ajustes_repository)],
        movimientos_repository: Annotated[MovimientosRepository, Depends(get_movimientos_repository)],
        alm_mat_repository: Annotated[AlmacenamientosMaterialesRepository, Depends(get_alm_mat_repository)],
        auditor: Annotated[Auditor, Depends(get_auditor_service)],
) -> AjustesService:
    return AjustesService(ajustes_repository, movimientos_repository, alm_mat_repository, auditor)


# ============================================================
# INYECCIÓN DE DEPENDENCIAS PARA REPORTES
# ============================================================

async def get_reportes_service(
        reportes_repository: ReportesRepository = Depends(get_reportes_repository)
) -> ReportesService:
    """
    Inyección de dependencias para el servicio de reportes.

    Args:
        reportes_repository: Repositorio de reportes inyectado automáticamente

    Returns:
        Instancia del servicio de reportes
    """
    return ReportesService(reportes_repository)


async def get_exportacion_service() -> ExportacionService:
    """
    Inyección de dependencias para el servicio de exportación.

    Este servicio no requiere dependencias externas ya que es stateless
    y no accede directamente a la base de datos.

    Returns:
        Instancia del servicio de exportación
    """
    return ExportacionService()
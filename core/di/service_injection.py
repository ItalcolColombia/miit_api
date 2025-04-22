from fastapi import Depends
from typing import Annotated

# Repositories
from repositories.almacenamientos_repository import AlmacenamientosRepository
from repositories.buques_repository import BuquesRepository
from repositories.camiones_repository import CamionesRepository
from repositories.flotas_repository import FlotasRepository
from repositories.materiales_repository import MaterialesRepository
from repositories.movimientos_repository import MovimientosRepository
from repositories.pesadas_repository import PesadasRepository
from repositories.transacciones_repository import TransaccionesRepository
from repositories.usuarios_repository import UsuariosRepository

# Services
from services.auth_service import AuthService
from services.almacenamientos_service import AlmacenamientosService
from services.buques_service import BuquesService
from services.camiones_service import CamionesService
from services.flotas_service import FlotasService
from services.materiales_service import MaterialesService
from services.movimientos_service import MovimientosService
from services.pesadas_service import PesadasService
from services.transacciones_service import TransaccionesService
from services.usuarios_service import UsuariosService

# InjectionRepo
from .repository_injection import (
    get_user_repository,
    get_flotas_repository,
    get_buques_repository,
    get_camiones_repository,
    get_alm_repository,
    get_materiales_repository,
    get_movimientos_repository,
    get_pesadas_repository,
    get_transacciones_repository
)

async def get_auth_service(
    user_repository: UsuariosRepository = Depends(get_user_repository)
) -> AuthService:
    return AuthService(user_repository)

async def get_alm_service(
    alm_repository: AlmacenamientosRepository = Depends(get_alm_repository)
) -> AlmacenamientosService:
    return AlmacenamientosService(alm_repository)

async def get_buques_service(
    buques_repository: BuquesRepository = Depends(get_buques_repository),
) -> BuquesService:
    return BuquesService(buques_repository)

async def get_camiones_service(
    camiones_repository: CamionesRepository = Depends(get_camiones_repository),
) -> CamionesService:
    return CamionesService(camiones_repository)

async def get_mat_service(
    materiales_repository: MaterialesRepository = Depends(get_materiales_repository)
) -> MaterialesService:
    return MaterialesService(materiales_repository)

async def get_flotas_service(
    flotas_repository: Annotated[FlotasRepository, Depends(get_flotas_repository)],
    materiales_service: Annotated[MaterialesService, Depends(get_mat_service)],
    buques_service: Annotated[BuquesService, Depends(get_buques_service)],
    camiones_service: Annotated[CamionesService, Depends(get_camiones_service)],
) -> FlotasService:
    return FlotasService(
        flotas_repository=flotas_repository,
        mat_service=materiales_service,
        buque_service=buques_service,
        camion_service=camiones_service
    )

async def get_mov_service(
    movimientos_repository: MovimientosRepository = Depends(get_movimientos_repository)
) -> MovimientosService:
    return MovimientosService(movimientos_repository)


async def get_pesadas_service(
    pesadas_repository: PesadasRepository = Depends(get_pesadas_repository)
) -> PesadasService:
    return PesadasService(pesadas_repository)

async def get_transacciones_service(
    trans_repository: TransaccionesRepository = Depends(get_transacciones_repository)
) -> TransaccionesService:
    return TransaccionesService(trans_repository)


async def get_user_service(
    user_repository: UsuariosRepository = Depends(get_user_repository)
) -> UsuariosService:
    return UsuariosService(user_repository)



# async def get_employee_reports_service(
#     employee_repository: IRepository = Depends(get_flotas_repository)
# ) -> EmployeeReportsService:
#     return EmployeeReportsService(employee_repository)
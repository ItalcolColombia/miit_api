from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import (
    Usuarios,
    Flotas,
    Bls,
    Clientes,
    Materiales,
    Almacenamientos,
    AlmacenamientosMateriales,
    Movimientos,
    Pesadas,
    Transacciones,
    Viajes, PesadasCorte
)
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
from schemas.almacenamientos_materiales_schema import AlmacenamientoMaterialesResponse
# Schemas
from schemas.almacenamientos_schema import AlmacenamientoResponse
from schemas.bls_schema import BlsResponse
from schemas.clientes_schema import ClientesResponse
from schemas.flotas_schema import FlotasResponse
from schemas.materiales_schema import MaterialesResponse
from schemas.movimientos_schema import MovimientosResponse
from schemas.pesadas_corte_schema import PesadasCorteResponse
from schemas.pesadas_schema import PesadaResponse
from schemas.transacciones_schema import TransaccionResponse
from schemas.usuarios_schema import UsuariosResponse
from schemas.viajes_schema import ViajesResponse
from services.logs_auditoria_service import DatabaseAuditor
from .database_injection import get_db


async def get_auditor_service(
        session: AsyncSession = Depends(get_db)
) -> Auditor:
    return DatabaseAuditor(session)

async def get_user_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> UsuariosRepository:
    return UsuariosRepository(Usuarios, UsuariosResponse, session, auditor)

async def get_viajes_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> ViajesRepository:
    return ViajesRepository(Viajes, ViajesResponse, session, auditor)

async def get_alm_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> AlmacenamientosRepository:
    return AlmacenamientosRepository(Almacenamientos, AlmacenamientoResponse, session, auditor)

async def get_alm_mat_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> AlmacenamientosMaterialesRepository:
    return AlmacenamientosMaterialesRepository(AlmacenamientosMateriales, AlmacenamientoMaterialesResponse, session, auditor)


async def get_flotas_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> FlotasRepository:
    return FlotasRepository(Flotas, FlotasResponse, session, auditor)


async def get_bls_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> BlsRepository:
    return BlsRepository(Bls, BlsResponse, session, auditor)

async def get_clientes_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> ClientesRepository:
    return ClientesRepository(Clientes, ClientesResponse, session, auditor)

async def get_materiales_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> MaterialesRepository:
    return MaterialesRepository(Materiales, MaterialesResponse, session, auditor)

async def get_movimientos_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> MovimientosRepository:
    return MovimientosRepository(Movimientos, MovimientosResponse, session, auditor)

async def get_pesadas_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> PesadasRepository:
    return PesadasRepository(Pesadas, PesadaResponse, session, auditor)

async def get_pesadas_corte_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> PesadasCorteRepository:
    return PesadasCorteRepository(PesadasCorte, PesadasCorteResponse, session, auditor)

async def get_transacciones_repository(
        session: AsyncSession = Depends(get_db),
        auditor: Auditor = Depends(get_auditor_service)
) -> TransaccionesRepository:
    return TransaccionesRepository(Transacciones, TransaccionResponse, session, auditor)
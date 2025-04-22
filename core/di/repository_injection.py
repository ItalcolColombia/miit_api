from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from .database_injection import get_db
from database.models import (
    Usuarios,
    Flotas,
    Materiales,
    Buques,
    Camiones,
    Almacenamientos,
    Movimientos,
    Pesadas,
    Transacciones
)

# Repositories
from repositories.almacenamientos_repository import AlmacenamientosRepository
from repositories.buques_repository import BuquesRepository
from repositories.camiones_repository import CamionesRepository
from repositories.flotas_repository import FlotasRepository
from repositories.materiales_repository import MaterialesRepository
from repositories.movimientos_repository import MovimientosRepository
from  repositories.pesadas_repository import PesadasRepository
from  repositories.transacciones_repository import TransaccionesRepository
from repositories.usuarios_repository import UsuariosRepository

# Schemas
from schemas.almacenamientos_schema import  AlmacenamientoResponse
from schemas.buques_schema import BuquesResponse
from schemas.camiones_schema import CamionResponse
from schemas.flotas_schema import FlotasResponse
from schemas.materiales_schema import MaterialesResponse
from schemas.movimientos_schema import MovimientosResponse
from schemas.pesadas_schema import PesadaResponse
from schemas.transacciones_schema import TransaccionResponse
from schemas.usuarios_schema import UsuariosResponse


async def get_user_repository(
    session: AsyncSession = Depends(get_db)
) -> UsuariosRepository:
    return UsuariosRepository(Usuarios, UsuariosResponse, session)

async def get_flotas_repository(
    session: AsyncSession = Depends(get_db)
) -> FlotasRepository:
    return FlotasRepository(Flotas, FlotasResponse, session)

async def get_alm_repository(
    session: AsyncSession = Depends(get_db)
) -> AlmacenamientosRepository:
    return AlmacenamientosRepository(Almacenamientos, AlmacenamientoResponse, session)

async def get_buques_repository(
        session: AsyncSession = Depends(get_db)
) -> BuquesRepository:
    return BuquesRepository(Buques, BuquesResponse, session)

async def get_camiones_repository(
        session: AsyncSession = Depends(get_db)
) -> CamionesRepository:
    return CamionesRepository(Camiones, CamionResponse, session)

async def get_materiales_repository(
    session: AsyncSession = Depends(get_db)
) -> MaterialesRepository:
    return MaterialesRepository(Materiales, MaterialesResponse, session)

async def get_movimientos_repository(
    session: AsyncSession = Depends(get_db)
) -> MovimientosRepository:
    return MovimientosRepository(Movimientos, MovimientosResponse, session)

async def get_pesadas_repository(
    session: AsyncSession = Depends(get_db)
) -> PesadasRepository:
    return PesadasRepository(Pesadas, PesadaResponse, session)

async def get_transacciones_repository(
    session: AsyncSession = Depends(get_db)
) -> TransaccionesRepository:
    return TransaccionesRepository(Transacciones, TransaccionResponse, session)
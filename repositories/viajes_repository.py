from typing import List, Optional

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from core.contracts.auditor import Auditor
from database.models import Viajes, VViajes, Flotas, Bls, Materiales
from repositories.base_repository import IRepository
from schemas.viajes_schema import ViajesResponse, ViajesActResponse
from utils.logger_util import LoggerUtil
from utils.time_util import now_local

log = LoggerUtil()


class ViajesRepository(IRepository[Viajes, ViajesResponse]):
    db: AsyncSession

    def __init__(self, model: type[Viajes], schema: type[ViajesResponse], db: AsyncSession, auditor:Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def get_buques_disponibles(self) -> List[ViajesActResponse] | None:
        """
                Filter buques which _operador = True

                Returns:
                    A list of Buques objects matching the filter, otherwise, returns a null.
                """
        query = (
            select(VViajes)
            .where(VViajes.tipo == 'buque')
            .where(VViajes.estado_operador == True)
        )
        result = await self.db.execute(query)
        viajes = result.scalars().all()

        if not viajes:
            return None

        return [ViajesActResponse.model_validate(viaje) for viaje in viajes]



    async def check_puerto_id(self, puerto_id: str) -> Optional[ViajesResponse]:
        """
        Find an existing viaje by 'puerto_id' value

        Args:
            puerto_id: The value to filter.

        Returns:
            A viaje object based on their puerto_id value.
        """
        try:
            result = await self.db.execute(
                select(self.model)
                .filter(self.model.puerto_id == puerto_id)
                .limit(1)  # Limitar a un solo resultado para evitar error de múltiples filas
            )
            flota = result.scalar_one_or_none()
            if flota:
                log.info(f"Viaje con puerto_id '{puerto_id}' verificado.")
                return self.schema.model_validate(flota)
            else:
                log.warning(f"No se encontró Viaje con puerto_id'{puerto_id}'.")
                return None
        except Exception as e:
            log.error(f"Error al intentar checar Viaje con puerto_id '{puerto_id}': {e}")
            raise

    async def get_viajes_activos_por_material(self, tipo_flota: str) -> List[dict] | None:
        """
        Obtener viajes activos agrupados por material.

        Para buques: agrupa los BLs por material
        Para camiones: usa el material_id del viaje

        Args:
            tipo_flota: 'buque' o 'camion'

        Returns:
            Lista de diccionarios con consecutivo, nombre, material y puntos_cargue ordenados por consecutivo (id) descendente
        """
        try:
            # Obtener fecha/hora actual en la zona horaria de la app (tz-aware)
            fecha_actual = now_local()
            log.info(f"[DEBUG get_viajes_activos_por_material] tipo_flota={tipo_flota}, fecha_actual={fecha_actual} (tzinfo={getattr(fecha_actual, 'tzinfo', None)})")

            if tipo_flota.lower() == 'buque':
                # Para buques, agrupamos por los materiales de los BLs
                # Usamos group_by para evitar duplicados por la misma combinación flota+material
                # Filtramos por viajes cuya fecha_llegada <= ahora Y (fecha_salida es nula O fecha_salida >= ahora)
                query = (
                    select(
                        func.max(Viajes.id).label('consecutivo'),
                        Flotas.referencia.label('nombre'),
                        Materiales.nombre.label('material'),
                        Flotas.puntos.label('puntos_cargue'),
                        func.max(Viajes.peso_meta).label('peso'),
                        func.max(Viajes.fecha_hora).label('fecha_hora_orden')
                    )
                    .join(Flotas, Viajes.flota_id == Flotas.id)
                    .join(Bls, Bls.viaje_id == Viajes.id)
                    .join(Materiales, Bls.material_id == Materiales.id)
                    .where(Flotas.tipo == 'buque')
                    .where(Flotas.estado_operador == True)
                    .where(
                        and_(
                            Viajes.fecha_llegada <= fecha_actual,
                            or_(
                                Viajes.fecha_salida.is_(None),
                                Viajes.fecha_salida >= fecha_actual
                            )
                        )
                    )
                    .group_by(Flotas.referencia, Materiales.nombre, Flotas.puntos)
                    .order_by(func.max(Viajes.id).desc())
                )
            else:  # camion
                # Para camiones, usamos el material_id del viaje
                # Usamos group_by para evitar duplicados por la misma combinación flota+material
                # Filtramos por viajes cuya fecha_llegada <= ahora Y (fecha_salida es nula O fecha_salida >= ahora)
                query = (
                    select(
                        func.max(Viajes.id).label('consecutivo'),
                        Flotas.referencia.label('nombre'),
                        Materiales.nombre.label('material'),
                        Flotas.puntos.label('puntos_cargue'),
                        func.max(Viajes.peso_meta).label('peso'),
                        func.max(Viajes.fecha_hora).label('fecha_hora_orden')
                    )
                    .join(Flotas, Viajes.flota_id == Flotas.id)
                    .join(Materiales, Viajes.material_id == Materiales.id)
                    .where(Flotas.tipo == 'camion')
                    .where(Flotas.estado_operador == True)
                    .where(Viajes.material_id.isnot(None))
                    .where(
                        and_(
                            Viajes.fecha_llegada <= fecha_actual,
                            or_(
                                Viajes.fecha_salida.is_(None),
                                Viajes.fecha_salida >= fecha_actual
                            )
                        )
                    )
                    .group_by(Flotas.referencia, Materiales.nombre, Flotas.puntos)
                    .order_by(func.max(Viajes.id).desc())
                )

            result = await self.db.execute(query)
            viajes = result.fetchall()

            if not viajes:
                return None

            # Convertir a lista de diccionarios
            return [
                {
                    'consecutivo': viaje.consecutivo,
                    'nombre': viaje.nombre,
                    'material': viaje.material,
                    'puntos_cargue': viaje.puntos_cargue,
                    'peso': viaje.peso
                }
                for viaje in viajes
            ]

        except Exception as e:
            log.error(f"Error al obtener viajes activos por material: {e}")
            raise

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.exc import NoResultFound

from core.contracts.auditor import Auditor
from database.models import Viajes, VViajes
from repositories.base_repository import IRepository
from schemas.viajes_schema import ViajesResponse, ViajesActResponse
from utils.logger_util import LoggerUtil

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
            result = await self.db.execute(select(self.model).filter(self.model.puerto_id == puerto_id))
            flota = result.scalar_one()
            if flota:
                log.info(f"Viaje con puerto_id '{puerto_id}' verificado.")
                return self.schema.model_validate(flota)
            else:
                return None
        except NoResultFound:
            log.warning(f"No se encontró Viaje con puerto_id'{puerto_id}'.")
            return None
        except Exception as e:
            log.error(f"Error al intentar checar Viaje con puerto_id '{puerto_id}': {e}")
            raise
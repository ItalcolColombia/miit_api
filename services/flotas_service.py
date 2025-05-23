from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Flotas
from schemas.flotas_schema import FlotasResponse, FlotaCreate, FlotaUpdate
from repositories.flotas_repository import FlotasRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class FlotasService:

    def __init__(self, flotas_repository: FlotasRepository) -> None:
        self._repo = flotas_repository

    async def create_flota(self, flota_data: FlotaCreate) -> FlotasResponse:
        flota_model = Flotas(**flota_data.dict())
        created_flota = await self._repo.create(flota_model)
        log.info(f"Flota creada con referencia: {created_flota.referencia}")
        return FlotasResponse.model_validate(created_flota)

    async def update_flota(self, id: int, flota_data: FlotasResponse) -> Optional[FlotasResponse]:
        flota_model = Flotas(**flota_data.dict())
        updated_flota = await self._repo.update(id, flota_model)
        log.info(f"Flota actualizada con ID: {id}")
        return FlotasResponse.model_validate(updated_flota)

    async def delete_flota(self, id: int) -> bool:
        deleted = await self._repo.delete(id)
        log.info(f"Flota eliminada con ID: {id}")
        return deleted

    async def get_flota(self, id: int) -> Optional[FlotasResponse]:
        flota = await self._repo.get_by_id(id)
        return FlotasResponse.model_validate(flota) if flota else None

    async def get_all_flotas(self) -> List[FlotasResponse]:
        flotas = await self._repo.get_all()
        return [FlotasResponse.model_validate(f) for f in flotas]

    async def get_flota_by_ref(self, ref: str) -> Optional[FlotasResponse]:
        """
               Find a Flota by their 'referencia'

               Args:
                   ref: The flota reference param to filter.

               Returns:
                   Flota object filtered by 'referencia'.
       """
        flota = await self._repo.get_flota_by_ref(ref)
        return FlotasResponse.model_validate(flota) if flota else None


    async def create_flota_if_not_exists(self, flota_data: FlotaCreate) -> FlotasResponse:
        """
               Check if a Flota already exists. If not, create a new one.

               Args:
                   flota_data: The schema of Flota object.

               Returns:
                   The existing or newly created Flota
       """
        try:
            flota_existente = await self._repo.get_flota_by_ref(flota_data.referencia)
            if flota_existente:
                log.info(f"Flota ya existente con referencia: {flota_data.referencia}")
                return FlotasResponse.model_validate(flota_existente)

            flota_creada = await self._repo.create(flota_data)
            log.info(f"Se creó flota: {flota_creada.referencia}")
            return FlotasResponse.model_validate(flota_creada)

        except Exception as e:
            log.error(f"Error al crear o consultar flota: {flota_data.referencia} - {e}")
            raise

    async def update_status(self, flota: Flotas, estado: bool ) -> FlotasResponse:
        """
                      Updates the 'estado' for an existing Flota.

                      This method updates the 'estado' value of a Flota in the database.

                      Args:
                          flota: The Flota object whose status needs to be updated.
                          estado: The new boolean value for the Flota's status (e.g., True for active, False for inactive).

                      Returns:
                          The Flota object after its status has been updated.

                      Raises:
                          Exception: If an error occurs during the update operation.
               """
        try:
            update_data = FlotaUpdate(estado=estado)
            updated = await self._repo.update(flota.id, update_data)
            log.info(f"Estado modificado para flota {flota.referencia} a {estado}")
            return FlotasResponse.model_validate(updated)

        except Exception as e:
            log.error(f"Error al cambiar estado de flota: {flota.referencia} - {e}")
            raise



    async def update_points(self, flota: Flotas, points: int ) -> FlotasResponse:
        """
                      Updates the 'puntos' (points) for an existing Flota.

                      This method updates the 'puntos' value of a Flota in the database.
                      It returns the updated Flota object.

                      Args:
                          flota: The Flota object whose points need to be updated.
                          points: The new integer value for the Flota's points.

                      Returns:
                          The Flota object after its points have been updated.

                      Raises:
                          Exception: If an error occurs during the update operation.
        """
        try:
            update_data = FlotaUpdate(puntos=points)
            updated = await self._repo.update(flota.id, update_data)
            log.info(f"Puntos actualizados para flota: {flota.referencia} a {points}")
            return FlotasResponse.model_validate(updated)

        except Exception as e:
            log.error(f"Error al cambiar puntos de flota: {flota.referencia} - {e}")
            raise

    async def chg_points(self, ref: str, points: int) -> FlotasResponse:
        flota = await self.get_flota_by_ref(ref)
        if not flota:
            raise BaseException(f"Flota con referencia: '{ref}' no encontrada")

        updated_buque = await self.update_points(flota, points)
        return updated_buque
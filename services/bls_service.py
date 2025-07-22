from typing import List, Optional
from database.models import Bls
from schemas.bls_schema import BlsResponse, BlsCreate, BlsUpdate
from repositories.bls_repository import BlsRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class BlsService:

    def __init__(self, bls_repository: BlsRepository) -> None:
        self._repo = bls_repository

    async def create(self, bl: BlsCreate) -> BlsResponse:
        creado = await self._repo.create(bl)
        log.info(f"BL creado con N°: {bl.no_bl}")
        return creado

    async def update(self, id: int, bl: BlsResponse) -> Optional[BlsResponse]:
        actualizado = await self._repo.update(id, bl)
        log.info(f"BL actualizado con ID: {id}")
        return actualizado

    async def delete(self, id: int) -> bool:
        deleted = await self._repo.delete(id)
        log.info(f"BL eliminado con ID: {id}")
        return deleted

    async def get(self, id: int) -> Optional[BlsResponse]:
        bl = await self._repo.get_by_id(id)
        return BlsResponse.model_validate(bl) if bl else None

    async def get_all(self) -> List[BlsResponse]:
        bls = await self._repo.get_all()
        return [BlsResponse.model_validate(bl) for bl in bls]



    async def create_bl_if_not_exitst(self, bl_data: BlsCreate) -> BlsResponse:
        """
               Check if a BL already exists. If not, create a new one.

               Args:
                   bl_data: The schema of BL object.

               Returns:
                   The existing or newly created BL
       """
        try:
            bl_existente = await self._repo.get_bls_no_bl(bl_data.no_bl)
            if bl_existente:
                log.info(f"BL ya existente con N°: {bl_data.no_bl}")
                return BlsResponse.model_validate(bl_existente)

            bl_creado = await self._repo.create(bl_data)
            log.info(f"Se creó BL: {bl_creado.no_bl}")
            return BlsResponse.model_validate(bl_creado)

        except Exception as e:
            log.error(f"Error al crear o consultar BL: {bl_data.referencia} - {e}")
            raise

    async def get_bl_by_num(self, number: str) -> Optional[BlsResponse]:
        """
         Find a Bl by their 'number'

         Args:
             number: The Bl number param to filter.

         Returns:
             Bl object filtered by 'number'.
         """
        return await self._repo.get_bls_no_bl(number)
   
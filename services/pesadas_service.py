from typing import List, Optional
from fastapi_pagination import Page, Params

from sqlalchemy import select

from core.exceptions.entity_exceptions import EntityNotFoundException, EntityAlreadyRegisteredException
from database.models import Pesadas, VPesadasAcumulado
from schemas.pesadas_schema import PesadaResponse, PesadaCreate, PesadaUpdate, VPesadasAcumResponse
from repositories.pesadas_repository import PesadasRepository

from utils.logger_util import LoggerUtil
log = LoggerUtil()

class PesadasService:

    def __init__(self, pesada_repository: PesadasRepository) -> None:
        self._repo = pesada_repository


    async def create_pesada(self, pesada_data: PesadaCreate) -> PesadaResponse:
        pesada_model = Pesadas(**pesada_data.dict())
        created_flota = await self._repo.create(pesada_model)
        log.info(f"Pesada creada con referencia: {created_flota.referencia}")
        return PesadaResponse.model_validate(created_flota)

    async def update_pesada( self, id: int, pesada: PesadaUpdate) -> Optional[PesadaResponse]:
        pesada_model = Pesadas(**pesada.dict())
        updated_flota = await self._repo.update(id, pesada_model)
        log.info(f"Pesada actualizada con ID: {id}")
        return PesadaResponse.model_validate(updated_flota)

    async def delete_pesada(self, id: int) -> bool:
        deleted = await self._repo.delete(id)
        log.info(f"Pesada eliminada con ID: {id}")
        return deleted

    async def get_pesada(self, id: int) -> Optional[PesadaResponse]:
        pesada = await self._repo.get_by_id(id)
        return PesadaResponse.model_validate(pesada) if pesada else None

    async def get_pag_pesadas(self, tran_id: Optional[int] = None, params: Params = Params()) -> Page[PesadaResponse]:
        """
              Get one or more pesadas related to an id_transaccion.
              Returns a page with filtered optionally transaction ID pesadas.
              """
        query = select(Pesadas)

        if tran_id is not None:
            query = query.where(Pesadas.transaccion_id == tran_id)

        return await self._repo.get_all_paginated(query=query, params=params)

    async def get_all_pesadas(self) -> List[PesadaResponse]:
        pesadas = await self._repo.get_all()
        return [PesadaResponse.model_validate(p) for p in pesadas]

    async def create_pesada_if_not_exists(self, pesada_data: PesadaCreate) -> PesadaResponse:
        """
               Check if a Pesada with same consec already exists. If not, create a new one.

               Args:
                   pesada_data: The data set in the schema of Pesada object.

               Returns:
                   An existing or newly created Pesada.
       """

        # 1. Validar si transacción ya existe
        if await self._repo.find_one(transaccion_id=pesada_data.transaccion_id,
                                     consecutivo=pesada_data.consecutivo
        ):
            raise EntityAlreadyRegisteredException(f"En la transacción {pesada_data.transaccion_id} ya existe una pesada con ese consecutivo '{pesada_data.consecutivo}'")

        # 2. Se crea transacción si esta no existe en la BD
        pesada_nueva = await self._repo.create(pesada_data)
        return pesada_nueva

    async def get_pesada_acumulada(self, puerto_id: [str]) -> VPesadasAcumResponse:
        """
             Get sum of pesadas related to a puerto_id.
             Returns an object with filtered applied.
             """
        pesada = await self._repo.get_sumatoria_pesadas(puerto_id)

        if pesada is None:
            raise EntityNotFoundException(f"No se encontraron registros de pesadas para la flota '{puerto_id}'")

        return pesada
from typing import List, Optional
from database.models import Bls
from repositories.clientes_repository import ClientesRepository
from schemas.clientes_schema import ClientesResponse, ClienteCreate, ClienteUpdate

from utils.logger_util import LoggerUtil

log = LoggerUtil()


class ClientesService:

    def __init__(self, clientes_repository: ClientesRepository) -> None:
        self._repo = clientes_repository

    async def create(self, bl: ClienteCreate) -> ClientesResponse:
        cliente_model = Bls(**bl.dict())
        created_bl = await self._repo.create(cliente_model)
        log.info(f"Cliente creado con N°: {created_bl.no_bl}")
        return ClientesResponse.model_validate(created_bl)

    async def update(self, id: int, bl: ClienteUpdate) -> Optional[ClientesResponse]:
        cliente_model = Bls(**bl.dict())
        updated_bl = await self._repo.update(id, cliente_model)
        log.info(f"Cliente actualizado con ID: {id}")
        return ClientesResponse.model_validate(updated_bl)

    async def delete(self, id: int) -> bool:
        deleted = await self._repo.delete(id)
        log.info(f"Cliente eliminado con ID: {id}")
        return deleted

    async def get(self, id: int) -> Optional[ClientesResponse]:
        cliente = await self._repo.get_by_id(id)
        return ClientesResponse.model_validate(cliente) if cliente else None

    async def get_all(self) -> List[ClientesResponse]:
        clientes = await self._repo.get_all()
        return [ClientesResponse.model_validate(cliente) for cliente in clientes]

    async def create_client_if_not_exists(self, cliente_data: ClienteCreate) -> ClientesResponse:
        """
               Check if a Cliente already exists. If not, create a new one.

               Args:
                   cliente_data: The schema of Cliente object.

               Returns:
                   The existing or newly created Cliente
       """
        try:
            cliente_existente = await self._repo.get_cliente_by_name(cliente_data.no_bl)
            if cliente_existente:
                log.info(f"Cliente ya existente con N°: {cliente_data.no_bl}")
                return ClientesResponse.model_validate(cliente_existente)

            cliente_creado = await self._repo.create(cliente_data)
            log.info(f"Se creó Cliente: {cliente_creado.no_bl}")
            return ClientesResponse.model_validate(cliente_creado)

        except Exception as e:
            log.error(f"Error al crear o consultar Cliente: {cliente_data.referencia} - {e}")
            raise

    async def get_cliente_by_name(self, nombre: str) -> Optional[ClientesResponse]:
        """
         Find a Cliente by their 'name'

         Args:
             nombre: The Cliente name param to filter.

         Returns:
             Cliente object filtered by 'name'.
         """
        return await self._repo.get_cliente_by_name(nombre)


from typing import Optional

from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import Clientes
from repositories.base_repository import IRepository
from schemas.clientes_schema import ClientesResponse
from utils.logger_util import LoggerUtil

log = LoggerUtil()


class ClientesRepository(IRepository[Clientes, ClientesResponse]):
    db: AsyncSession

    def __init__(self, model: type[Clientes], schema: type[ClientesResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def get_cliente_by_name(self, ref: str) -> Optional[Clientes]:
        stmt = select(self.model).filter(self.model.razon_social == ref)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def sync_sequence(self) -> None:
        """Sincroniza la secuencia del ID de clientes con el máximo valor existente."""
        # Para columnas IDENTITY, usamos pg_get_serial_sequence o consultamos pg_class
        sync_sql = """
            SELECT setval(
                pg_get_serial_sequence('clientes', 'id'),
                COALESCE((SELECT MAX(id) FROM clientes), 1)
            )
        """
        await self.db.execute(text(sync_sql))
        await self.db.commit()
        log.info("Secuencia de clientes sincronizada correctamente")

    async def create_with_sequence_fix(self, obj: BaseModel) -> ClientesResponse:
        """
        Crea un cliente manejando el caso de secuencia desincronizada.
        Si ocurre un error de clave duplicada, sincroniza la secuencia y reintenta.
        """
        try:
            return await self.create(obj)
        except IntegrityError as e:
            if "clientes_pkey" in str(e) or "UniqueViolation" in str(e):
                log.warning("Secuencia desincronizada detectada, sincronizando...")
                await self.db.rollback()
                await self.sync_sequence()
                # Reintentar la creación
                return await self.create(obj)
            raise



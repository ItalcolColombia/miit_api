from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import SaldoSnapshotScada
from repositories.base_repository import IRepository
from schemas.saldo_snapshot_schema import SaldoSnapshotCreate, SaldoSnapshotResponse


class SaldoSnapshotRepository(IRepository[SaldoSnapshotScada, SaldoSnapshotResponse]):
    db: AsyncSession

    def __init__(self, model: type[SaldoSnapshotScada], schema: type[SaldoSnapshotResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def create_snapshot(self, snapshot: SaldoSnapshotCreate) -> SaldoSnapshotResponse:
        # Compatibilidad con create() del repositorio base
        return await self.create(snapshot)


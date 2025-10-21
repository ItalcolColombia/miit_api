from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, and_

from core.contracts.auditor import Auditor
from repositories.base_repository import IRepository
from schemas.pesadas_corte_schema import PesadasCalculate, PesadasCorteCreate, PesadasRange
from schemas.pesadas_schema import PesadaResponse, VPesadasAcumResponse
from database.models import Pesadas, Viajes, Flotas, Transacciones, Materiales, Bls, PesadasCorte


class PesadasRepository(IRepository[Pesadas, PesadaResponse]):
    db: AsyncSession

    def __init__(self, model: type[Pesadas], schema: type[PesadaResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)


    async def get_sumatoria_pesadas(self, puerto_ref: str, tran_id: Optional[int] = None) -> List[PesadasCalculate] | None:
        """
                Filter pesada sum

                Returns:
                    A sum of Pesadas register matching the filter, otherwise, returns a null.
                """

        query = (
            select(
                Viajes.puerto_id,
                Flotas.referencia,
                Viajes.id.label('consecutivo'),
                Transacciones.id.label('transaccion'),
                Transacciones.pit,
                Materiales.codigo.label('material'),
                func.sum(Pesadas.peso_real).label('peso'),
                func.max(Pesadas.fecha_hora).label('fecha_hora'),
                func.min(Pesadas.id).label('primera'),
                func.max(Pesadas.id).label('ultima'),
                Pesadas.usuario_id,
                func.fn_usuario_nombre(Pesadas.usuario_id).label('usuario'),
                Bls.no_bl
            )
            .join(Transacciones, Pesadas.transaccion_id == Transacciones.id)
            .join(Materiales, Transacciones.material_id == Materiales.id)
            .join(Viajes, Transacciones.viaje_id == Viajes.id)
            .join(Flotas, Viajes.flota_id == Flotas.id)
            .outerjoin(Bls, and_(
                Transacciones.material_id == Bls.material_id,
                Viajes.id == Bls.viaje_id
            ))
            .where(Pesadas.leido == False)  # Only include non-read pesadas
            .group_by(
                Transacciones.id,
                Flotas.referencia,
                Viajes.id,
                Transacciones.pit,
                Materiales.codigo,
                Pesadas.usuario_id,
                Bls.no_bl
            )
            .order_by(Transacciones.id)
        )

        if puerto_ref is not None:
            query = query.where(Viajes.puerto_id == puerto_ref)

        if tran_id is not None:
            query = query.where(Transacciones.id == tran_id)

        result = await self.db.execute(query)
        return [PesadasCalculate(**row) for row in result.mappings().all()]

    async def mark_pesadas(self, pesada_ranges: List[PesadasRange]) -> List[int]:
        """
            Mark pesadas as 'leido' for the given ranges of pesada  (between primera and ultima pesadas ID)
            for each transaccion_id using bulk update.

            Args:
                pesada_ranges: List of tuples (primera, ultima, transaccion).
            Returns:
                List[int]: List of Pesadas IDs that were marked as leido.
        """
        if not pesada_ranges:
            return []

        pesada_ids = []
        for item in pesada_ranges:
            query = (
                select(Pesadas.id)
                .where(
                    Pesadas.id.between(item.primera, item.ultima),
                    Pesadas.transaccion_id == item.transaccion
                )
            )
            result = await self.db.execute(query)
            pesada_ids = [row[0] for row in result.fetchall()]

        if pesada_ids:
            await self.update_bulk(
                entity_ids=pesada_ids,
                update_data={'leido': True}
            )

        return pesada_ids

    async def mark_pesadas_corte_as_enviado(self, corte_ids: List[int]):
        """
        Mark specified pesadas_corte records as 'enviado'.
            Args:
        corte_ids: List of cortes Id.
        """
        if not corte_ids:
            return

        await self.update_bulk(entity_ids=corte_ids, update_data={'enviado': True})

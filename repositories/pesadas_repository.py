from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.contracts.auditor import Auditor
from database.models import Pesadas, Viajes, Flotas, Transacciones, Materiales, VPesadasAcumulado
from repositories.base_repository import IRepository
from schemas.pesadas_corte_schema import PesadasCalculate, PesadasRange
from schemas.pesadas_schema import PesadaResponse, VPesadasAcumResponse


class PesadasRepository(IRepository[Pesadas, PesadaResponse]):
    db: AsyncSession

    def __init__(self, model: type[Pesadas], schema: type[PesadaResponse], db: AsyncSession, auditor: Auditor) -> None:
        self.db = db
        super().__init__(model, schema, db, auditor)

    async def get_sumatoria_pesada(self, puerto_ref: Optional[str] = None, tran_id: Optional[int] = None) -> Optional[VPesadasAcumResponse]:
        """
                Filter pesada sum

                Returns:
                    A sum of Pesadas register matching the filter, otherwise, returns a null.
                """

        query = select(VPesadasAcumulado)

        if puerto_ref is not None:
            query = query.where(VPesadasAcumulado.puerto_id == puerto_ref)

        if tran_id is not None:
            query = query.where(VPesadasAcumulado.transaccion == tran_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

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
                func.fn_usuario_nombre(Pesadas.usuario_id).label('usuario')
            )
            .join(Transacciones, Pesadas.transaccion_id == Transacciones.id)
            .join(Materiales, Transacciones.material_id == Materiales.id)
            .join(Viajes, Transacciones.viaje_id == Viajes.id)
            .join(Flotas, Viajes.flota_id == Flotas.id)
            .where(Pesadas.leido == False)  # Only include non-read pesadas
            .group_by(
                Transacciones.id,
                Flotas.referencia,
                Viajes.id,
                Transacciones.pit,
                Materiales.codigo,
                Pesadas.usuario_id
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
            # use scalars() to extract ids and extend the list (do not overwrite previous ids)
            ids = result.scalars().all()
            pesada_ids.extend(ids)

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

    async def fetch_and_mark_sumatoria_pesadas(self, puerto_ref: str, tran_id: int) -> List[PesadasCalculate] | None:
        """
        Atomic operation to fetch the sum/grouping of non-read pesadas for a specific transaction
        and mark the involved Pesadas rows as read. This reduces race conditions when multiple
        workers process the same puerto simultaneously.

        Strategy:
        1. Start a DB transaction.
        2. Select Pesadas IDs matching puerto_ref and tran_id with FOR UPDATE SKIP LOCKED to avoid
           competing workers picking the same rows.
        3. If no IDs found, return empty list.
        4. Reuse the existing aggregation query (similar to get_sumatoria_pesadas) but filter by the
           selected IDs to compute the aggregated values per transaction.
        5. Update Pesadas SET leido = True WHERE id IN (selected_ids).
        6. Commit and return the aggregated mappings as PesadasCalculate instances.
        """
        try:
            # 1. iniciar transacción
            async with self.db.begin():
                # 2. seleccionar ids con FOR UPDATE SKIP LOCKED
                id_sel = (
                    select(Pesadas.id)
                    .join(Transacciones, Pesadas.transaccion_id == Transacciones.id)
                    .join(Viajes, Transacciones.viaje_id == Viajes.id)
                    .where(
                        Pesadas.leido == False,
                        Transacciones.id == tran_id,
                        Viajes.puerto_id == puerto_ref
                    )
                    .with_for_update(skip_locked=True)
                )
                res_ids = await self.db.execute(id_sel)
                ids = res_ids.scalars().all()

                if not ids:
                    return []

                # 4. Agregación sobre los ids seleccionados
                agg_q = (
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
                        func.fn_usuario_nombre(Pesadas.usuario_id).label('usuario')
                    )
                    .join(Transacciones, Pesadas.transaccion_id == Transacciones.id)
                    .join(Materiales, Transacciones.material_id == Materiales.id)
                    .join(Viajes, Transacciones.viaje_id == Viajes.id)
                    .join(Flotas, Viajes.flota_id == Flotas.id)
                    .where(Pesadas.id.in_(ids))
                    .group_by(
                        Transacciones.id,
                        Flotas.referencia,
                        Viajes.id,
                        Transacciones.pit,
                        Materiales.codigo,
                        Pesadas.usuario_id
                    )
                )

                agg_res = await self.db.execute(agg_q)
                mappings = agg_res.mappings().all()

                # 5. Marcar pesadas como leidas
                await self.update_bulk(entity_ids=ids, update_data={'leido': True})

                return [PesadasCalculate(**row) for row in mappings]
        except Exception:
            # No propagar detalles SQL, dejar que quien llame maneje/loguee
            raise

    async def get_suma_peso_by_transaccion(self, tran_id: int) -> Optional[dict]:
        """
        Obtener la suma total de peso_real de pesadas asociadas a una transacción.
        Este método no depende de JOINs con Viajes/Flotas, por lo que funciona
        para cualquier tipo de transacción incluyendo Traslados.

        Args:
            tran_id: ID de la transacción.

        Returns:
            dict con 'peso_total' (Decimal) y 'cantidad_pesadas' (int), o None si no hay pesadas.
        """
        query = (
            select(
                func.sum(Pesadas.peso_real).label('peso_total'),
                func.count(Pesadas.id).label('cantidad_pesadas')
            )
            .where(Pesadas.transaccion_id == tran_id)
        )
        result = await self.db.execute(query)
        row = result.mappings().first()
        if row and row['peso_total'] is not None:
            return {
                'peso_total': row['peso_total'],
                'cantidad_pesadas': row['cantidad_pesadas']
            }
        return None


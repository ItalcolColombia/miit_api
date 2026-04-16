"""
Worker periodico que envia notificaciones CamionCargue consolidadas.

La API externa CamionCargue solo acepta un envio por camion (y el puerto se
queda con el primer payload recibido). Cuando un viaje de despacho directo
tiene multiples transacciones, enviar al finalizar cada transaccion ocasiona
que el puerto solo registre la primera.

Para cubrir ese caso, al finalizar una transaccion de despacho directo se
difiere el envio (columna viajes.camioncargue_notify_at = now() + debounce).
Si llega otra transaccion dentro de la ventana, se reinicia el contador.
Este worker revisa periodicamente los viajes con la ventana ya vencida y
aun no notificados (camioncargue_notified_at IS NULL), consolida todas sus
transacciones de despacho y dispara el envio a la API externa.
"""

from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from core.config.settings import get_settings
from database.connection import DatabaseConfiguration
from database.models import (
    Bls,
    Flotas,
    Transacciones,
    Viajes,
)
from repositories.bls_repository import BlsRepository
from repositories.flotas_repository import FlotasRepository
from repositories.transacciones_repository import TransaccionesRepository
from repositories.viajes_repository import ViajesRepository
from schemas.bls_schema import BlsResponse
from schemas.flotas_schema import FlotasResponse
from schemas.transacciones_schema import TransaccionResponse
from schemas.viajes_schema import ViajesResponse
from services.logs_auditoria_service import DatabaseAuditor
from services.transacciones_service import TransaccionesService
from utils.logger_util import LoggerUtil

log = LoggerUtil()

_scheduler: Optional[AsyncIOScheduler] = None
_JOB_ID = "camioncargue_pending_notifications"


async def _procesar_notificaciones_pendientes() -> None:
    """
    Tick del worker. Busca viajes con debounce vencido y envia el consolidado.
    Errores de envio se loggean pero no se propagan: al no marcar notified_at
    el mismo viaje vuelve a intentarse en el siguiente tick.
    """
    try:
        async for session in DatabaseConfiguration.get_session():
            auditor = DatabaseAuditor(session)

            viajes_repo = ViajesRepository(Viajes, ViajesResponse, session, auditor)
            try:
                pending_ids = await viajes_repo.find_pending_camioncargue_viaje_ids()
            except Exception as e:
                log.error(f"[camioncargue_worker] Error consultando viajes pendientes: {e}", exc_info=True)
                return

            if not pending_ids:
                return

            log.info(f"[camioncargue_worker] {len(pending_ids)} viaje(s) pendiente(s) de notificar: {pending_ids}")

            trans_repo = TransaccionesRepository(Transacciones, TransaccionResponse, session, auditor)
            flotas_repo = FlotasRepository(Flotas, FlotasResponse, session, auditor)
            bls_repo = BlsRepository(Bls, BlsResponse, session, auditor)

            service = TransaccionesService(
                tran_repository=trans_repo,
                pesadas_service=None,
                mov_service=None,
                alm_service=None,
                mat_service=None,
                viajes_repository=viajes_repo,
                bls_repository=bls_repo,
                flotas_repository=flotas_repo,
            )

            for viaje_id in pending_ids:
                try:
                    resultado = await service.enviar_camion_cargue(viaje_id)
                    if resultado.get('success'):
                        log.info(
                            f"[camioncargue_worker] viaje {viaje_id} notificado: {resultado.get('message')}"
                        )
                    else:
                        log.warning(
                            f"[camioncargue_worker] viaje {viaje_id} no notificado (se reintentara): "
                            f"{resultado.get('message')}"
                        )
                except Exception as e:
                    log.error(
                        f"[camioncargue_worker] Error al procesar viaje {viaje_id}: {e}",
                        exc_info=True,
                    )
    except Exception as e:
        log.error(f"[camioncargue_worker] Error inesperado en tick: {e}", exc_info=True)


def start_camioncargue_scheduler() -> None:
    """
    Inicia el scheduler. Idempotente: llamarlo mas de una vez no duplica el job.
    """
    global _scheduler
    if _scheduler is not None and _scheduler.running:
        return

    settings = get_settings()
    interval_seconds = max(10, int(settings.CAMIONCARGUE_WORKER_INTERVAL_SECONDS))

    _scheduler = AsyncIOScheduler(timezone="America/Bogota")
    _scheduler.add_job(
        _procesar_notificaciones_pendientes,
        trigger="interval",
        seconds=interval_seconds,
        id=_JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    _scheduler.start()
    log.info(
        f"[camioncargue_worker] Scheduler iniciado. Intervalo={interval_seconds}s, "
        f"debounce={settings.CAMIONCARGUE_DEBOUNCE_MINUTES}min"
    )


def shutdown_camioncargue_scheduler() -> None:
    """
    Detiene el scheduler (si esta corriendo). Seguro llamar aunque no se haya iniciado.
    """
    global _scheduler
    if _scheduler is None:
        return
    try:
        if _scheduler.running:
            _scheduler.shutdown(wait=False)
            log.info("[camioncargue_worker] Scheduler detenido")
    finally:
        _scheduler = None

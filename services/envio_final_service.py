from datetime import datetime, timezone
from typing import Any, List, Optional
from decimal import Decimal
from sqlalchemy import select as _select

from fastapi import HTTPException, status
from core.exceptions.entity_exceptions import EntityNotFoundException
from core.exceptions.base_exception import BasedException

from schemas.pesadas_corte_schema import PesadaCorteRetrieve
from utils.logger_util import LoggerUtil
from database.models import Materiales

log = LoggerUtil()


async def notify_envio_final(puerto_id: str, pesadas: List[Any], viajes_service: Any, mode: str = 'last') -> None:
    """Centraliza la lógica del endpoint POST /envio-final/{puerto_id}/notify

    Modes:
    - 'auto': deja que el servicio determine si acepta lista (external_accepts_list=None)
    - 'list': fuerza envío como lista (external_accepts_list=True)
    - 'single': fuerza envío no-lista (external_accepts_list=False)
    - 'last': envía la lista pero indica que el último debe enviarse como objeto (send_last_as_object=True)

    Convierte los items a dicts (si son modelos), añade `voyage` a cada elemento y llama
    a `viajes_service.send_envio_final_external` con los flags calculados.

    """
    if not pesadas:
        placeholder = {
            "referencia": "",
            "consecutivo": 0,
            "transaccion": 0,
            "pit": 0,
            "material": "",
            "peso": Decimal("0.00"),
            "puerto_id": puerto_id,
            "fecha_hora": datetime.now(timezone.utc),
            "usuario_id": 0,
            "usuario": ""
        }
        pesadas = [placeholder]

    if mode not in ('auto', 'list', 'single', 'last'):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="mode inválido. use 'auto'|'list'|'single'|'last'")

    if mode == 'auto':
        external_accepts_list = None
        send_last_as_object = False
    elif mode == 'list':
        external_accepts_list = True
        send_last_as_object = False
    elif mode == 'single':
        external_accepts_list = False
        send_last_as_object = False
    else:  # 'last'
        external_accepts_list = None
        send_last_as_object = True

    # convertir elementos a dicts y añadir voyage
    pesadas_converted = []
    for item in pesadas:
        try:
            if hasattr(item, 'model_dump'):
                obj = item.model_dump()
            elif hasattr(item, 'dict'):
                obj = item.dict()
            elif hasattr(item, '__dict__'):
                obj = item.__dict__
            else:
                obj = dict(item)
        except Exception:
            obj = item if isinstance(item, dict) else {}

        obj['voyage'] = puerto_id
        pesadas_converted.append(obj)

    try:
        await viajes_service.send_envio_final_external(puerto_id, pesadas_converted, external_accepts_list=external_accepts_list, send_last_as_object=send_last_as_object)
        log.info(f"EnvioFinal notify helper: notificación externa enviada para {puerto_id} (mode={mode})")
    except Exception as e_send:
        try:
            from core.exceptions.base_exception import BasedException as _BasedException
        except Exception:
            _BasedException = None

        if _BasedException is not None and isinstance(e_send, _BasedException):
            log.error(f"EnvioFinal notify helper: fallo al notificar externamente para {puerto_id}: {e_send}")
            raise

        log.error(f"EnvioFinal notify helper: error inesperado al notificar externamente para {puerto_id}: {e_send}")
        raise


async def prepare_preview_envio_final(puerto_id: str, pesadas: List[Any]) -> List[Any]:
    """Prepara la lista de pesadas para la vista previa (GET /envio-final).

    - Si `pesadas` no está vacía, la devuelve tal cual.
    - Si está vacía, devuelve una lista con un placeholder que contiene peso 0
      y fecha UTC (timezone-aware), manteniendo la estructura esperada por el consumidor.
    """
    if pesadas:
        return pesadas

    placeholder = {
        "referencia": "",
        "consecutivo": 0,
        "transaccion": 0,
        "pit": 0,
        "material": "",
        "peso": Decimal("0.00"),
        "puerto_id": puerto_id,
        "fecha_hora": datetime.now(timezone.utc),
        "usuario_id": 0,
        "usuario": ""
    }
    return [placeholder]


async def fetch_preview_for_puerto(puerto_id: str, pesadas_service: Any) -> List[Any]:
    """Obtiene la lista de pesadas pendientes para la última transacción y la prepara para preview.

    Si el servicio de pesadas no encuentra pesadas o lanza 404, intenta construir un placeholder
    usando metadatos de la última transacción candidata (preferir estado 'Proceso').
    """
    # Intentar obtener pesadas pendientes normalmente
    pesadas = []
    try:
        pesadas = await pesadas_service.get_pending_for_last_transaccion(puerto_id=puerto_id)
    except (EntityNotFoundException, BasedException, HTTPException) as exc:
        # Si el servicio indica 'no encontrado' o devuelve 404, lo interpretamos como ausencia de pesadas
        if getattr(exc, 'status_code', None) == status.HTTP_404_NOT_FOUND or isinstance(exc, EntityNotFoundException):
            log.info(f"fetch_preview_for_puerto: no se encontraron pesadas pendientes para {puerto_id} ({type(exc).__name__}); se intentará construir placeholder desde última transacción candidata")
            pesadas = []
        else:
            # Propagar otros errores
            raise

    # Si no hay pesadas, intentar construir placeholder a partir de la última transacción candidata
    if not pesadas:
        try:
            tran_candidates = None
            trans_repo = getattr(pesadas_service, '_trans_repo', None)
            if trans_repo is not None:
                try:
                    trans_list = await trans_repo.find_many(ref1=puerto_id)
                    if trans_list:
                        proceso = [t for t in trans_list if getattr(t, 'estado', None) == 'Proceso']
                        proceso_sorted = sorted(proceso, key=lambda t: getattr(t, 'fecha_hora') or datetime.min, reverse=True)
                        others = [t for t in trans_list if getattr(t, 'estado', None) != 'Proceso']
                        others_sorted = sorted(others, key=lambda t: getattr(t, 'fecha_hora') or datetime.min, reverse=True)
                        tran_candidates = proceso_sorted + others_sorted
                except Exception as e_tran:
                    log.warning(f"fetch_preview_for_puerto: error buscando transacciones para {puerto_id}: {e_tran}")
                    tran_candidates = None

            selected_tran = tran_candidates[0] if tran_candidates else None

            if selected_tran is not None:
                t_id = getattr(selected_tran, 'id', None)
                viaje_consec = int(getattr(selected_tran, 'viaje_id', 0) or 0)
                pit = int(getattr(selected_tran, 'pit', 0) or 0)
                fecha_hora = getattr(selected_tran, 'fecha_hora', None) or datetime.now(timezone.utc)
                usuario_id = int(getattr(selected_tran, 'usuario_id', 0) or 0)
                usuario = getattr(selected_tran, 'usuario', '') or ""

                # Resolver material
                material = ''
                mat_id = getattr(selected_tran, 'material_id', None)
                try:
                    repo_db = getattr(pesadas_service._repo, 'db', None)
                    if mat_id is not None and repo_db is not None:
                        result = await repo_db.execute(_select(Materiales).where(Materiales.id == int(mat_id)))
                        mat_obj = result.scalar_one_or_none()
                        if mat_obj is not None:
                            material = getattr(mat_obj, 'codigo', None) or getattr(mat_obj, 'nombre', '') or ''
                except Exception as e_mat:
                    log.warning(f"fetch_preview_for_puerto: no se pudo resolver material para material_id={mat_id}: {e_mat}")

                # generar referencia con gen_pesada_identificador + 'F'
                referencia_final = ''
                try:
                    gen_req = PesadaCorteRetrieve(puerto_id=puerto_id, transaccion=int(t_id) if t_id is not None else None)
                    ref_gen = await pesadas_service.gen_pesada_identificador(gen_req)
                    referencia_final = f"{ref_gen}F" if ref_gen else ''
                except Exception as e_ref:
                    log.warning(f"fetch_preview_for_puerto: no se pudo generar referencia para transaccion {t_id}: {e_ref}")

                placeholder = {
                    "referencia": referencia_final,
                    "consecutivo": int(viaje_consec),
                    "transaccion": int(t_id) if t_id is not None else 0,
                    "pit": int(pit),
                    "material": material,
                    "peso": Decimal("0.00"),
                    "puerto_id": puerto_id,
                    "fecha_hora": fecha_hora,
                    "usuario_id": usuario_id,
                    "usuario": usuario
                }
                pesadas = [placeholder]
        except Exception as e_placeholder:
            log.error(f"fetch_preview_for_puerto: error construyendo placeholder para {puerto_id}: {e_placeholder}", exc_info=True)
            pesadas = []

    return await prepare_preview_envio_final(puerto_id, pesadas)

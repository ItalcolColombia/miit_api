from datetime import datetime
from typing import Any, List, Optional

from fastapi import HTTPException, status

from schemas.pesadas_schema import VPesadasEnvioResponse
from utils.logger_util import LoggerUtil

log = LoggerUtil()


async def prepare_and_notify_envio_final(puerto_id: str, pesadas: List[Any], viajes_service: Any, notify: bool = True) -> Optional[VPesadasEnvioResponse]:
    """Prepara el último registro de `pesadas` para envío final.

    - Selecciona la última entrada por `fecha_hora` (soporta dicts y modelos).
    - Convierte el elemento seleccionado a dict y añade `voyage` = puerto_id.
    - Si `notify` es True, invoca `viajes_service.send_envio_final_external` con una lista que contiene
      el último item y propaga excepciones según la implementación existente (re-raise).

    Retorna una instancia de `VPesadasEnvioResponse` o None si `pesadas` está vacío.
    """
    if not pesadas:
        return None

    def _get_date(item: Any):
        try:
            if isinstance(item, dict):
                val = item.get('fecha_hora')
            else:
                val = getattr(item, 'fecha_hora', None)

            if isinstance(val, str):
                # soportar sufijo Z
                return datetime.fromisoformat(val.replace('Z', '+00:00'))

            return val
        except Exception:
            return datetime.min

    last = max(pesadas, key=_get_date)

    # convertir a dict si es modelo
    try:
        if hasattr(last, 'model_dump'):
            last_obj = last.model_dump()
        elif hasattr(last, '__dict__'):
            last_obj = last.__dict__
        else:
            last_obj = dict(last)
    except Exception:
        last_obj = last if isinstance(last, dict) else {}

    # añadir campo voyage
    last_obj['voyage'] = puerto_id

    # notificar externamente si se solicita
    if notify:
        try:
            await viajes_service.send_envio_final_external(puerto_id, [last_obj])
            log.info(f"EnvioFinal helper: notificación externa enviada para {puerto_id}")
        except Exception as e_send:
            try:
                from core.exceptions.base_exception import BasedException as _BasedException
            except Exception:
                _BasedException = None

            if _BasedException is not None and isinstance(e_send, _BasedException):
                log.error(f"EnvioFinal helper: fallo al notificar externamente para {puerto_id}: {e_send}")
                raise

            log.error(f"EnvioFinal helper: error inesperado al notificar externamente para {puerto_id}: {e_send}")
            raise

    # retornar modelo validado
    return VPesadasEnvioResponse.model_validate(last_obj)


async def notify_envio_final(puerto_id: str, pesadas: List[Any], viajes_service: Any, mode: str = 'last') -> None:
    """Centraliza la lógica del endpoint POST /envio-final/{puerto_id}/notify

    Modes:
    - 'auto': deja que el servicio determine si acepta lista (external_accepts_list=None)
    - 'list': fuerza envío como lista (external_accepts_list=True)
    - 'single': fuerza envío no-lista (external_accepts_list=False)
    - 'last': envía la lista pero indica que el último debe enviarse como objeto (send_last_as_object=True)

    Convierte los items a dicts (si son modelos), añade `voyage` a cada elemento y llama
    a `viajes_service.send_envio_final_external` con los flags calculados.

    Lanza HTTPException 404 si no hay pesadas.
    """
    if not pesadas:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontraron pesadas para el puerto especificado")

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

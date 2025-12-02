import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


def utc_from_timestamp(timestamp: float) -> datetime:
    """
    Class responsible for handling timestamp generation.

    This class returns datetime with the timezone.

    Class Args:
        None
    """
    return datetime.fromtimestamp(timestamp, timezone.utc)


def ensure_aware_utc(dt: datetime) -> datetime:
    """Ensure a datetime is timezone-aware in UTC.

    - If dt is None, return None.
    - If dt already has tzinfo, convert to UTC.
    - If dt is naive, assume it's in the local timezone (from TZ env or system local timezone)
      and convert to UTC. This fixes cases where code calls datetime.now() (naive) expecting
      local time of the container.
    """
    if dt is None:
        return None

    # If dt already has tzinfo, convert to UTC
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc)

    # dt is naive: determine local tz
    tz_name = os.environ.get('TZ')
    if tz_name:
        try:
            local_tz = ZoneInfo(tz_name)
        except Exception:
            local_tz = datetime.now().astimezone().tzinfo or timezone.utc
    else:
        # Fallback to system local timezone
        local_tz = datetime.now().astimezone().tzinfo or timezone.utc

    # Localize naive dt as local_tz then convert to UTC
    localized = dt.replace(tzinfo=local_tz)
    return localized.astimezone(timezone.utc)


def utc_to_bogota(dt: datetime) -> datetime:
    """Convierte un datetime aware en UTC a la zona America/Bogota.

    Si dt es naive se asume UTC.
    """
    if dt is None:
        return None
    dt_utc = ensure_aware_utc(dt)
    return dt_utc.astimezone(ZoneInfo('America/Bogota'))


def format_iso_bogota(dt: datetime) -> str:
    """Devuelve una representación ISO 8601 en zona America/Bogota.

    Si dt es None devuelve None.
    """
    if dt is None:
        return None
    return utc_to_bogota(dt).isoformat()


# Nueva función: asegurar datetime en la zona configurada por TZ
def ensure_aware_local(dt: datetime) -> datetime:
    """Asegura que un datetime sea timezone-aware usando la zona definida en la variable
    de entorno TZ (por ejemplo 'America/Bogota').

    - Si dt es None devuelve None.
    - Si dt es naive: se asume que está en la zona local (TZ) y se le añade tzinfo.
    - Si dt ya tiene tzinfo: se convierte a la zona local.

    Esto permite persistir valores con la zona local en lugar de forzar UTC.
    """
    if dt is None:
        return None
    tz_name = os.environ.get('TZ', 'UTC')
    try:
        local_tz = ZoneInfo(tz_name)
    except Exception:
        local_tz = timezone.utc

    if dt.tzinfo is None:
        # Asumir naive como hora local
        return dt.replace(tzinfo=local_tz)
    return dt.astimezone(local_tz)


def now_local() -> datetime:
    """Devuelve la fecha y hora actual en la zona local definida por TZ (timezone-aware).

    Útil para asignar campos de fecha_hora que deban reflejar la hora local del contenedor.
    """
    tz_name = os.environ.get('TZ', 'UTC')
    try:
        local_tz = ZoneInfo(tz_name)
    except Exception:
        local_tz = timezone.utc
    return datetime.now(local_tz)

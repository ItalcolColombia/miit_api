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

    - If dt is naive, assume it's already UTC and make it timezone-aware.
    - If dt has tzinfo, convert to UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


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

from datetime import datetime, timezone
import os
from zoneinfo import ZoneInfo
from typing import Optional


def get_app_timezone() -> str:
    """Devuelve la zona configurada por APP_TIMEZONE o 'America/Bogota' por defecto."""
    return os.environ.get('APP_TIMEZONE') or 'America/Bogota'


def _parse_iso_datetime(value: str) -> datetime:
    """Parses an ISO datetime string robustly (handles trailing 'Z')."""
    if value.endswith('Z'):
        value = value[:-1] + '+00:00'
    return datetime.fromisoformat(value)


def ensure_aware_in_app_tz(dt: datetime) -> datetime:
    """Asegura que dt sea timezone-aware en la zona configurada por APP_TIMEZONE.

    - Si dt es naive -> se le asume la zona APP_TIMEZONE.
    - Si dt ya tiene tzinfo -> se convierte a la zona APP_TIMEZONE.
    """
    if dt is None:
        return None
    tz_name = get_app_timezone()
    try:
        app_tz = ZoneInfo(tz_name)
    except Exception:
        # Fallback a UTC si la zona no existe
        app_tz = timezone.utc

    if dt.tzinfo is None:
        return dt.replace(tzinfo=app_tz)
    return dt.astimezone(app_tz)


def normalize_to_utc(value: Optional[object]) -> Optional[datetime]:
    """Toma un str o datetime (naive o aware) y devuelve un datetime aware en UTC.

    - Si value es None -> None
    - Si es str -> intenta parsear ISO
    - Si es naive -> se asume APP_TIMEZONE y luego se convierte a UTC
    - Si es aware -> se convierte a UTC
    """
    if value is None:
        return None

    if isinstance(value, str):
        # parsear ISO flexiblemente
        dt = _parse_iso_datetime(value)
    elif isinstance(value, datetime):
        dt = value
    else:
        # no es un tipo esperado; intentar dejar que pydantic o quien llame valide
        return value

    # si es naive, asumir zona APP_TIMEZONE
    if dt.tzinfo is None:
        dt = ensure_aware_in_app_tz(dt)

    return dt.astimezone(timezone.utc)


def utc_to_app_tz(dt: Optional[datetime]) -> Optional[datetime]:
    """Convierte un datetime aware UTC a la zona configurada por APP_TIMEZONE.

    Si dt es naive, se asume que ya está en UTC.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # interpretar naive como UTC
        dt = dt.replace(tzinfo=timezone.utc)
    tz_name = get_app_timezone()
    try:
        app_tz = ZoneInfo(tz_name)
    except Exception:
        app_tz = timezone.utc
    return dt.astimezone(app_tz)


def format_iso_bogota(dt: Optional[datetime]) -> Optional[str]:
    """Convierte un datetime a la zona APP_TIMEZONE y devuelve un ISO string sin microsegundos.

    - Si dt es None -> None
    - Si dt es naive se asume UTC y se convierte a APP_TIMEZONE
    - Si dt es aware se convierte a APP_TIMEZONE
    """
    if dt is None:
        return None
    try:
        converted = utc_to_app_tz(dt)
        # eliminar microsegundos para salidas más limpias
        converted = converted.replace(microsecond=0)
        return converted.isoformat()
    except Exception:
        # fallback seguro
        try:
            return dt.replace(microsecond=0).isoformat()
        except Exception:
            return str(dt)


# Compatibilidad: alias/funciones utilitarias usadas en otros módulos
def ensure_aware_local(dt: Optional[datetime]) -> Optional[datetime]:
    """Alias para ensure_aware_in_app_tz: asegura tz aware en APP_TIMEZONE (útil al guardar)."""
    if dt is None:
        return None
    return ensure_aware_in_app_tz(dt)


def now_local() -> datetime:
    """Devuelve el datetime actual con tzaware en la zona configurada por APP_TIMEZONE."""
    tz_name = get_app_timezone()
    try:
        app_tz = ZoneInfo(tz_name)
    except Exception:
        app_tz = timezone.utc
    return datetime.now(app_tz)


def now_utc() -> datetime:
    """Devuelve el datetime actual en UTC (tz-aware)."""
    return datetime.now(timezone.utc)

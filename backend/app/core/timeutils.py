"""Utilidades de fecha y hora. Todo el sistema usa la hora local configurada (TIMEZONE)."""
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from app.core.config import settings


def now_local() -> datetime:
    """Fecha y hora actual en la zona configurada, sin tzinfo (formato almacenado en BD)."""
    return datetime.now(ZoneInfo(settings.TIMEZONE)).replace(tzinfo=None, microsecond=0)


def today_local() -> date:
    return now_local().date()


def add_minutes(t: time, minutes: int) -> time | None:
    """Suma minutos a una hora. Devuelve None si el resultado pasa al día siguiente."""
    base = datetime.combine(date(2000, 1, 1), t)
    result = base + timedelta(minutes=minutes)
    if result.date() != base.date():
        return None
    return result.time()

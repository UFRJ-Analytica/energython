from __future__ import annotations

from datetime import datetime, timedelta, timezone


class DateRangeError(ValueError):
    pass


def parse_iso_datetime(value: str | None, field_name: str) -> datetime:
    if not value:
        raise DateRangeError(f"{field_name}_obrigatorio")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception as exc:
        raise DateRangeError(f"{field_name}_invalido") from exc

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


def parse_range(inicio: str | None, fim: str | None, max_dias: int = 366) -> tuple[datetime, datetime]:
    i = parse_iso_datetime(inicio, "inicio")
    f = parse_iso_datetime(fim, "fim")
    if i > f:
        raise DateRangeError("intervalo_invalido")
    if (f - i) > timedelta(days=max_dias):
        raise DateRangeError(f"intervalo_excede_{max_dias}_dias")
    return i, f


def ts_hour_key(value: datetime | str) -> str:
    """Retorna chave string do timestamp truncado à hora (sem minutos/segundos/tz)."""
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    return str(dt.replace(minute=0, second=0, microsecond=0, tzinfo=None))


def ts_keys(value: datetime | str) -> tuple[str, str]:
    """Retorna (chave exata, chave arredondada à hora) para lookup de PLD."""
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    dt = dt.replace(tzinfo=None)
    return str(dt), str(dt.replace(minute=0, second=0, microsecond=0))

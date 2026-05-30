from __future__ import annotations

from datetime import datetime, timezone


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


def parse_range(inicio: str | None, fim: str | None) -> tuple[datetime, datetime]:
    i = parse_iso_datetime(inicio, "inicio")
    f = parse_iso_datetime(fim, "fim")
    if i > f:
        raise DateRangeError("intervalo_invalido")
    return i, f

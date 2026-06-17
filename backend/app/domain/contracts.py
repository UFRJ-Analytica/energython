from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class ConstrainedOffEvent:
    timestamp: datetime
    energia_restringida_mwh: float
    razao_restricao: str | None
    cod_razaorestricao: str | None
    cod_origemrestricao: str | None = None
    origem_restricao: str | None = None
    usina_id: str | None = None
    fonte: str | None = None
    geracao_verificada_mwh: float | None = None
    geracao_referencia_mwh: float | None = None
    geracao_limitada_mwmed: float | None = None
    submercado: str | None = None


@dataclass(frozen=True)
class PldPoint:
    timestamp: datetime
    pld_reais_mwh: float


@dataclass(frozen=True)
class DisponibilidadePoint:
    timestamp: datetime
    disponibilidade: float
    teifa: float
    teip: float


@dataclass(frozen=True)
class DessemPoint:
    timestamp: datetime
    geracao_programada_mwh: float


@dataclass(frozen=True)
class GarantiaFisicaPoint:
    timestamp: datetime
    garantia_fisica_mwh: float


def _as_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    return datetime.fromisoformat(str(value)).replace(tzinfo=None)


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_constrained_off(items: list[dict[str, Any]]) -> list[ConstrainedOffEvent]:
    out: list[ConstrainedOffEvent] = []
    for e in items:
        out.append(
            ConstrainedOffEvent(
                timestamp=_as_datetime(e.get("timestamp")),
                energia_restringida_mwh=_as_float(e.get("energia_restringida_mwh")),
                razao_restricao=e.get("razao_restricao"),
                cod_razaorestricao=e.get("cod_razaorestricao"),
                cod_origemrestricao=e.get("cod_origemrestricao") or e.get("origem_restricao"),
                origem_restricao=e.get("origem_restricao"),
                usina_id=e.get("usina_id"),
                fonte=e.get("fonte"),
                geracao_verificada_mwh=_as_float(e.get("geracao_verificada_mwh")) if e.get("geracao_verificada_mwh") is not None else None,
                geracao_referencia_mwh=_as_float(e.get("geracao_referencia_mwh")) if e.get("geracao_referencia_mwh") is not None else None,
                geracao_limitada_mwmed=_as_float(e.get("geracao_limitada_mwmed")) if e.get("geracao_limitada_mwmed") is not None else None,
                submercado=e.get("submercado"),
            )
        )
    return out


def parse_pld(items: list[dict[str, Any]]) -> list[PldPoint]:
    out: list[PldPoint] = []
    for p in items:
        out.append(
            PldPoint(
                timestamp=_as_datetime(p.get("timestamp")),
                pld_reais_mwh=_as_float(p.get("pld_reais_mwh")),
            )
        )
    return out


def parse_disponibilidade(items: list[dict[str, Any]]) -> list[DisponibilidadePoint]:
    out: list[DisponibilidadePoint] = []
    for p in items:
        out.append(
            DisponibilidadePoint(
                timestamp=_as_datetime(p.get("timestamp")),
                disponibilidade=_as_float(p.get("disponibilidade")),
                teifa=_as_float(p.get("teifa")),
                teip=_as_float(p.get("teip")),
            )
        )
    return out


def parse_dessem(items: list[dict[str, Any]]) -> list[DessemPoint]:
    out: list[DessemPoint] = []
    for p in items:
        out.append(
            DessemPoint(
                timestamp=_as_datetime(p.get("timestamp")),
                geracao_programada_mwh=_as_float(p.get("geracao_programada_mwh")),
            )
        )
    return out


def parse_garantia_fisica(items: list[dict[str, Any]]) -> list[GarantiaFisicaPoint]:
    out: list[GarantiaFisicaPoint] = []
    for p in items:
        out.append(
            GarantiaFisicaPoint(
                timestamp=_as_datetime(p.get("timestamp")),
                garantia_fisica_mwh=_as_float(p.get("garantia_fisica_mwh")),
            )
        )
    return out

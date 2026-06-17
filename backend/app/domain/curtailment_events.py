from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any
import hashlib
import unicodedata

COFF_INTERVAL_HOURS = 0.5
COFF_VAL_GERACAOLIMITADA_UNIT = "mwmed"
COFF_ENERGY_UNIT_VALIDATED = True
COFF_ENERGY_FORMULA = "max((val_geracaoreferenciafinal or val_geracaoreferencia) - val_geracao, 0) * 0.5"


@dataclass(frozen=True)
class CurtailmentInterval:
    interval_id: str
    usina_id: str
    tecnologia: str | None
    timestamp_inicio: datetime
    timestamp_fim: datetime
    duracao_horas: float
    energia_restringida_mwh: float
    perda_reais: float
    geracao_verificada_mwh: float | None
    geracao_referencia_mwh: float | None
    cod_razaorestricao: str | None
    cod_origemrestricao: str | None
    razao_normalizada: str | None
    origem_normalizada: str | None
    submercado: str | None
    source_table: str
    data_quality_status: str


@dataclass(frozen=True)
class CurtailmentEvent:
    event_id: str
    usina_id: str
    tecnologia: str | None
    inicio: datetime
    fim: datetime
    duracao_horas: float
    n_intervalos: int
    cod_razaorestricao: str | None
    cod_origemrestricao: str | None
    razao_normalizada: str | None
    origem_normalizada: str | None
    energia_restringida_mwh: float
    perda_total_reais: float
    perda_potencial_ressarcivel_reais: float
    perda_ressarcivel_pos_franquia_reais: float
    elegibilidade_status: str
    evidence_score: int
    source_interval_ids: list[str]
    gap_detectado: bool = False


def _strip_accents(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))


def normalize_reason(value: str | None) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    token = _strip_accents(raw).upper().replace("-", "_").replace(" ", "_")
    if token.startswith("CNF") or token.startswith("CF") or "CONFIAB" in token:
        return "CNF"
    if token.startswith("REL") or token.startswith("IE") or "INDISP" in token:
        return "REL"
    if token.startswith("ENE") or token.startswith("EN") or "ENERGET" in token:
        return "ENE"
    if token in {"CONFIABILIDADE"}:
        return "CNF"
    return token


def normalize_origin(value: str | None) -> str | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    token = _strip_accents(raw).upper().replace("-", "_").replace(" ", "_")
    if token.startswith("SIS") or "SIST" in token:
        return "SIS"
    if token.startswith("LOC") or "LOCAL" in token:
        return "LOC"
    return token


def classify_regulatory_eligibility(reason: str | None, origin: str | None) -> str:
    reason_norm = normalize_reason(reason)
    origin_norm = normalize_origin(origin)
    if not reason_norm or not origin_norm:
        return "REVISAO_HUMANA"
    if reason_norm in {"CNF", "REL"} and origin_norm == "SIS":
        return "ELEGIVEL"
    if reason_norm in {"CNF", "REL"} and origin_norm == "LOC":
        return "REVISAO_HUMANA"
    if reason_norm == "ENE":
        return "NAO_ELEGIVEL"
    return "REVISAO_HUMANA"


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


def _as_optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _timestamp_key(ts: datetime) -> str:
    return str(ts.replace(tzinfo=None))


def calculate_coff_energy_mwh(row: dict[str, Any], *, fallback_precomputed_is_mwmed: bool = False) -> tuple[float, float | None, float | None]:
    """Return curtailed energy for ONS COFF rows.

    ONS COFF fields are MWmed for each 30-minute interval. The physical cut is
    reference generation minus verified generation, not val_geracaolimitada.
    val_geracaolimitada is retained only as diagnostic/source metadata.
    """
    raw_generation = row.get("val_geracao")
    raw_reference = row.get("val_geracaoreferenciafinal")
    if raw_reference in (None, ""):
        raw_reference = row.get("val_geracaoreferencia")

    has_official_coff_fields = raw_generation not in (None, "") and raw_reference not in (None, "")
    if has_official_coff_fields:
        generation_mwmed = _as_float(raw_generation)
        reference_mwmed = _as_float(raw_reference)
        restricted_mwh = max(reference_mwmed - generation_mwmed, 0.0) * COFF_INTERVAL_HOURS
        return restricted_mwh, generation_mwmed * COFF_INTERVAL_HOURS, reference_mwmed * COFF_INTERVAL_HOURS

    precomputed = _as_float(row.get("energia_restringida_mwh"))
    energy = precomputed * COFF_INTERVAL_HOURS if fallback_precomputed_is_mwmed else precomputed
    return energy, _as_optional_float(row.get("geracao_verificada_mwh")), _as_optional_float(row.get("geracao_referencia_mwh"))


def classify_interval_quality(energia_restringida_mwh: float, reason: str | None, origin: str | None) -> str:
    has_energy = energia_restringida_mwh > 0
    has_reason = bool(normalize_reason(reason))
    has_origin = bool(normalize_origin(origin))
    if not has_energy and not has_reason and not has_origin:
        return "SEM_RESTRICAO"
    if has_energy and has_reason and has_origin:
        return "RESTRICAO_CLASSIFICADA"
    if has_energy and (not has_reason or not has_origin):
        return "RESTRICAO_INCOMPLETA"
    return "METADADO_SEM_ENERGIA"


def build_curtailment_intervals(
    rows: list[dict[str, Any]],
    *,
    perda_por_intervalo: dict[str, float] | None = None,
    source_table: str = "constrained_off",
    convert_limited_value_from_mwmed: bool = True,
) -> list[CurtailmentInterval]:
    perda_por_intervalo = perda_por_intervalo or {}
    intervals: list[CurtailmentInterval] = []
    for idx, row in enumerate(rows):
        ts = _as_datetime(row.get("timestamp"))
        reason = row.get("cod_razaorestricao") or row.get("razao_restricao")
        origin = row.get("cod_origemrestricao") or row.get("origem_restricao")
        energia, geracao_verificada_mwh, geracao_referencia_mwh = calculate_coff_energy_mwh(
            row,
            fallback_precomputed_is_mwmed=convert_limited_value_from_mwmed,
        )
        quality = classify_interval_quality(energia, reason, origin)
        if energia <= 0 or quality == "SEM_RESTRICAO":
            continue
        usina_id = str(row.get("usina_id") or "")
        tecnologia = row.get("tecnologia") or row.get("fonte")
        interval_id = str(row.get("interval_id") or f"{usina_id}:{_timestamp_key(ts)}:{idx}")
        intervals.append(
            CurtailmentInterval(
                interval_id=interval_id,
                usina_id=usina_id,
                tecnologia=str(tecnologia) if tecnologia is not None else None,
                timestamp_inicio=ts,
                timestamp_fim=ts + timedelta(hours=COFF_INTERVAL_HOURS),
                duracao_horas=COFF_INTERVAL_HOURS,
                energia_restringida_mwh=energia,
                perda_reais=float(perda_por_intervalo.get(_timestamp_key(ts), 0.0)),
                geracao_verificada_mwh=geracao_verificada_mwh,
                geracao_referencia_mwh=geracao_referencia_mwh,
                cod_razaorestricao=str(reason) if reason is not None else None,
                cod_origemrestricao=str(origin) if origin is not None else None,
                razao_normalizada=normalize_reason(str(reason) if reason is not None else None),
                origem_normalizada=normalize_origin(str(origin) if origin is not None else None),
                submercado=str(row.get("submercado")) if row.get("submercado") is not None else None,
                source_table=str(row.get("source_table") or source_table),
                data_quality_status=quality,
            )
        )
    return sorted(intervals, key=lambda i: (i.usina_id, i.tecnologia or "", i.timestamp_inicio))


def _event_id(intervals: list[CurtailmentInterval]) -> str:
    first = intervals[0]
    raw = "|".join(
        [
            first.usina_id,
            first.tecnologia or "",
            first.razao_normalizada or "",
            first.origem_normalizada or "",
            first.timestamp_inicio.isoformat(),
            intervals[-1].timestamp_fim.isoformat(),
            str(len(intervals)),
        ]
    )
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:16]


def _make_event(intervals: list[CurtailmentInterval], *, gap_detectado: bool = False) -> CurtailmentEvent:
    first = intervals[0]
    perda_total = sum(i.perda_reais for i in intervals)
    status = classify_regulatory_eligibility(first.razao_normalizada, first.origem_normalizada)
    potencial = perda_total if status == "ELEGIVEL" else 0.0
    evidence_score = 100 if status == "ELEGIVEL" else 60 if status == "REVISAO_HUMANA" else 40
    return CurtailmentEvent(
        event_id=_event_id(intervals),
        usina_id=first.usina_id,
        tecnologia=first.tecnologia,
        inicio=intervals[0].timestamp_inicio,
        fim=intervals[-1].timestamp_fim,
        duracao_horas=round(sum(i.duracao_horas for i in intervals), 6),
        n_intervalos=len(intervals),
        cod_razaorestricao=first.cod_razaorestricao,
        cod_origemrestricao=first.cod_origemrestricao,
        razao_normalizada=first.razao_normalizada,
        origem_normalizada=first.origem_normalizada,
        energia_restringida_mwh=round(sum(i.energia_restringida_mwh for i in intervals), 6),
        perda_total_reais=round(perda_total, 6),
        perda_potencial_ressarcivel_reais=round(potencial, 6),
        perda_ressarcivel_pos_franquia_reais=round(potencial, 6),
        elegibilidade_status=status,
        evidence_score=evidence_score,
        source_interval_ids=[i.interval_id for i in intervals],
        gap_detectado=gap_detectado,
    )


def _same_partition(prev: CurtailmentInterval, cur: CurtailmentInterval) -> bool:
    return (
        prev.usina_id == cur.usina_id
        and (prev.tecnologia or "") == (cur.tecnologia or "")
        and (prev.razao_normalizada or "") == (cur.razao_normalizada or "")
        and (prev.origem_normalizada or "") == (cur.origem_normalizada or "")
    )


def group_intervals_into_events(
    intervals: list[CurtailmentInterval],
    *,
    expected_interval: timedelta = timedelta(minutes=30),
    tolerance: timedelta = timedelta(0),
) -> list[CurtailmentEvent]:
    if not intervals:
        return []
    ordered = sorted(
        intervals,
        key=lambda i: (
            i.usina_id,
            i.tecnologia or "",
            i.razao_normalizada or "",
            i.origem_normalizada or "",
            i.timestamp_inicio,
        ),
    )
    events: list[CurtailmentEvent] = []
    current: list[CurtailmentInterval] = [ordered[0]]
    current_started_after_gap = False
    for interval in ordered[1:]:
        prev = current[-1]
        gap = interval.timestamp_inicio > prev.timestamp_inicio + expected_interval + tolerance
        if not _same_partition(prev, interval) or gap:
            events.append(_make_event(current, gap_detectado=current_started_after_gap))
            current = [interval]
            current_started_after_gap = gap
        else:
            current.append(interval)
    events.append(_make_event(current, gap_detectado=current_started_after_gap))
    return sorted(events, key=lambda e: (e.inicio, e.usina_id, e.event_id))

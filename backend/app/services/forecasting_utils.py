from __future__ import annotations

import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from pathlib import Path

from app.domain.contracts import parse_constrained_off, parse_pld


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip().replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(raw)
    except Exception:
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
            try:
                dt = datetime.strptime(raw, fmt)
                break
            except Exception:
                dt = None
    if dt is None:
        return None
    if dt.tzinfo is not None:
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def _demo_cache_dir() -> Path:
    override = os.getenv("CURTAILMENT_DEMO_CACHE_DIR", "").strip()
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[2] / "models_ml" / "data_ml" / "temp_cache"


def _demo_cache_enabled() -> bool:
    mode = os.getenv("CURTAILMENT_DEMO_LOCAL_CACHE_ENABLED", "auto").strip().lower()
    if mode in {"1", "true", "yes", "on"}:
        return True
    if mode in {"0", "false", "no", "off"}:
        return False
    base = _demo_cache_dir()
    required = [
        base / "usinas_cache.csv",
        base / "flat_dados_eolica.csv",
        base / "flat_dados_solar.csv",
        base / "ccee_cache.csv",
    ]
    return all(p.exists() and p.stat().st_size > 0 for p in required)


@lru_cache(maxsize=1)
def _demo_usinas_map() -> dict[str, dict]:
    out: dict[str, dict] = {}
    path = _demo_cache_dir() / "usinas_cache.csv"
    if not path.exists():
        return out
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                uid = str(row.get("usina_id") or "").strip()
                if not uid:
                    continue
                out[uid] = {
                    "usina_id": uid,
                    "nome": str(row.get("nome") or "").strip(),
                    "fonte": str(row.get("fonte") or "").strip().lower(),
                    "submercado": str(row.get("submercado") or "").strip().upper(),
                }
    except Exception:
        return {}
    return out


@lru_cache(maxsize=64)
def _demo_event_points(usina_id: str) -> list[tuple[datetime, float]]:
    points: list[tuple[datetime, float]] = []
    base = _demo_cache_dir()
    for file_name in ("flat_dados_eolica.csv", "flat_dados_solar.csv"):
        path = base / file_name
        if not path.exists():
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if str(row.get("usina_id") or "").strip() != usina_id:
                        continue
                    ts = _parse_dt(str(row.get("timestamp") or ""))
                    if ts is None:
                        continue
                    try:
                        energia = float(row.get("energia_restringida_mwh") or 0.0)
                    except Exception:
                        energia = 0.0
                    points.append((ts, max(0.0, energia)))
        except Exception:
            continue
    points.sort(key=lambda x: x[0])
    return points


@lru_cache(maxsize=16)
def _demo_pld_points(submercado: str) -> list[tuple[datetime, float]]:
    points: list[tuple[datetime, float]] = []
    path = _demo_cache_dir() / "ccee_cache.csv"
    if not path.exists():
        return points
    subm_norm = (submercado or "").strip().upper()
    aliases = {"NE": "NORDESTE", "SE": "SUDESTE", "N": "NORTE", "S": "SUL"}
    subm_candidates = {subm_norm, aliases.get(subm_norm, subm_norm)}
    try:
        with path.open("r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                subm = str(row.get("submercado") or row.get("id_submercado") or "").strip().upper()
                if subm not in subm_candidates:
                    continue
                mes = str(row.get("mes_referencia") or "").strip()
                dia = str(row.get("dia") or "").strip().zfill(2)
                hora = str(row.get("hora") or "").strip().zfill(2)
                ts = _parse_dt(f"{mes}{dia}{hora}")
                if ts is None:
                    try:
                        ts = datetime.strptime(f"{mes}{dia}{hora}", "%Y%m%d%H")
                    except Exception:
                        ts = None
                if ts is None:
                    continue
                val_raw = str(row.get("pld_hora") or row.get("pld") or "0").replace(",", ".")
                try:
                    pld = float(val_raw)
                except Exception:
                    pld = 0.0
                points.append((ts, max(0.0, pld)))
    except Exception:
        return []
    points.sort(key=lambda x: x[0])
    return points


def _hourly_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _build_energy_seasonal_forecast(
    eventos_hist,
    horizon_hours: int,
    now: datetime,
) -> list[dict]:
    by_hour = defaultdict(list)
    by_weekday_hour = defaultdict(list)
    all_vals = []

    for e in eventos_hist:
        ts = e.timestamp
        val = max(0.0, float(e.energia_restringida_mwh or 0.0))
        by_hour[ts.hour].append(val)
        by_weekday_hour[(ts.weekday(), ts.hour)].append(val)
        all_vals.append(val)

    overall_mean = _hourly_mean(all_vals)

    out = []
    for i in range(horizon_hours):
        ts = now + timedelta(hours=i)
        mean_wh = _hourly_mean(by_weekday_hour[(ts.weekday(), ts.hour)])
        mean_h = _hourly_mean(by_hour[ts.hour])
        # fallback progressivo: weekday+hora -> hora -> média global
        pred = mean_wh if mean_wh > 0 else (mean_h if mean_h > 0 else overall_mean)
        out.append(
            {
                "timestamp": ts,
                "energia_prevista_mwh": round(max(0.0, pred), 4),
                "prob_corte": 0.5 if pred > 0 else 0.2,
                "fonte": "forecast_fallback_sazonal_hora",
            }
        )
    return out





def _floor_hour(dt: datetime) -> datetime:
    return dt.replace(minute=0, second=0, microsecond=0)


def _build_dense_hourly_energy_series(eventos_hist, start: datetime, end: datetime) -> list[tuple[datetime, float]]:
    """Build a complete hourly historical series, treating hours without events as 0 MWh.

    This is intentionally conservative for MVP BESS sizing: curtailment is episodic,
    so forecasting from event-only averages inflates future loss frequency.
    """
    start_h = _floor_hour(start)
    end_h = _floor_hour(end)
    by_hour = defaultdict(float)
    for e in eventos_hist:
        ts = _floor_hour(e.timestamp)
        if start_h <= ts <= end_h:
            by_hour[ts] += max(0.0, float(e.energia_restringida_mwh or 0.0))

    out: list[tuple[datetime, float]] = []
    current = start_h
    while current <= end_h:
        out.append((current, by_hour.get(current, 0.0)))
        current += timedelta(hours=1)
    return out


def _mean_by_hour(rows: list[tuple[datetime, float]]) -> dict[int, float]:
    grouped = defaultdict(list)
    for ts, val in rows:
        grouped[ts.hour].append(val)
    return {hour: _hourly_mean(vals) for hour, vals in grouped.items()}


def _build_energy_moving_average_forecast(
    eventos_hist,
    horizon_hours: int,
    now: datetime,
) -> tuple[list[dict], dict]:
    hist_30_start = now - timedelta(days=30)
    hist_7_start = now - timedelta(days=7)
    dense_30 = _build_dense_hourly_energy_series(eventos_hist, hist_30_start, now)
    dense_7 = [(ts, val) for ts, val in dense_30 if ts >= _floor_hour(hist_7_start)]

    total_30 = sum(val for _, val in dense_30)
    total_7 = sum(val for _, val in dense_7)
    avg_30_global = _hourly_mean([val for _, val in dense_30])
    avg_7_global = _hourly_mean([val for _, val in dense_7])
    by_hour_30 = _mean_by_hour(dense_30)
    by_hour_7 = _mean_by_hour(dense_7)

    raw_items = []
    raw_total = 0.0
    for i in range(horizon_hours):
        ts = now + timedelta(hours=i)
        pred = (
            0.60 * by_hour_30.get(ts.hour, avg_30_global)
            + 0.25 * by_hour_7.get(ts.hour, avg_7_global)
            + 0.15 * avg_30_global
        )
        pred = max(0.0, pred)
        raw_total += pred
        raw_items.append((ts, pred))

    horizon_days = max(horizon_hours / 24.0, 1 / 24.0)
    scale_to_30d = horizon_days / 30.0
    expected_7_for_30_window = total_30 * (7 / 30) if total_30 > 0 else 0.0
    recent_spike = bool(expected_7_for_30_window > 0 and total_7 > expected_7_for_30_window * 1.5)
    cap_multiplier_30d = 1.30 if recent_spike else 1.15
    cap_for_horizon = total_30 * cap_multiplier_30d * scale_to_30d

    guardrail_applied = total_30 <= 0 < raw_total or (cap_for_horizon > 0 and raw_total > cap_for_horizon)
    adjusted_total = 0.0 if total_30 <= 0 else min(raw_total, cap_for_horizon if cap_for_horizon > 0 else raw_total)
    factor = (adjusted_total / raw_total) if raw_total > 0 else 0.0

    out = []
    for ts, raw_pred in raw_items:
        pred = raw_pred * factor
        out.append(
            {
                "timestamp": ts,
                "energia_prevista_mwh": round(pred, 4),
                "prob_corte": 0.5 if pred > 0 else 0.0,
                "fonte": "media_movel_7_30d_com_zeros_guardrail",
            }
        )

    metadata = {
        "historico_base_30d_mwh": round(total_30, 4),
        "historico_base_7d_mwh": round(total_7, 4),
        "previsao_bruta_mwh": round(raw_total, 4),
        "previsao_ajustada_mwh": round(adjusted_total, 4),
        "guardrail_aplicado": guardrail_applied,
        "teto_multiplicador_30d": cap_multiplier_30d,
        "recent_spike": recent_spike,
    }
    return out, metadata


def _build_pld_seasonal_forecast(pld_hist, horizon_hours: int, now: datetime) -> list[dict]:
    by_hour = defaultdict(list)
    by_weekday_hour = defaultdict(list)
    all_vals = []

    for p in pld_hist:
        ts = p.timestamp
        val = max(0.0, float(p.pld_reais_mwh or 0.0))
        by_hour[ts.hour].append(val)
        by_weekday_hour[(ts.weekday(), ts.hour)].append(val)
        all_vals.append(val)

    overall_mean = _hourly_mean(all_vals)

    out = []
    for i in range(horizon_hours):
        ts = now + timedelta(hours=i)
        mean_wh = _hourly_mean(by_weekday_hour[(ts.weekday(), ts.hour)])
        mean_h = _hourly_mean(by_hour[ts.hour])
        pred = mean_wh if mean_wh > 0 else (mean_h if mean_h > 0 else overall_mean)
        out.append({"timestamp": ts, "pld_previsto_reais_mwh": round(max(0.0, pred), 4)})
    return out


def forecast_future_losses(
    repo,
    usina: dict,
    horizon_hours: int = 48,
    ml_model_path: str = "models_ml/curtailment_model.pkl",
    use_ml: bool = False,
) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    hist_start = now - timedelta(days=30)

    eventos_hist = []
    pld_hist = []
    metodo_cache = ""
    if _demo_cache_enabled() and usina.get("usina_id") in _demo_usinas_map():
        raw_events = _demo_event_points(str(usina["usina_id"]))
        eventos_hist = [
            type("Evt", (), {"timestamp": ts, "energia_restringida_mwh": energia})
            for ts, energia in raw_events
            if hist_start <= ts <= now
        ]
        raw_pld = _demo_pld_points(str(usina.get("submercado") or ""))
        pld_hist = [
            type("Pld", (), {"timestamp": ts, "pld_reais_mwh": pld})
            for ts, pld in raw_pld
            if hist_start <= ts <= now
        ]
        metodo_cache = "demo_cache_local"

    if not eventos_hist:
        eventos_hist = parse_constrained_off(repo.get_constrained_off(usina["usina_id"], hist_start, now))
    if not pld_hist:
        pld_hist = parse_pld(repo.get_pld(usina["submercado"], hist_start, now))

    pld_forecast = _build_pld_seasonal_forecast(pld_hist, horizon_hours=horizon_hours, now=now)
    pld_map = {item["timestamp"]: item["pld_previsto_reais_mwh"] for item in pld_forecast}

    method = "media_movel_7_30d_com_zeros_guardrail"
    forecast_metadata = {}

    if use_ml:
        try:
            from app.ml.features import build_inference_frame
            from app.ml.predictor import CurtailmentPredictor

            predictor = CurtailmentPredictor(ml_model_path)
            clima_future = repo.get_clima_horario(usina["usina_id"], now, now + timedelta(hours=horizon_hours), is_forecast=True)
            geracao_recent = repo.get_geracao_horaria(usina["usina_id"], now - timedelta(hours=48), now)
            constrained_recent = repo.get_constrained_off(usina["usina_id"], now - timedelta(hours=48), now)
            disponibilidade_recent = repo.get_disponibilidade_usina(usina["usina_id"], now - timedelta(hours=48), now)
            dessem_recent = repo.get_despacho_dessem(usina["usina_id"], now - timedelta(hours=48), now)
            garantia_fisica_recent = repo.get_garantia_fisica(usina["usina_id"], now - timedelta(hours=48), now)

            if clima_future:
                feat_df = build_inference_frame(
                    usina=usina,
                    clima_future=clima_future,
                    geracao_recent=geracao_recent,
                    constrained_recent=constrained_recent,
                    pld_recent=repo.get_pld(usina["submercado"], now - timedelta(hours=48), now),
                    disponibilidade_recent=disponibilidade_recent,
                    dessem_recent=dessem_recent,
                    garantia_fisica_recent=garantia_fisica_recent,
                )
                ml_preds = predictor.predict(feat_df)
                if ml_preds:
                    method = "ml_base_random_forest"
                    energy_forecast = []
                    for p in ml_preds[:horizon_hours]:
                        ts = datetime.fromisoformat(str(p["timestamp"]).replace("Z", "+00:00")).replace(tzinfo=None)
                        energy_forecast.append(
                            {
                                "timestamp": ts,
                                "energia_prevista_mwh": max(0.0, float(p.get("magnitude_estimada_mwh", 0.0) or 0.0)),
                                "prob_corte": float(p.get("prob_corte", 0.0) or 0.0),
                                "fonte": "ml",
                            }
                        )
                else:
                    energy_forecast, forecast_metadata = _build_energy_moving_average_forecast(eventos_hist, horizon_hours, now)
            else:
                energy_forecast, forecast_metadata = _build_energy_moving_average_forecast(eventos_hist, horizon_hours, now)
        except Exception:
            energy_forecast, forecast_metadata = _build_energy_moving_average_forecast(eventos_hist, horizon_hours, now)
    else:
        energy_forecast, forecast_metadata = _build_energy_moving_average_forecast(eventos_hist, horizon_hours, now)

    series = []
    total_energy = 0.0
    total_financial = 0.0
    for item in energy_forecast:
        ts = item["timestamp"]
        energy = max(0.0, float(item["energia_prevista_mwh"]))
        pld = max(0.0, float(pld_map.get(ts, 0.0)))
        loss = energy * pld
        total_energy += energy
        total_financial += loss
        series.append(
            {
                "timestamp": ts.isoformat(),
                "energia_prevista_mwh": round(energy, 4),
                "pld_previsto_reais_mwh": round(pld, 4),
                "perda_prevista_reais": round(loss, 2),
                "prob_corte": round(float(item.get("prob_corte", 0.0) or 0.0), 4),
                "tipo_dado": "previsao",
            }
        )

    if metodo_cache and method in {"fallback_sazonal", "media_movel_7_30d_com_zeros_guardrail"}:
        method = f"{method}+{metodo_cache}"

    return {
        "metodo_previsao": method,
        "horizonte_horas": horizon_hours,
        "energia_total_prevista_mwh": round(total_energy, 4),
        "perda_total_prevista_reais": round(total_financial, 2),
        "serie_previsao": series,
        "metadados_previsao": forecast_metadata,
    }


def list_demo_cache_usinas() -> list[dict]:
    return sorted(_demo_usinas_map().values(), key=lambda x: x.get("usina_id") or "")


def build_historical_vs_forecast_losses(
    repo,
    usina: dict,
    horizonte_horas: int = 48,
    historico_horas: int = 168,
) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    hist_start = now - timedelta(hours=historico_horas)

    eventos_hist = parse_constrained_off(repo.get_constrained_off(usina["usina_id"], hist_start, now))
    pld_hist = parse_pld(repo.get_pld(usina["submercado"], hist_start, now))
    pld_map_hist = {p.timestamp: p.pld_reais_mwh for p in pld_hist}

    serie_historico = []
    total_hist = 0.0
    for e in eventos_hist:
        pld = float(pld_map_hist.get(e.timestamp, 0.0) or 0.0)
        perda = max(0.0, float(e.energia_restringida_mwh or 0.0)) * max(0.0, pld)
        total_hist += perda
        serie_historico.append(
            {
                "timestamp": e.timestamp.isoformat(),
                "energia_mwh": round(max(0.0, float(e.energia_restringida_mwh or 0.0)), 4),
                "pld_reais_mwh": round(max(0.0, pld), 4),
                "perda_reais": round(perda, 2),
                "tipo_dado": "historico",
            }
        )

    previsao = forecast_future_losses(repo=repo, usina=usina, horizon_hours=horizonte_horas)
    serie_previsao = [
        {
            "timestamp": item["timestamp"],
            "energia_mwh": item["energia_prevista_mwh"],
            "pld_reais_mwh": item["pld_previsto_reais_mwh"],
            "perda_reais": item["perda_prevista_reais"],
            "tipo_dado": "previsao",
            "prob_corte": item.get("prob_corte", 0.0),
        }
        for item in previsao["serie_previsao"]
    ]

    return {
        "metodo_previsao": previsao["metodo_previsao"],
        "horizonte_horas": horizonte_horas,
        "historico_horas": historico_horas,
        "resumo": {
            "perda_historica_reais": round(total_hist, 2),
            "perda_prevista_reais": round(previsao["perda_total_prevista_reais"], 2),
            "energia_historica_mwh": round(sum(i["energia_mwh"] for i in serie_historico), 4),
            "energia_prevista_mwh": round(previsao["energia_total_prevista_mwh"], 4),
        },
        "serie_historico": serie_historico,
        "serie_previsao": serie_previsao,
    }

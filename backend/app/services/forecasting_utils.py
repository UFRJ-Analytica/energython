from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

from app.domain.contracts import parse_constrained_off, parse_pld


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
) -> dict:
    now = datetime.now(timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
    hist_start = now - timedelta(days=30)

    eventos_hist = parse_constrained_off(repo.get_constrained_off(usina["usina_id"], hist_start, now))
    pld_hist = parse_pld(repo.get_pld(usina["submercado"], hist_start, now))

    pld_forecast = _build_pld_seasonal_forecast(pld_hist, horizon_hours=horizon_hours, now=now)
    pld_map = {item["timestamp"]: item["pld_previsto_reais_mwh"] for item in pld_forecast}

    method = "fallback_sazonal"

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
                energy_forecast = _build_energy_seasonal_forecast(eventos_hist, horizon_hours, now)
        else:
            energy_forecast = _build_energy_seasonal_forecast(eventos_hist, horizon_hours, now)
    except Exception:
        energy_forecast = _build_energy_seasonal_forecast(eventos_hist, horizon_hours, now)

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

    return {
        "metodo_previsao": method,
        "horizonte_horas": horizon_hours,
        "energia_total_prevista_mwh": round(total_energy, 4),
        "perda_total_prevista_reais": round(total_financial, 2),
        "serie_previsao": series,
    }


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

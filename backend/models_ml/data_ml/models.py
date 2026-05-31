"""
advanced_predictor.py — Preditor Avançado de Curtailment (Prophet + CatBoost)
=============================================================================

Módulo de predição que carrega o bundle avançado (Prophet + CatBoost) e
gera previsões detalhadas para analistas do setor de energia.

Diferenças em relação ao predictor.py base:
  • Suporte a modelos CatBoost nativos (sem necessidade de Pipeline sklearn)
  • Decomposição temporal via Prophet (trend, seasonality, holidays)
  • Previsões com intervalos de confiança
  • Contexto analítico rico (feature importances por predição, regime operacional)
  • Alertas automáticos baseados em limiares configuráveis
  • Compatível retroativamente com o bundle base (sklearn)

Uso no backend (via app/ml/predictor.py ou direto):
    from models_ml.advanced_predictor import AdvancedCurtailmentPredictor

    predictor = AdvancedCurtailmentPredictor("models_ml/curtailment_model_advanced.pkl")
    results = predictor.predict(features_df)
    results_detail = predictor.predict_detailed(features_df)
    decomposition = predictor.get_prophet_forecast(horizonte_horas=48)
"""

from __future__ import annotations

import json
import logging
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Limiares de alerta para analistas
# ---------------------------------------------------------------------------

ALERT_THRESHOLDS = {
    "prob_corte_alto": 0.7,       # Probabilidade alta de corte
    "prob_corte_medio": 0.4,      # Probabilidade moderada
    "magnitude_severa_mwh": 20.0, # Magnitude severa (MWh)
    "magnitude_alta_mwh": 10.0,   # Magnitude alta
}


class AdvancedCurtailmentPredictor:
    """
    Preditor avançado de curtailment com suporte a Prophet + CatBoost.
    Retrocompatível com bundles sklearn (RandomForest).
    """

    def __init__(self, model_path: str, thresholds: dict | None = None):
        self.model_path = Path(model_path)
        self.bundle = self._load_bundle()
        self.thresholds = thresholds or ALERT_THRESHOLDS
        self._engine = self.bundle.get("engine", "sklearn_fallback")
        self._version = self.bundle.get("version", "v1_base")

    def _load_bundle(self) -> dict:
        """Carrega o bundle de modelos. Suporta tanto v1 (base) quanto v2 (avançado)."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {self.model_path}")
        with self.model_path.open("rb") as f:
            bundle = pickle.load(f)

        # Validar campos obrigatórios
        required = ["classifier", "regressor", "feature_cols"]
        missing = [k for k in required if k not in bundle]
        if missing:
            raise ValueError(f"Bundle incompleto — faltam campos: {missing}")

        logger.info(
            f"Modelo carregado: engine={bundle.get('engine', 'sklearn')}, "
            f"version={bundle.get('version', 'v1')}, "
            f"features={len(bundle['feature_cols'])}"
        )
        return bundle

    @property
    def feature_cols(self) -> list[str]:
        return list(self.bundle.get("feature_cols", []))

    @property
    def cat_cols(self) -> list[str]:
        return list(self.bundle.get("cat_cols", ["fonte", "submercado"]))

    @property
    def num_cols(self) -> list[str]:
        return list(self.bundle.get("num_cols", [c for c in self.feature_cols if c not in self.cat_cols]))

    @property
    def metrics(self) -> dict:
        return self.bundle.get("metrics", {})

    @property
    def feature_importances(self) -> dict:
        return self.bundle.get("feature_importances", {})

    @property
    def model_info(self) -> dict:
        """Informações do modelo para o frontend/documentação."""
        return {
            "engine": self._engine,
            "version": self._version,
            "trained_at": self.bundle.get("trained_at"),
            "threshold_mwh": self.bundle.get("threshold_mwh", 1.0),
            "n_features": len(self.feature_cols),
            "features": self.feature_cols,
            "cat_features": self.cat_cols,
            "metrics_resumo": {
                "auc": self.metrics.get("auc") or self.metrics.get("classificacao", {}).get("auc_roc"),
                "mae_mwh": self.metrics.get("mae") or self.metrics.get("regressao", {}).get("mae_mwh"),
                "train_rows": self.metrics.get("train_rows") or self.metrics.get("dataset", {}).get("train_rows"),
                "test_rows": self.metrics.get("test_rows") or self.metrics.get("dataset", {}).get("test_rows"),
            },
        }

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepara features para predição — suporta CatBoost e sklearn."""
        X = df.copy()
        for c in self.feature_cols:
            if c not in X.columns:
                X[c] = 0.0
        for c in self.cat_cols:
            if c in X.columns:
                X[c] = X[c].astype(str)
        return X[self.feature_cols]

    # ------------------------------------------------------------------
    # Predição básica (compatível com o predictor.py base)
    # ------------------------------------------------------------------

    def predict(self, features_df: pd.DataFrame) -> list[dict]:
        """
        Predição básica — retrocompatível com CurtailmentPredictor.predict().
        Retorna lista de {timestamp, prob_corte, magnitude_estimada_mwh}.
        """
        if features_df.empty:
            return []

        X = self._prepare(features_df)
        clf = self.bundle["classifier"]
        reg = self.bundle["regressor"]

        # Classificação
        prob = self._get_probabilities(clf, X)

        # Regressão
        mag = reg.predict(X)
        mag = [max(0.0, float(v)) for v in mag]

        out = []
        for ts, p, m in zip(features_df["timestamp"].tolist(), prob, mag):
            out.append({
                "timestamp": pd.to_datetime(ts).isoformat(),
                "prob_corte": round(float(p), 4),
                "magnitude_estimada_mwh": round(float(m), 4),
            })
        return out

    # ------------------------------------------------------------------
    # Predição detalhada (para analistas do setor de energia)
    # ------------------------------------------------------------------

    def predict_detailed(
        self,
        features_df: pd.DataFrame,
        pld_medio_reais_mwh: float = 200.0,
        usina_info: dict | None = None,
    ) -> dict[str, Any]:
        """
        Predição detalhada com contexto analítico rico.

        Retorna:
            - previsoes: lista de previsões hora a hora com alertas
            - resumo: KPIs consolidados para o período
            - decomposicao_temporal: componentes Prophet (se disponível)
            - importancia_features: ranking de importância para interpretação
            - alertas: eventos de alto risco identificados
        """
        if features_df.empty:
            return {
                "previsoes": [],
                "resumo": {"horizonte_horas": 0},
                "alertas": [],
            }

        X = self._prepare(features_df)
        clf = self.bundle["classifier"]
        reg = self.bundle["regressor"]

        # Classificação com probabilidades
        prob = self._get_probabilities(clf, X)

        # Regressão
        mag_raw = reg.predict(X)
        mag = [max(0.0, float(v)) for v in mag_raw]

        # ---- Construir previsões detalhadas ----
        previsoes = []
        alertas = []
        total_magnitude = 0.0
        total_perda_estimada = 0.0
        horas_alto_risco = 0
        horas_medio_risco = 0

        for i, (ts, p, m) in enumerate(zip(features_df["timestamp"].tolist(), prob, mag)):
            ts_dt = pd.to_datetime(ts)

            # Classificar nível de risco
            if p >= self.thresholds["prob_corte_alto"]:
                nivel_risco = "ALTO"
                horas_alto_risco += 1
            elif p >= self.thresholds["prob_corte_medio"]:
                nivel_risco = "MODERADO"
                horas_medio_risco += 1
            else:
                nivel_risco = "BAIXO"

            # Classificar severidade da magnitude
            if m >= self.thresholds["magnitude_severa_mwh"]:
                severidade_magnitude = "SEVERA"
            elif m >= self.thresholds["magnitude_alta_mwh"]:
                severidade_magnitude = "ALTA"
            else:
                severidade_magnitude = "NORMAL"

            # Perda financeira estimada
            perda_estimada = round(float(m * pld_medio_reais_mwh * p), 2)
            total_magnitude += m * p  # Magnitude ponderada pela probabilidade
            total_perda_estimada += perda_estimada

            entry = {
                "timestamp": ts_dt.isoformat(),
                "hora": ts_dt.hour,
                "dia_semana": ts_dt.strftime("%A"),
                "prob_corte": round(float(p), 4),
                "prob_corte_pct": f"{float(p)*100:.1f}%",
                "magnitude_estimada_mwh": round(float(m), 4),
                "nivel_risco": nivel_risco,
                "severidade_magnitude": severidade_magnitude,
                "perda_estimada_reais": perda_estimada,
                "pld_usado_reais_mwh": pld_medio_reais_mwh,
            }

            # Contexto operacional
            if "vento_ms" in features_df.columns:
                entry["vento_ms"] = round(float(features_df.iloc[i].get("vento_ms", 0)), 1)
            if "irradiancia_wm2" in features_df.columns:
                entry["irradiancia_wm2"] = round(float(features_df.iloc[i].get("irradiancia_wm2", 0)), 0)
            if "fator_capacidade" in features_df.columns:
                entry["fator_capacidade"] = round(float(features_df.iloc[i].get("fator_capacidade", 0)), 3)

            previsoes.append(entry)

            # Gerar alerta se risco alto
            if nivel_risco == "ALTO":
                alerta = {
                    "timestamp": ts_dt.isoformat(),
                    "tipo": "RISCO_ALTO_CORTE",
                    "prob_corte_pct": f"{float(p)*100:.1f}%",
                    "magnitude_estimada_mwh": round(float(m), 2),
                    "perda_estimada_reais": perda_estimada,
                    "recomendacao": self._gerar_recomendacao(p, m, ts_dt, usina_info),
                }
                alertas.append(alerta)

        # ---- Resumo consolidado ----
        resumo = {
            "horizonte_horas": len(previsoes),
            "modelo": self._engine,
            "versao": self._version,
            "pld_medio_usado_reais_mwh": pld_medio_reais_mwh,
            "risco": {
                "horas_alto_risco": horas_alto_risco,
                "horas_medio_risco": horas_medio_risco,
                "horas_baixo_risco": len(previsoes) - horas_alto_risco - horas_medio_risco,
                "prob_media_corte": round(float(np.mean(prob)), 4),
                "prob_max_corte": round(float(np.max(prob)), 4),
            },
            "impacto_estimado": {
                "magnitude_total_esperada_mwh": round(float(total_magnitude), 2),
                "perda_total_estimada_reais": round(float(total_perda_estimada), 2),
                "magnitude_media_por_hora_mwh": round(float(total_magnitude / max(len(previsoes), 1)), 2),
            },
            "total_alertas": len(alertas),
        }

        if usina_info:
            resumo["usina"] = {
                "usina_id": usina_info.get("usina_id"),
                "nome": usina_info.get("nome"),
                "fonte": usina_info.get("fonte"),
                "potencia_mw": usina_info.get("potencia_mw"),
                "submercado": usina_info.get("submercado"),
            }

        # ---- Feature importances (do modelo treinado) ----
        fi = self.feature_importances
        if fi:
            resumo["importancia_features"] = fi

        # ---- Decomposição Prophet (se disponível no bundle) ----
        decomposicao = None
        prophet_model = self.bundle.get("prophet_model")
        if prophet_model is not None:
            try:
                # Fazer inferência rápida de pelo menos 48h
                horizonte = max(48, len(previsoes))
                decomposicao = self._get_prophet_decomposition(horizonte)
            except Exception as e:
                logger.warning(f"Erro ao gerar decomposição Prophet: {e}")

        # ---- Insights de Similaridade (KNN) ----
        knn_insights = {}
        try:
            from models_ml.knn_pca_insights import run_knn_analysis
            # O KNN precisa de 'houve_corte', simulamos baseado na probabilidade alta para a análise rápida
            df_knn = features_df.copy()
            df_knn["houve_corte"] = [1 if p >= self.thresholds["prob_corte_alto"] else 0 for p in prob]
            knn_insights = run_knn_analysis(df_knn, n_neighbors=3)
        except Exception as e:
            logger.warning(f"Erro ao gerar insights KNN: {e}")

        return {
            "previsoes": previsoes,
            "resumo": resumo,
            "alertas": alertas,
            "decomposicao_temporal": decomposicao,
            "knn_insights": knn_insights,
        }

    # ------------------------------------------------------------------
    # Prophet: decomposição temporal
    # ------------------------------------------------------------------

    def get_prophet_forecast(self, horizonte_horas: int = 48) -> dict | None:
        """
        Gera forecast do Prophet para o horizonte especificado.
        Retorna componentes de decomposição temporal.
        """
        return self._get_prophet_decomposition(horizonte_horas)

    def _get_prophet_decomposition(self, horizonte_horas: int) -> dict | None:
        """Obtém decomposição temporal do Prophet."""
        prophet_model = self.bundle.get("prophet_model")
        if prophet_model is None:
            return None

        try:
            future = prophet_model.make_future_dataframe(periods=horizonte_horas, freq="h")

            # Adicionar regressores se necessário
            if hasattr(prophet_model, "extra_regressors") and prophet_model.extra_regressors:
                for reg_name in prophet_model.extra_regressors:
                    if reg_name == "hora_sin":
                        future["hora_sin"] = np.sin(2 * np.pi * future["ds"].dt.hour / 24)
                    elif reg_name == "hora_cos":
                        future["hora_cos"] = np.cos(2 * np.pi * future["ds"].dt.hour / 24)

            forecast = prophet_model.predict(future)
            
            base_trend = max(20.0, forecast["trend"].median())
            forecast["yhat"] = forecast["yhat"] - forecast["trend"] + base_trend
            forecast["trend"] = base_trend

            # Extrair componentes do forecast futuro
            future_forecast = forecast.tail(horizonte_horas)

            decomposicao = {
                "horizonte_horas": horizonte_horas,
                "previsao_serie_temporal": [
                    {
                        "timestamp": row["ds"].isoformat() if hasattr(row["ds"], "isoformat") else str(row["ds"]),
                        "valor_previsto_mwh": round(float(max(0, row["yhat"])), 2),
                        "intervalo_inferior_mwh": round(float(max(0, row["yhat_lower"])), 2),
                        "intervalo_superior_mwh": round(float(row["yhat_upper"]), 2),
                        "tendencia": round(float(row["trend"]), 2),
                    }
                    for _, row in future_forecast.iterrows()
                ],
                "componentes": {},
            }

            # Sazonalidade semanal
            if "weekly" in forecast.columns:
                decomposicao["componentes"]["semanal"] = {
                    "interpretacao": (
                        "Padrão semanal de curtailment. Valores positivos "
                        "indicam dias com mais corte (tipicamente fins de semana)."
                    ),
                    "valores": [
                        {
                            "timestamp": row["ds"].isoformat() if hasattr(row["ds"], "isoformat") else str(row["ds"]),
                            "efeito_mwh": round(float(row["weekly"]), 4),
                        }
                        for _, row in future_forecast.iterrows()
                    ],
                }

            # Sazonalidade diária
            if "daily" in forecast.columns:
                decomposicao["componentes"]["diario"] = {
                    "interpretacao": (
                        "Padrão diário (intraday) de curtailment. Para usinas "
                        "solares, o pico é tipicamente entre 10h-14h. Para eólicas, "
                        "de madrugada."
                    ),
                    "valores": [
                        {
                            "timestamp": row["ds"].isoformat() if hasattr(row["ds"], "isoformat") else str(row["ds"]),
                            "efeito_mwh": round(float(row["daily"]), 4),
                        }
                        for _, row in future_forecast.iterrows()
                    ],
                }

            # Efeito de feriados
            if "holidays" in forecast.columns:
                holidays_effect = future_forecast[future_forecast["holidays"].abs() > 0.01]
                if len(holidays_effect) > 0:
                    decomposicao["componentes"]["feriados"] = {
                        "interpretacao": (
                            "Efeito de feriados no curtailment. Feriados tipicamente "
                            "reduzem demanda e aumentam o risco de corte por sobreoferta."
                        ),
                        "valores": [
                            {
                                "timestamp": row["ds"].isoformat() if hasattr(row["ds"], "isoformat") else str(row["ds"]),
                                "efeito_mwh": round(float(row["holidays"]), 4),
                            }
                            for _, row in holidays_effect.iterrows()
                        ],
                    }

            return decomposicao

        except Exception as e:
            logger.warning(f"Erro na decomposição Prophet: {e}")
            return None

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_probabilities(self, clf: Any, X: pd.DataFrame) -> list[float]:
        """Obtém probabilidades do classificador (CatBoost ou sklearn)."""
        try:
            prob_arr = clf.predict_proba(X)
            if hasattr(prob_arr, "shape"):
                if prob_arr.shape[1] == 1:
                    cls = int(getattr(clf, "classes_", [0])[0])
                    return [1.0 if cls == 1 else 0.0] * len(X)
                return prob_arr[:, 1].tolist()
            return [float(p) for p in prob_arr]
        except Exception:
            # Fallback: usar predict binário
            try:
                preds = clf.predict(X)
                return [float(p) for p in preds]
            except Exception:
                return [0.5] * len(X)

    def _gerar_recomendacao(
        self, prob: float, magnitude: float, timestamp: datetime, usina_info: dict | None
    ) -> str:
        """Gera recomendação textual para o analista."""
        recomendacoes = []

        if prob >= 0.8:
            recomendacoes.append(
                "Risco muito alto de corte. Considere avaliar exposição financeira "
                "e preparar estratégia de hedge."
            )
        elif prob >= 0.6:
            recomendacoes.append(
                "Risco elevado de corte. Monitorar condições de rede e "
                "despacho programado."
            )

        if magnitude >= 20:
            recomendacoes.append(
                "Magnitude estimada severa. Verificar se a usina possui "
                "BESS para mitigação ou se há flexibilidade de despacho."
            )

        hora = timestamp.hour if hasattr(timestamp, "hour") else 12
        if usina_info and usina_info.get("fonte") == "solar" and 10 <= hora <= 14:
            recomendacoes.append(
                "Horário de pico solar coincide com o período de maior risco. "
                "Padrão consistente com sobreoferta no NE."
            )
        elif usina_info and usina_info.get("fonte") == "eolica" and (hora < 6 or hora > 22):
            recomendacoes.append(
                "Horário de madrugada com risco eólico elevado. "
                "Demanda baixa combinada com geração eólica forte."
            )

        if not recomendacoes:
            recomendacoes.append("Monitorar evolução do risco nas próximas horas.")

        return " ".join(recomendacoes)

    # ------------------------------------------------------------------
    # Análise de contribuição de features (para explicabilidade)
    # ------------------------------------------------------------------

    def explain_prediction(self, features_row: pd.Series | dict) -> dict[str, Any]:
        """
        Explica uma predição individual mostrando a contribuição de cada feature.
        Útil para analistas entenderem por que o modelo prevê risco alto/baixo.
        """
        if isinstance(features_row, dict):
            features_row = pd.Series(features_row)

        X = pd.DataFrame([features_row])
        X = self._prepare(X)

        clf = self.bundle["classifier"]
        reg = self.bundle["regressor"]

        prob = self._get_probabilities(clf, X)[0]
        mag = max(0.0, float(reg.predict(X)[0]))

        # Feature importances do modelo
        fi = self.feature_importances
        clf_fi = fi.get("classificador", {})
        if not clf_fi:
            # Fallback para importâncias do regressor se classificador não estiver disponível
            clf_fi = fi.get("regressor", {})

        # Construir explicação
        explicacao = {
            "prob_corte": round(prob, 4),
            "magnitude_estimada_mwh": round(mag, 4),
            "fatores_contribuintes": [],
        }

        for feat in sorted(clf_fi.keys(), key=lambda f: -clf_fi.get(f, 0)):
            valor = features_row.get(feat, None)
            if valor is not None:
                explicacao["fatores_contribuintes"].append({
                    "feature": feat,
                    "valor": float(valor) if not isinstance(valor, str) else valor,
                    "importancia_global": clf_fi.get(feat, 0),
                    "descricao": _feature_descriptions().get(feat, feat),
                })

        return explicacao


def _feature_descriptions() -> dict[str, str]:
    """Descrições das features para analistas."""
    return {
        "fator_capacidade": "Fator de capacidade da usina (0-1). Valores altos indicam geração próxima ao máximo.",
        "geracao_mwh": "Geração verificada em MWh no período.",
        "irradiancia_wm2": "Irradiância solar (W/m²). Relevante para usinas fotovoltaicas.",
        "vento_ms": "Velocidade do vento (m/s). Relevante para usinas eólicas.",
        "temperatura_c": "Temperatura ambiente (°C). Proxy de demanda elétrica.",
        "pld_reais_mwh": "Preço de Liquidação das Diferenças (R$/MWh). PLD baixo = risco maior de corte.",
        "mm_corte_3h": "Média móvel de corte nas últimas 3 horas. Indica persistência de curtailment.",
        "mm_corte_24h": "Média móvel de corte nas últimas 24 horas. Captura tendência diária.",
        "hora": "Hora do dia (0-23). Picos solares ~12h, eólicos ~3h.",
        "dia_semana": "Dia da semana (0=seg, 6=dom). Fins de semana têm mais corte.",
        "is_weekend": "Flag de fim de semana (0/1). Demanda mais baixa → mais corte.",
        "fonte": "Tipo da usina: eolica ou solar.",
        "submercado": "Submercado elétrico: NE, N, SE_CO, S.",
    }

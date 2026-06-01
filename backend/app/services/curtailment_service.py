from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import importlib.util


class CurtailmentService:
    def __init__(
        self,
        repo,
        model_path: str = "models_ml/curtailment_model.pkl",
        model_mode: str = "auto",  # auto | base | advanced
        advanced_model_path: str = "models_ml/curtailment_model_advanced.pkl",
        advanced_module_path: str = "models_ml/data_ml/models.py",
    ):
        self.repo = repo
        self.model_path = model_path
        self.model_mode = model_mode
        self.advanced_model_path = advanced_model_path
        self.advanced_module_path = advanced_module_path
        self._predictor_base = None
        self._predictor_advanced = None

    def _get_predictor_base(self):
        if self._predictor_base is not None:
            return self._predictor_base
        try:
            from app.ml.predictor import CurtailmentPredictor

            self._predictor_base = CurtailmentPredictor(self.model_path)
            return self._predictor_base
        except Exception:
            return None

    def _get_predictor_advanced(self):
        if self._predictor_advanced is not None:
            return self._predictor_advanced

        try:
            module_path = Path(self.advanced_module_path)
            if not module_path.is_absolute():
                module_path = Path(__file__).resolve().parents[2] / module_path
            if not module_path.exists():
                return None

            spec = importlib.util.spec_from_file_location("advanced_curtailment_module", str(module_path))
            if spec is None or spec.loader is None:
                return None
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            predictor_cls = getattr(mod, "AdvancedCurtailmentPredictor", None)
            if predictor_cls is None:
                return None
            self._predictor_advanced = predictor_cls(self.advanced_model_path)
            return self._predictor_advanced
        except Exception:
            return None

    def _build_features(self, usina_id: str, horizonte_horas: int):
        usina = self.repo.get_usina(usina_id)
        if not usina:
            return None, None

        now = datetime.now(timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
        fim = now + timedelta(hours=horizonte_horas)

        clima_future = self.repo.get_clima_horario(usina_id, now, fim, is_forecast=True)
        if not clima_future:
            clima_future = self.repo.get_clima_horario(
                usina_id,
                datetime(2000, 1, 1),
                datetime(2100, 1, 1),
                is_forecast=True,
            )[:horizonte_horas]

        try:
            from app.ml.features import build_inference_frame

            feat_df = build_inference_frame(
                usina=usina,
                clima_future=clima_future,
                geracao_recent=self.repo.get_geracao_horaria(usina_id, now - timedelta(hours=48), now),
                constrained_recent=self.repo.get_constrained_off(usina_id, now - timedelta(hours=48), now),
                pld_recent=self.repo.get_pld(usina.get("submercado", "NE"), now - timedelta(hours=48), now),
                disponibilidade_recent=self.repo.get_disponibilidade_usina(usina_id, now - timedelta(hours=48), now),
                dessem_recent=self.repo.get_despacho_dessem(usina_id, now - timedelta(hours=48), now),
                garantia_fisica_recent=self.repo.get_garantia_fisica(usina_id, now - timedelta(hours=48), now),
            )
            return usina, feat_df
        except Exception:
            return usina, None

    def _heuristic(self, usina_id: str, horizonte_horas: int, feat_df):
        records = feat_df.to_dict(orient="records") if feat_df is not None else []
        previsoes = [
            {
                "timestamp": item["timestamp"].isoformat() if hasattr(item.get("timestamp"), "isoformat") else str(item.get("timestamp")),
                "prob_corte": 0.5,
                "magnitude_estimada_mwh": round(float(item.get("mm_corte_3h", 0.0) or 0.0), 4),
            }
            for item in records
        ]
        if not previsoes:
            now = datetime.now(timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
            previsoes = [
                {
                    "timestamp": (now + timedelta(hours=i)).isoformat(),
                    "prob_corte": 0.5,
                    "magnitude_estimada_mwh": 0.0,
                }
                for i in range(horizonte_horas)
            ]
        return {
            "usina_id": usina_id,
            "horizonte_horas": horizonte_horas,
            "previsoes": previsoes,
            "modelo": "heuristico_fallback",
        }

    def prever_risco(self, usina_id: str, horizonte_horas: int = 48) -> dict:
        usina, feat_df = self._build_features(usina_id, horizonte_horas)
        if usina is None:
            return {"usina_id": usina_id, "horizonte_horas": horizonte_horas, "previsoes": [], "modelo": "sem_usina"}
        if feat_df is None:
            return self._heuristic(usina_id, horizonte_horas, feat_df=None)

        advanced = self._get_predictor_advanced() if self.model_mode in {"auto", "advanced"} else None
        if advanced is not None:
            try:
                return {
                    "usina_id": usina_id,
                    "horizonte_horas": horizonte_horas,
                    "previsoes": advanced.predict(feat_df),
                    "modelo": "ml_advanced",
                }
            except Exception:
                if self.model_mode == "advanced":
                    return self._heuristic(usina_id, horizonte_horas, feat_df)

        base = self._get_predictor_base() if self.model_mode in {"auto", "base"} else None
        if base is not None:
            try:
                return {
                    "usina_id": usina_id,
                    "horizonte_horas": horizonte_horas,
                    "previsoes": base.predict(feat_df),
                    "modelo": "ml_base_random_forest",
                }
            except Exception:
                return self._heuristic(usina_id, horizonte_horas, feat_df)

        return self._heuristic(usina_id, horizonte_horas, feat_df)

    def prever_risco_detalhado(self, usina_id: str, horizonte_horas: int = 48) -> dict:
        usina, feat_df = self._build_features(usina_id, horizonte_horas)
        if usina is None:
            return {
                "usina_id": usina_id,
                "horizonte_horas": horizonte_horas,
                "modelo": "sem_usina",
                "resumo": {"horizonte_horas": 0},
                "previsoes": [],
                "alertas": [],
            }

        pld_recent = self.repo.get_pld(usina.get("submercado", "NE"), datetime.now() - timedelta(hours=48), datetime.now())
        pld_medio = (
            sum(float(p.get("pld_reais_mwh", 0.0) or 0.0) for p in pld_recent) / len(pld_recent) if pld_recent else 200.0
        )

        advanced = self._get_predictor_advanced() if self.model_mode in {"auto", "advanced"} else None
        if advanced is not None:
            try:
                out = advanced.predict_detailed(feat_df, pld_medio_reais_mwh=float(pld_medio), usina_info=usina)
                out.update(
                    {
                        "usina_id": usina_id,
                        "horizonte_horas": horizonte_horas,
                        "modelo": "ml_advanced",
                        "tipo_dado": "previsao",
                    }
                )
                return out
            except Exception:
                if self.model_mode == "advanced":
                    pass

        base_out = self.prever_risco(usina_id, horizonte_horas)
        previsoes = base_out.get("previsoes", [])
        alertas = [p for p in previsoes if float(p.get("prob_corte", 0.0) or 0.0) >= 0.7]
        return {
            "usina_id": usina_id,
            "horizonte_horas": horizonte_horas,
            "modelo": base_out.get("modelo", "heuristico_fallback"),
            "tipo_dado": "previsao",
            "previsoes": previsoes,
            "alertas": alertas,
            "resumo": {
                "horizonte_horas": horizonte_horas,
                "total_alertas": len(alertas),
                "metodo": "fallback_detalhado_base",
            },
            "decomposicao_temporal": None,
            "knn_insights": {},
        }

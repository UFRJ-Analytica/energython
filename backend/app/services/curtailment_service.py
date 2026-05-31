from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.ml.features import build_inference_frame
from app.ml.predictor import CurtailmentPredictor


class CurtailmentService:
    def __init__(self, repo, model_path: str = "models_ml/curtailment_model.pkl"):
        self.repo = repo
        self.model_path = model_path
        self._predictor = None

    def _get_predictor(self) -> CurtailmentPredictor | None:
        if self._predictor is not None:
            return self._predictor
        try:
            self._predictor = CurtailmentPredictor(self.model_path)
            return self._predictor
        except FileNotFoundError:
            return None

    def prever_risco(self, usina_id: str, horizonte_horas: int = 48) -> dict:
        usina = self.repo.get_usina(usina_id)
        if not usina:
            return {"usina_id": usina_id, "horizonte_horas": horizonte_horas, "previsoes": []}

        now = datetime.now(timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
        fim = now + timedelta(hours=horizonte_horas)

        clima_future = self.repo.get_clima_horario(usina_id, now, fim, is_forecast=True)
        if not clima_future:
            # fallback para ambientes de desenvolvimento com janelas de dados históricas curtas
            clima_future = self.repo.get_clima_horario(
                usina_id,
                datetime(2000, 1, 1),
                datetime(2100, 1, 1),
                is_forecast=True,
            )[:horizonte_horas]
        geracao_recent = self.repo.get_geracao_horaria(usina_id, now - timedelta(hours=48), now)
        constrained_recent = self.repo.get_constrained_off(usina_id, now - timedelta(hours=48), now)
        pld_recent = self.repo.get_pld(usina.get("submercado", "NE"), now - timedelta(hours=48), now)
        disponibilidade_recent = self.repo.get_disponibilidade_usina(usina_id, now - timedelta(hours=48), now)
        dessem_recent = self.repo.get_despacho_dessem(usina_id, now - timedelta(hours=48), now)
        garantia_fisica_recent = self.repo.get_garantia_fisica(usina_id, now - timedelta(hours=48), now)

        feat_df = build_inference_frame(
            usina=usina,
            clima_future=clima_future,
            geracao_recent=geracao_recent,
            constrained_recent=constrained_recent,
            pld_recent=pld_recent,
            disponibilidade_recent=disponibilidade_recent,
            dessem_recent=dessem_recent,
            garantia_fisica_recent=garantia_fisica_recent,
        )

        predictor = self._get_predictor()
        if predictor is None:
            previsoes = [
                {
                    "timestamp": item["timestamp"].isoformat() if hasattr(item.get("timestamp"), "isoformat") else str(item.get("timestamp")),
                    "prob_corte": 0.5,
                    "magnitude_estimada_mwh": round(float(item.get("mm_corte_3h", 0.0) or 0.0), 4),
                }
                for item in feat_df.to_dict(orient="records")
            ]
            return {
                "usina_id": usina_id,
                "horizonte_horas": horizonte_horas,
                "previsoes": previsoes,
                "modelo": "heuristico_fallback",
            }

        previsoes = predictor.predict(feat_df)
        return {
            "usina_id": usina_id,
            "horizonte_horas": horizonte_horas,
            "previsoes": previsoes,
            "modelo": "ml_base_random_forest",
        }

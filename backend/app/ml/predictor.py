from __future__ import annotations

import pickle
from pathlib import Path

import pandas as pd


class CurtailmentPredictor:
    def __init__(self, model_path: str):
        self.model_path = Path(model_path)
        self.bundle = self._load_bundle()

    def _load_bundle(self) -> dict:
        if not self.model_path.exists():
            raise FileNotFoundError(f"Modelo não encontrado: {self.model_path}")
        with self.model_path.open("rb") as f:
            return pickle.load(f)

    @property
    def feature_cols(self) -> list[str]:
        return list(self.bundle.get("feature_cols", []))

    @property
    def cat_cols(self) -> list[str]:
        return list(self.bundle.get("cat_cols", ["fonte", "submercado"]))

    def _prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        X = df.copy()
        for c in self.feature_cols:
            if c not in X.columns:
                X[c] = 0.0
        for c in self.cat_cols:
            if c in X.columns:
                X[c] = X[c].astype(str)
        return X[self.feature_cols]

    def predict(self, features_df: pd.DataFrame) -> list[dict]:
        if features_df.empty:
            return []

        X = self._prepare(features_df)
        clf = self.bundle["classifier"]
        reg = self.bundle["regressor"]

        prob_arr = clf.predict_proba(X)
        if getattr(prob_arr, "shape", (0, 0))[1] == 1:
            cls = int(getattr(clf, "classes_", [0])[0])
            prob = [1.0 if cls == 1 else 0.0] * len(X)
        else:
            prob = prob_arr[:, 1].tolist()
        mag = reg.predict(X)
        mag = [max(0.0, float(v)) for v in mag]

        out = []
        for ts, p, m in zip(features_df["timestamp"].tolist(), prob, mag):
            out.append(
                {
                    "timestamp": pd.to_datetime(ts).isoformat(),
                    "prob_corte": round(float(p), 4),
                    "magnitude_estimada_mwh": round(float(m), 4),
                }
            )
        return out

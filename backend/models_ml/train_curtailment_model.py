from __future__ import annotations

import argparse
import json
import pickle
import sys
from pathlib import Path

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier, DummyRegressor
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.ml.features import build_training_frame


FEATURE_COLS = [
    "fator_capacidade",
    "geracao_mwh",
    "irradiancia_wm2",
    "vento_ms",
    "temperatura_c",
    "pld_reais_mwh",
    "mm_corte_3h",
    "mm_corte_24h",
    "hora",
    "dia_semana",
    "is_weekend",
    "fonte",
    "submercado",
]
CAT_COLS = ["fonte", "submercado"]


def train(data_dir: Path, output_model: Path, output_metrics: Path, threshold_mwh: float) -> dict:
    usinas = pd.read_csv(data_dir / "usinas.csv")
    constrained = pd.read_csv(data_dir / "constrained_off.csv")
    geracao = pd.read_csv(data_dir / "geracao_horaria.csv")
    clima = pd.read_csv(data_dir / "clima_horario.csv")
    pld = pd.read_csv(data_dir / "pld_horario.csv")

    frame = build_training_frame(usinas, constrained, geracao, clima, pld, threshold_mwh=threshold_mwh)
    frame = frame.sort_values("timestamp").reset_index(drop=True)

    X = frame[FEATURE_COLS]
    y_cls = frame["houve_corte"].astype(int)
    y_reg = frame["energia_restringida_mwh"].astype(float)

    split_idx = max(1, int(len(frame) * 0.8))
    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_cls_train, y_cls_test = y_cls.iloc[:split_idx], y_cls.iloc[split_idx:]
    y_reg_train, y_reg_test = y_reg.iloc[:split_idx], y_reg.iloc[split_idx:]

    pre = ColumnTransformer(
        transformers=[("cat", OneHotEncoder(handle_unknown="ignore"), CAT_COLS)],
        remainder="passthrough",
    )

    if len(y_cls_train.unique()) < 2:
        clf_model = DummyClassifier(strategy="constant", constant=int(y_cls_train.iloc[0]))
    else:
        clf_model = RandomForestClassifier(n_estimators=150, random_state=42, min_samples_leaf=1)

    if len(y_reg_train) < 2:
        reg_model = DummyRegressor(strategy="constant", constant=float(y_reg_train.iloc[0]))
    else:
        reg_model = RandomForestRegressor(n_estimators=200, random_state=42, min_samples_leaf=1)

    clf = Pipeline(steps=[("pre", pre), ("model", clf_model)])
    reg = Pipeline(steps=[("pre", pre), ("model", reg_model)])

    clf.fit(X_train, y_cls_train)
    reg.fit(X_train, y_reg_train)

    auc = None
    if len(X_test) > 0 and len(set(y_cls_test.tolist())) > 1:
        probs = clf.predict_proba(X_test)[:, 1]
        auc = float(roc_auc_score(y_cls_test, probs))

    mae = None
    if len(X_test) > 0:
        pred_reg = reg.predict(X_test)
        mae = float(mean_absolute_error(y_reg_test, pred_reg))

    metrics = {
        "rows": int(len(frame)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "auc": auc,
        "mae": mae,
        "threshold_mwh": threshold_mwh,
    }

    bundle = {
        "classifier": clf,
        "regressor": reg,
        "feature_cols": FEATURE_COLS,
        "cat_cols": CAT_COLS,
        "metrics": metrics,
    }

    output_model.parent.mkdir(parents=True, exist_ok=True)
    with output_model.open("wb") as f:
        pickle.dump(bundle, f)

    output_metrics.parent.mkdir(parents=True, exist_ok=True)
    with output_metrics.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    return metrics


def main() -> None:
    parser = argparse.ArgumentParser(description="Treina modelo base de curtailment (Elo 1)")
    parser.add_argument("--data-dir", default="data/samples")
    parser.add_argument("--output-model", default="models_ml/curtailment_model.pkl")
    parser.add_argument("--output-metrics", default="models_ml/curtailment_metrics.json")
    parser.add_argument("--threshold-mwh", type=float, default=1.0)
    args = parser.parse_args()

    metrics = train(
        data_dir=Path(args.data_dir),
        output_model=Path(args.output_model),
        output_metrics=Path(args.output_metrics),
        threshold_mwh=args.threshold_mwh,
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

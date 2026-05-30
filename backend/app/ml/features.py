from __future__ import annotations

from datetime import datetime

import pandas as pd


def _ensure_datetime(df: pd.DataFrame, col: str = "timestamp") -> pd.DataFrame:
    out = df.copy()
    if col in out.columns:
        out[col] = pd.to_datetime(out[col], utc=False)
    return out


def build_training_frame(
    usinas_df: pd.DataFrame,
    constrained_df: pd.DataFrame,
    geracao_df: pd.DataFrame,
    clima_df: pd.DataFrame,
    pld_df: pd.DataFrame,
    threshold_mwh: float = 1.0,
) -> pd.DataFrame:
    usinas = usinas_df.copy()
    co = _ensure_datetime(constrained_df)
    ger = _ensure_datetime(geracao_df)
    clima = _ensure_datetime(clima_df)
    pld = _ensure_datetime(pld_df)

    base = (
        co.merge(usinas[["usina_id", "fonte", "submercado"]], on="usina_id", how="left", suffixes=("", "_usina"))
        .merge(ger[["usina_id", "timestamp", "fator_capacidade", "geracao_mwh"]], on=["usina_id", "timestamp"], how="left")
        .merge(clima[["usina_id", "timestamp", "irradiancia_wm2", "vento_ms", "temperatura_c"]], on=["usina_id", "timestamp"], how="left")
        .merge(pld[["timestamp", "submercado", "pld_reais_mwh"]], on=["timestamp", "submercado"], how="left")
    )

    base["energia_restringida_mwh"] = base["energia_restringida_mwh"].fillna(0.0)
    base["houve_corte"] = (base["energia_restringida_mwh"] > threshold_mwh).astype(int)

    ts = pd.to_datetime(base["timestamp"])
    base["hora"] = ts.dt.hour
    base["dia_semana"] = ts.dt.weekday
    base["is_weekend"] = (base["dia_semana"] >= 5).astype(int)

    base = base.sort_values(["usina_id", "timestamp"]).reset_index(drop=True)
    base["mm_corte_3h"] = (
        base.groupby("usina_id")["energia_restringida_mwh"].transform(lambda s: s.shift(1).rolling(3, min_periods=1).mean())
    )
    base["mm_corte_24h"] = (
        base.groupby("usina_id")["energia_restringida_mwh"].transform(lambda s: s.shift(1).rolling(24, min_periods=1).mean())
    )

    numeric_cols = [
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
    ]
    for col in numeric_cols:
        if col not in base.columns:
            base[col] = 0.0
        base[col] = pd.to_numeric(base[col], errors="coerce")
        base[col] = base[col].fillna(base[col].median() if not base[col].dropna().empty else 0.0)

    for col in ["fonte", "submercado"]:
        if col not in base.columns:
            base[col] = "desconhecido"
        base[col] = base[col].fillna("desconhecido").astype(str)

    return base


def build_inference_frame(
    usina: dict,
    clima_future: list[dict],
    geracao_recent: list[dict],
    constrained_recent: list[dict],
    pld_recent: list[dict],
    disponibilidade_recent: list[dict] | None = None,
    dessem_recent: list[dict] | None = None,
    garantia_fisica_recent: list[dict] | None = None,
) -> pd.DataFrame:
    df = pd.DataFrame(clima_future)
    if df.empty:
        return df

    df = _ensure_datetime(df)
    df["usina_id"] = usina["usina_id"]
    df["fonte"] = usina.get("fonte", "desconhecido")
    df["submercado"] = usina.get("submercado", "NE")

    # últimas referências como fallback para horizonte futuro
    fator_cap = None
    geracao_mwh = None
    if geracao_recent:
        last_g = sorted(geracao_recent, key=lambda x: x["timestamp"])[-1]
        fator_cap = last_g.get("fator_capacidade")
        geracao_mwh = last_g.get("geracao_mwh")

    last_mm3 = 0.0
    last_mm24 = 0.0
    if constrained_recent:
        hist = sorted(constrained_recent, key=lambda x: x["timestamp"])
        serie = pd.Series([float(x.get("energia_restringida_mwh", 0.0) or 0.0) for x in hist])
        last_mm3 = float(serie.tail(3).mean()) if not serie.empty else 0.0
        last_mm24 = float(serie.tail(24).mean()) if not serie.empty else 0.0

    # Fallbacks de novas features (preparação para dados reais)
    disponibilidade_recent = disponibilidade_recent or []
    dessem_recent = dessem_recent or []
    garantia_fisica_recent = garantia_fisica_recent or []

    def _last_or_default(items: list[dict], key: str, default: float = 0.0) -> float:
        if not items:
            return default
        ordered = sorted(items, key=lambda x: x.get("timestamp"))
        raw = ordered[-1].get(key, default)
        try:
            return float(raw or default)
        except Exception:
            return default

    disponibilidade_val = _last_or_default(disponibilidade_recent, "disponibilidade", 0.0)
    teifa_val = _last_or_default(disponibilidade_recent, "teifa", 0.0)
    teip_val = _last_or_default(disponibilidade_recent, "teip", 0.0)
    dessem_val = _last_or_default(dessem_recent, "geracao_programada_mwh", 0.0)
    gf_val = _last_or_default(garantia_fisica_recent, "garantia_fisica_mwh", 0.0)

    pld_map = {x["timestamp"]: x.get("pld_reais_mwh") for x in pld_recent}
    pld_default = None
    if pld_recent:
        vals = [float(x.get("pld_reais_mwh", 0.0) or 0.0) for x in pld_recent]
        pld_default = sum(vals) / len(vals)

    df["fator_capacidade"] = fator_cap if fator_cap is not None else 0.0
    df["geracao_mwh"] = geracao_mwh if geracao_mwh is not None else 0.0
    df["pld_reais_mwh"] = df["timestamp"].map(pld_map).fillna(pld_default if pld_default is not None else 0.0)
    df["mm_corte_3h"] = last_mm3
    df["mm_corte_24h"] = last_mm24

    # Novas colunas opcionais: já preparadas mesmo sem ingestão real no banco
    df["disponibilidade"] = disponibilidade_val
    df["teifa"] = teifa_val
    df["teip"] = teip_val
    df["geracao_programada_mwh"] = dessem_val
    df["garantia_fisica_mwh"] = gf_val
    df["flag_missing_disponibilidade"] = 0 if disponibilidade_recent else 1
    df["flag_missing_dessem"] = 0 if dessem_recent else 1
    df["flag_missing_garantia_fisica"] = 0 if garantia_fisica_recent else 1

    ts = pd.to_datetime(df["timestamp"])
    df["hora"] = ts.dt.hour
    df["dia_semana"] = ts.dt.weekday
    df["is_weekend"] = (df["dia_semana"] >= 5).astype(int)

    for col in ["irradiancia_wm2", "vento_ms", "temperatura_c"]:
        if col not in df.columns:
            df[col] = 0.0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df

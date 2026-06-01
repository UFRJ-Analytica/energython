import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

"""
Utilitário OFFLINE de extração para analytics/data-science.
Não é parte do runtime da API FastAPI.

Uso:
  DATABASE_URL=... python data_extraction.py
"""

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não definida. Configure no ambiente ou em backend/.env")

OUTPUT_DIR = Path(__file__).parent / "temp_cache"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("Conectando ao banco de dados...")
engine = create_engine(DATABASE_URL)


def process_and_save(df, filename):
    if df.empty:
        return
    df["timestamp"] = pd.to_datetime(df["timestamp_raw"], errors="coerce")
    df["geracao_mwh"] = pd.to_numeric(df["val_geracao"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["capacidade_mwh"] = pd.to_numeric(df["val_disponibilidade"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["energia_restringida_mwh"] = pd.to_numeric(
        df["val_geracaoreferenciafinal"].astype(str).str.replace(",", "."), errors="coerce"
    ).fillna(0)
    df = df.drop(columns=["timestamp_raw", "val_geracao", "val_disponibilidade", "val_geracaoreferenciafinal"])
    filepath = OUTPUT_DIR / filename
    df.to_csv(filepath, index=False)
    print(f"Salvo {filepath} ({os.path.getsize(filepath) / (1024 * 1024):.1f} MB)")


try:
    print("Extraindo usinas únicas (Eólicas e Solares)...")
    usinas_query = """
        SELECT DISTINCT id_ons AS usina_id, nom_usina AS nome, 'eolica' AS fonte,
               'NE' AS submercado, 50.0 AS potencia_mw
        FROM public.restricao_coff_eolica_usi
        WHERE id_ons IS NOT NULL
        UNION
        SELECT DISTINCT id_ons AS usina_id, nom_usina AS nome, 'solar' AS fonte,
               'NE' AS submercado, 50.0 AS potencia_mw
        FROM public.restricao_coff_fotovoltaica
        WHERE id_ons IS NOT NULL
    """
    usinas_df = pd.read_sql(usinas_query, engine)
    usinas_df.to_csv(OUTPUT_DIR / "usinas_cache.csv", index=False)
    usinas_list = tuple(usinas_df["usina_id"].tolist())

    print("Extraindo Eólica...")
    query_eolica = """
        SELECT id_ons AS usina_id, CAST(din_instante AS text) AS timestamp_raw,
               CAST(val_geracao AS text) AS val_geracao, CAST(val_disponibilidade AS text) AS val_disponibilidade,
               CAST(val_geracaoreferenciafinal AS text) AS val_geracaoreferenciafinal, cod_razaorestricao AS razao_restricao
        FROM public.restricao_coff_eolica_usi
        WHERE id_ons IS NOT NULL AND din_instante IS NOT NULL
    """
    df_eolica = pd.read_sql(query_eolica, engine)
    process_and_save(df_eolica, "flat_dados_eolica.csv")

    print("Extraindo Solar...")
    query_solar = """
        SELECT id_ons AS usina_id, CAST(din_instante AS text) AS timestamp_raw,
               CAST(val_geracao AS text) AS val_geracao, CAST(val_disponibilidade AS text) AS val_disponibilidade,
               CAST(val_geracaoreferenciafinal AS text) AS val_geracaoreferenciafinal, cod_razaorestricao AS razao_restricao
        FROM public.restricao_coff_fotovoltaica
        WHERE id_ons IS NOT NULL AND din_instante IS NOT NULL
    """
    df_solar = pd.read_sql(query_solar, engine)
    process_and_save(df_solar, "flat_dados_solar.csv")

    print("Extraindo CCEE...")
    query_ccee = """
        SELECT *
        FROM public.ccee_pld_horario_submercado
        WHERE mes_referencia >= to_char(current_date - interval '180 day', 'YYYYMM')
    """
    df_ccee = pd.read_sql(query_ccee, engine)
    df_ccee.to_csv(OUTPUT_DIR / "ccee_cache.csv", index=False)
    print("Salvo CCEE cache")

except Exception as e:
    print(f"Erro: {e}")

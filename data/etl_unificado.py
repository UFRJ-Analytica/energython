#!/usr/bin/env python3
"""
ETL UNIFICADO - CAMADA PRATA (SILVER)
PostgreSQL → Parquet particionado

Operações:
1. Remoção de NULLs em colunas-chave
2. Remoção de outliers (IQR)
3. Limpeza e normalização de strings
4. Particionamento por estado/ano/mes
5. Agregações (dia e mês)
6. H3 para dados geográficos

Uso:
  python etl_unificado.py
  python etl_unificado.py --limit 500000
  python etl_unificado.py --tables geracao_usina_2
"""

import os
import sys
import argparse
import logging
from datetime import datetime
import json

import pandas as pd
import psycopg2
import pyarrow as pa
import pyarrow.parquet as pq

try:
    import duckdb
except:
    pass

try:
    import h3
    H3_AVAILABLE = True
except:
    H3_AVAILABLE = False

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════



SILVER_DIR = os.path.join(BASE_LAKE, "silver")
AGG_DIR = os.path.join(BASE_LAKE, "agg")

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger("etl-prata")

# ══════════════════════════════════════════════════════════════
# DEFINIÇÃO DAS TABELAS
# ══════════════════════════════════════════════════════════════

TABLES = {
    "geracao_usina_2": {
        "time_col": "din_instante",
        "state_col": "id_estado",
        "key_cols": ["din_instante", "id_estado", "nom_usina"],
        "lower_cols": ["nom_estado", "nom_usina", "nom_subsistema", "nom_tipousina", "nom_tipocombustivel"],
        "outlier_cols": ["val_geracao"],
        "numeric_cols": ["val_geracao", "ceg"],
    },
    "disponibilidade_usina": {
        "time_col": "din_instante",
        "state_col": "id_estado",
        "key_cols": ["din_instante", "id_estado", "nom_usina"],
        "lower_cols": ["nom_estado", "nom_usina", "nom_subsistema", "nom_tipocombustivel"],
        "outlier_cols": ["val_potenciainstalada", "val_dispoperacional", "val_dispsincronizada"],
        "numeric_cols": ["val_potenciainstalada", "val_dispoperacional", "val_dispsincronizada"],
    },
    "fator_capacidade_2": {
        "time_col": "din_instante",
        "state_col": "id_estado",
        "key_cols": ["din_instante", "id_estado", "nom_pontoconexao"],
        "lower_cols": ["nom_estado", "nom_localizacao", "nom_tipousina", "nom_modalidadeoperacao"],
        "outlier_cols": ["val_geracaoprogramada", "val_geracaoverificada", "val_capacidadeinstalada"],
        "numeric_cols": ["val_geracaoprogramada", "val_geracaoverificada", "val_capacidadeinstalada", "val_latitudesecoletora", "val_longitudesecoletora"],
        "h3": {
            "lat_cols": ["val_latitudesecoletora", "val_latitudepontoconexao"],
            "lon_cols": ["val_longitudesecoletora", "val_longitudepontoconexao"],
            "res": [6, 7],
        },
    },
    "restricao_coff_eolica_detail": {
        "time_col": "din_instante",
        "state_col": "id_estado",
        "key_cols": ["din_instante", "id_estado", "nom_usina"],
        "lower_cols": ["nom_usina", "nom_conjuntousina", "nom_modalidadeoperacao"],
        "outlier_cols": ["val_ventoverificado", "val_geracaoestimada", "val_geracaoverificada"],
        "numeric_cols": ["val_ventoverificado", "val_geracaoestimada", "val_geracaoverificada"],
    },
    "ccee_pld_horario": {
        "time_col": None,
        "state_col": "submercado",
        "key_cols": ["submercado", "dia", "hora"],
        "lower_cols": ["submercado"],
        "outlier_cols": [],
        "numeric_cols": ["pld_hora"],
    },
}


# ══════════════════════════════════════════════════════════════
# FUNÇÕES AUXILIARES
# ══════════════════════════════════════════════════════════════

def pg_conn():
    return psycopg2.connect(
        host=PG_HOST, port=PG_PORT, dbname=PG_DATABASE,
        user=PG_USER, password=PG_PASSWORD
    )


def compute_iqr_bounds(conn, table, cols):
    """Calcula limites IQR para detecção de outliers."""
    bounds = {}
    cur = conn.cursor()
    for col in cols:
        try:
            q = f"""
            SELECT
                percentile_cont(0.25) WITHIN GROUP (ORDER BY "{col}") AS q1,
                percentile_cont(0.75) WITHIN GROUP (ORDER BY "{col}") AS q3,
                MIN("{col}") AS min_val,
                MAX("{col}") AS max_val,
                COUNT(*) AS total
            FROM public.{table}
            WHERE "{col}" IS NOT NULL
            """
            cur.execute(q)
            q1, q3, min_val, max_val, total = cur.fetchone()
            
            if q1 is None or q3 is None:
                bounds[col] = None
            else:
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                bounds[col] = {
                    "lower": lower,
                    "upper": upper,
                    "q1": q1,
                    "q3": q3,
                    "iqr": iqr,
                    "original_range": (min_val, max_val),
                    "total": total,
                }
                log.info(f"  {col}: IQR=[{q1:.2f}, {q3:.2f}], valid_range=[{lower:.2f}, {upper:.2f}], total={total}")
        except Exception as e:
            log.warning(f"  {col}: erro ao calcular IQR - {e}")
    cur.close()
    return bounds


def build_where_clause(cfg, bounds):
    """Monta cláusula WHERE com filtros de nulos e outliers."""
    clauses = []
    
    # Remove nulos em colunas-chave
    for c in cfg.get("key_cols", []):
        clauses.append(f'"{c}" IS NOT NULL')
    
    # Filtra outliers
    for col, b in (bounds or {}).items():
        if b is None:
            continue
        lower = b["lower"]
        upper = b["upper"]
        clauses.append(f'"{col}" BETWEEN {lower} AND {upper}')
    
    if clauses:
        return "WHERE " + " AND ".join(clauses)
    return ""


def normalize_df(df, cfg):
    """Normaliza strings: trim + lower."""
    for c in cfg.get("lower_cols", []):
        if c in df.columns:
            df[c] = df[c].astype("string").str.strip().str.lower()
    return df


def add_time_partitions(df, time_col):
    """Adiciona colunas ano, mes, dia para particionamento."""
    if time_col and time_col in df.columns:
        dt = pd.to_datetime(df[time_col], errors="coerce")
        df["ano"] = dt.dt.year
        df["mes"] = dt.dt.month
        df["dia"] = dt.dt.day
    return df


def add_h3_columns(df, cfg):
    """Adiciona índices H3 (Uber) para dados geográficos."""
    if not H3_AVAILABLE:
        return df
    
    h3_cfg = cfg.get("h3")
    if not h3_cfg:
        return df
    
    lat_cols = h3_cfg.get("lat_cols", [])
    lon_cols = h3_cfg.get("lon_cols", [])
    
    if not lat_cols or not lon_cols:
        return df
    
    # Tenta primeir coluna, fallback para segunda
    lat_col = None
    lon_col = None
    
    for lc in lat_cols:
        if lc in df.columns:
            lat_col = lc
            break
    
    for lc in lon_cols:
        if lc in df.columns:
            lon_col = lc
            break
    
    if lat_col is None or lon_col is None:
        return df
    
    lat = df[lat_col]
    lon = df[lon_col]
    
    for res in h3_cfg.get("res", [6, 7]):
        h3_vals = []
        for la, lo in zip(lat, lon):
            try:
                if la is not None and lo is not None and pd.notna(la) and pd.notna(lo):
                    h3_id = h3.latlng_to_cell(la, lo, res)
                    h3_vals.append(h3_id)
                else:
                    h3_vals.append(None)
            except:
                h3_vals.append(None)
        df[f"h3_res{res}"] = h3_vals
    
    return df


def write_parquet(df, out_dir, partition_cols):
    """Escreve DataFrame como Parquet particionado."""
    os.makedirs(out_dir, exist_ok=True)
    
    # Remove colunas de partição do índice se necessário
    table = pa.Table.from_pandas(df, preserve_index=False)
    
    pq.write_to_dataset(
        table,
        root_path=out_dir,
        partition_cols=partition_cols,
        existing_data_behavior="overwrite_or_ignore",
        compression="snappy",
    )


def extract_and_process_table(table_name, limit=None, chunksize=200000):
    """Extrai, limpa e escreve uma tabela."""
    if table_name not in TABLES:
        log.warning(f"Tabela {table_name} não configurada")
        return None
    
    cfg = TABLES[table_name]
    out_dir = os.path.join(SILVER_DIR, table_name)
    
    log.info(f"\n{'='*80}")
    log.info(f"PROCESSANDO: {table_name}")
    log.info(f"{'='*80}")
    
    stats = {
        "table": table_name,
        "total_input": 0,
        "total_output": 0,
        "removed_nulls": 0,
        "removed_outliers": 0,
        "chunks": 0,
    }
    
    with pg_conn() as conn:
        # Calcular limites IQR
        log.info("Calculando limites IQR...")
        bounds = compute_iqr_bounds(conn, table_name, cfg.get("outlier_cols", []))
        
        where_sql = build_where_clause(cfg, bounds)
        limit_sql = f"LIMIT {int(limit)}" if limit else ""
        
        sql = f"SELECT * FROM public.{table_name} {where_sql} {limit_sql}"
        
        log.info(f"SQL: {sql[:150]}...")
        log.info(f"Lendo dados em chunks de {chunksize}...")
        
        # Processa em chunks
        for i, chunk in enumerate(pd.read_sql(sql, conn, chunksize=chunksize)):
            stats["chunks"] += 1
            initial_rows = len(chunk)
            stats["total_input"] += initial_rows
            
            # Limpeza
            chunk = normalize_df(chunk, cfg)
            chunk = add_time_partitions(chunk, cfg.get("time_col"))
            chunk = add_h3_columns(chunk, cfg)
            
            stats["total_output"] += len(chunk)
            
            # Determina colunas de partição
            part_cols = []
            if cfg.get("state_col") and cfg.get("state_col") in chunk.columns:
                part_cols.append(cfg.get("state_col"))
            for c in ["ano", "mes"]:
                if c in chunk.columns:
                    part_cols.append(c)
            
            # Escreve
            write_parquet(chunk, out_dir, part_cols)
            
            log.info(f"  Chunk {i+1}: {initial_rows:,} → {len(chunk):,} linhas (removidas: {initial_rows - len(chunk):,})")
    
    log.info(f"\n✓ {table_name} concluído")
    log.info(f"  Saída: {out_dir}")
    log.info(f"  Total input:  {stats['total_input']:,}")
    log.info(f"  Total output: {stats['total_output']:,}")
    log.info(f"  Removidas: {stats['total_input'] - stats['total_output']:,}")
    
    return stats


def create_aggregations():
    """Cria tabelas agregadas."""
    log.info(f"\n{'='*80}")
    log.info("GERANDO AGREGAÇÕES")
    log.info(f"{'='*80}")
    
    try:
        import duckdb
    except:
        log.warning("DuckDB não instalado. Pulando agregações.")
        return
    
    con = duckdb.connect()
    aggs_created = []
    
    # Agg 1: Geração por estado e dia
    src = os.path.join(SILVER_DIR, "geracao_usina_2")
    if os.path.isdir(src):
        out = os.path.join(AGG_DIR, "agg_geracao_estado_dia")
        os.makedirs(out, exist_ok=True)
        
        q = f"""
        SELECT 
            id_estado, 
            nom_estado, 
            DATE(din_instante) AS data,
            COUNT(*) AS registros,
            SUM(val_geracao) AS geracao_total_mw,
            AVG(val_geracao) AS geracao_media_mw,
            MIN(val_geracao) AS geracao_min_mw,
            MAX(val_geracao) AS geracao_max_mw
        FROM parquet_scan('{src}/**/*.parquet')
        WHERE id_estado IS NOT NULL AND din_instante IS NOT NULL
        GROUP BY 1,2,3
        ORDER BY 1,3
        """
        
        con.execute(f"COPY ({q}) TO '{out}' (FORMAT PARQUET, PARTITION_BY (id_estado))")
        aggs_created.append(f"agg_geracao_estado_dia")
        log.info(f"✓ {out}")
    
    # Agg 2: Fator de capacidade por estado e mês
    src = os.path.join(SILVER_DIR, "fator_capacidade_2")
    if os.path.isdir(src):
        out = os.path.join(AGG_DIR, "agg_fator_capacidade_estado_mes")
        os.makedirs(out, exist_ok=True)
        
        q = f"""
        SELECT 
            id_estado,
            nom_estado,
            DATE_TRUNC('month', din_instante)::DATE AS mes,
            COUNT(*) AS registros,
            AVG(val_fatorcapacidade) AS fator_capacidade_media,
            AVG(val_geracaoverificada) AS geracao_verificada_media_mw,
            AVG(val_capacidadeinstalada) AS capacidade_instalada_media_mw
        FROM parquet_scan('{src}/**/*.parquet')
        WHERE id_estado IS NOT NULL AND din_instante IS NOT NULL
        GROUP BY 1,2,3
        ORDER BY 1,3
        """
        
        con.execute(f"COPY ({q}) TO '{out}' (FORMAT PARQUET, PARTITION_BY (id_estado))")
        aggs_created.append(f"agg_fator_capacidade_estado_mes")
        log.info(f"✓ {out}")
    
    log.info(f"\n✓ Agregações criadas: {', '.join(aggs_created)}")


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="ETL Unificado - Camada Prata")
    parser.add_argument("--tables", default=",".join(TABLES.keys()), help="Tabelas a processar")
    parser.add_argument("--limit", type=int, default=None, help="Limite de linhas por tabela")
    parser.add_argument("--skip-agg", action="store_true", help="Pula agregações")
    
    args = parser.parse_args()
    
    tables = [t.strip() for t in args.tables.split(",") if t.strip()]
    all_stats = []
    
    log.info(f"\n{'='*80}")
    log.info(f"ETL UNIFICADO - CAMADA PRATA")
    log.info(f"Início: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"Base: {BASE_LAKE}")
    log.info(f"{'='*80}\n")
    
    for t in tables:
        if t not in TABLES:
            log.warning(f"Tabela '{t}' não configurada")
            continue
        
        stats = extract_and_process_table(t, limit=args.limit)
        if stats:
            all_stats.append(stats)
    
    if not args.skip_agg:
        create_aggregations()
    
    # Resumo final
    log.info(f"\n{'='*80}")
    log.info("RESUMO FINAL")
    log.info(f"{'='*80}")
    for s in all_stats:
        log.info(f"{s['table']}: {s['total_input']:,} → {s['total_output']:,} linhas")
    log.info(f"\nFim: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()

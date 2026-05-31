from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

NE_UFS = ["MA", "PI", "CE", "RN", "PB", "PE", "AL", "SE", "BA"]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _sql_in_list(values: list[str]) -> str:
    escaped = [v.replace("'", "''") for v in values]
    return "(" + ",".join(f"'{v}'" for v in escaped) + ")"


def build_dataset(database_url: str, output_dir: Path, lookback_days: int, max_usinas: int) -> dict:
    engine = create_engine(database_url)
    ufs_sql = _sql_in_list(NE_UFS)

    with engine.connect() as conn:
        usinas = pd.read_sql(
            text(
                f"""
                WITH ranked AS (
                    SELECT
                        id_ons AS usina_id,
                        COALESCE(nom_usina_conjunto, id_ons) AS nome,
                        COALESCE(nom_tipousina, 'desconhecida') AS fonte,
                        'NE'::text AS submercado,
                        COALESCE(val_capacidadeinstalada, 0)::double precision AS potencia_mw,
                        ROW_NUMBER() OVER (PARTITION BY id_ons ORDER BY din_instante DESC) AS rn
                    FROM public.fator_capacidade_2
                    WHERE UPPER(COALESCE(id_estado, '')) IN {ufs_sql}
                      AND id_ons IS NOT NULL
                )
                SELECT usina_id, nome, fonte, submercado, potencia_mw
                FROM ranked
                WHERE rn = 1
                ORDER BY usina_id
                LIMIT :max_usinas
                """
            ),
            conn,
            params={"max_usinas": max_usinas},
        )

        if usinas.empty:
            raise RuntimeError("Nenhuma usina NE encontrada para treino")

        usina_ids_sql = _sql_in_list(usinas["usina_id"].astype(str).tolist())

        geracao = pd.read_sql(
            text(
                f"""
                SELECT
                    id_ons AS usina_id,
                    din_instante AS timestamp,
                    COALESCE(val_geracaoverificada, 0)::double precision AS geracao_mwh,
                    COALESCE(val_fatorcapacidade, 0)::double precision AS fator_capacidade
                FROM public.fator_capacidade_2
                WHERE id_ons IN {usina_ids_sql}
                  AND din_instante >= (NOW() - (:lookback_days || ' days')::interval)
                  AND UPPER(COALESCE(id_estado, '')) IN {ufs_sql}
                ORDER BY id_ons, din_instante
                """
            ),
            conn,
            params={"lookback_days": lookback_days},
        )

        constrained = pd.read_sql(
            text(
                f"""
                SELECT
                    id_ons AS usina_id,
                    din_instante AS timestamp,
                    COALESCE(nom_tipousina, 'desconhecida') AS fonte,
                    COALESCE(val_geracaoverificada, 0)::double precision AS geracao_verificada_mwh,
                    COALESCE(val_geracaoprogramada, 0)::double precision AS geracao_referencia_mwh,
                    GREATEST(
                        COALESCE(val_geracaoprogramada, 0) - COALESCE(val_geracaoverificada, 0),
                        0
                    )::double precision AS energia_restringida_mwh,
                    NULL::text AS razao_restricao,
                    'NE'::text AS submercado
                FROM public.fator_capacidade_2
                WHERE id_ons IN {usina_ids_sql}
                  AND din_instante >= (NOW() - (:lookback_days || ' days')::interval)
                  AND UPPER(COALESCE(id_estado, '')) IN {ufs_sql}
                ORDER BY id_ons, din_instante
                """
            ),
            conn,
            params={"lookback_days": lookback_days},
        )

        clima = pd.read_sql(
            text(
                f"""
                SELECT
                    id_ons AS usina_id,
                    din_instante AS timestamp,
                    NULL::double precision AS irradiancia_wm2,
                    COALESCE(val_ventoverificado, 0)::double precision AS vento_ms,
                    NULL::double precision AS temperatura_c
                FROM public.restricao_coff_eolica_detail
                WHERE id_ons IN {usina_ids_sql}
                  AND din_instante >= (NOW() - (:lookback_days || ' days')::interval)
                  AND UPPER(COALESCE(id_estado, '')) IN {ufs_sql}
                ORDER BY id_ons, din_instante
                """
            ),
            conn,
            params={"lookback_days": lookback_days},
        )

        pld = pd.read_sql(
            text(
                f"""
                WITH years AS (
                    SELECT DISTINCT EXTRACT(YEAR FROM din_instante)::int AS ano
                    FROM public.fator_capacidade_2
                    WHERE id_ons IN {usina_ids_sql}
                      AND din_instante >= (NOW() - (:lookback_days || ' days')::interval)
                      AND UPPER(COALESCE(id_estado, '')) IN {ufs_sql}
                ),
                pld_map AS (
                    SELECT y.ano, COALESCE(p.pldx_anual, 0)::double precision AS pld_reais_mwh
                    FROM years y
                    LEFT JOIN public.ccee_pldx_valor_anual p ON p.ano = y.ano
                )
                SELECT DISTINCT
                    g.din_instante AS timestamp,
                    'NE'::text AS submercado,
                    COALESCE(pm.pld_reais_mwh, 0)::double precision AS pld_reais_mwh
                FROM public.fator_capacidade_2 g
                LEFT JOIN pld_map pm ON pm.ano = EXTRACT(YEAR FROM g.din_instante)::int
                WHERE g.id_ons IN {usina_ids_sql}
                  AND g.din_instante >= (NOW() - (:lookback_days || ' days')::interval)
                  AND UPPER(COALESCE(g.id_estado, '')) IN {ufs_sql}
                ORDER BY g.din_instante
                """
            ),
            conn,
            params={"lookback_days": lookback_days},
        )

    _ensure_dir(output_dir)
    usinas.to_csv(output_dir / "usinas.csv", index=False)
    constrained.to_csv(output_dir / "constrained_off.csv", index=False)
    geracao.to_csv(output_dir / "geracao_horaria.csv", index=False)
    clima.to_csv(output_dir / "clima_horario.csv", index=False)
    pld.to_csv(output_dir / "pld_horario.csv", index=False)

    return {
        "usinas": int(len(usinas)),
        "constrained_rows": int(len(constrained)),
        "geracao_rows": int(len(geracao)),
        "clima_rows": int(len(clima)),
        "pld_rows": int(len(pld)),
        "output_dir": str(output_dir),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Monta dataset de treino a partir do Postgres real")
    parser.add_argument("--database-url", required=True)
    parser.add_argument("--output-dir", default="data/training_v0")
    parser.add_argument("--lookback-days", type=int, default=365)
    parser.add_argument("--max-usinas", type=int, default=120)
    args = parser.parse_args()

    stats = build_dataset(
        database_url=args.database_url,
        output_dir=Path(args.output_dir),
        lookback_days=args.lookback_days,
        max_usinas=args.max_usinas,
    )
    print(stats)


if __name__ == "__main__":
    main()

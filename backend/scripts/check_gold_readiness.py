from __future__ import annotations

import json
from dataclasses import dataclass

from sqlalchemy import create_engine, inspect, text

from app.config import get_settings


@dataclass
class Requirement:
    table: str
    required_columns: list[str]
    critical: bool


REQUIREMENTS = [
    Requirement("gold.usinas", ["usina_id", "fonte", "submercado", "potencia_mw"], True),
    Requirement("gold.constrained_off", ["usina_id", "timestamp", "energia_restringida_mwh", "razao_restricao", "submercado"], True),
    Requirement("gold.geracao_horaria", ["usina_id", "timestamp", "geracao_mwh", "fator_capacidade"], True),
    Requirement("gold.clima_horario", ["usina_id", "timestamp", "irradiancia_wm2", "vento_ms", "temperatura_c", "is_forecast"], True),
    Requirement("gold.pld_horario", ["timestamp", "submercado", "pld_reais_mwh"], True),
    # Preparação para dados futuros
    Requirement("gold.disponibilidade_usina", ["usina_id", "timestamp", "disponibilidade", "teifa", "teip"], False),
    Requirement("gold.despacho_dessem", ["usina_id", "timestamp", "geracao_programada_mwh"], False),
    Requirement("gold.garantia_fisica_horaria", ["usina_id", "timestamp", "garantia_fisica_mwh"], False),
]


def split_schema_table(name: str) -> tuple[str, str]:
    parts = name.split(".", 1)
    if len(parts) == 1:
        return "public", parts[0]
    return parts[0], parts[1]


def main() -> int:
    settings = get_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    insp = inspect(engine)

    report = {
        "critical_ok": True,
        "tables": [],
    }

    with engine.connect() as conn:
        for req in REQUIREMENTS:
            schema, table = split_schema_table(req.table)
            exists = insp.has_table(table, schema=schema)
            cols = {c["name"] for c in insp.get_columns(table, schema=schema)} if exists else set()
            missing_cols = [c for c in req.required_columns if c not in cols]

            row_count = None
            if exists:
                try:
                    row_count = conn.execute(text(f"SELECT COUNT(*) FROM {schema}.{table}")) .scalar_one()
                except Exception:
                    row_count = None

            status = "ok" if exists and not missing_cols else "missing"
            if req.critical and status != "ok":
                report["critical_ok"] = False

            report["tables"].append(
                {
                    "table": req.table,
                    "critical": req.critical,
                    "exists": exists,
                    "missing_columns": missing_cols,
                    "row_count": row_count,
                    "status": status,
                }
            )

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["critical_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "marimo>=0.10.0",
#   "pandas>=2.2.0",
#   "sqlalchemy>=2.0.0",
#   "psycopg[binary]>=3.2.0",
#   "python-dotenv>=1.0.0",
# ]
# ///

"""
CurtailIQ Data Landscape & Product Readiness EDA

Como rodar na raiz do projeto:
    uvx marimo edit curtailiq_eda_master.py

Ou, se preferir instalar localmente:
    uv add marimo pandas sqlalchemy "psycopg[binary]" python-dotenv
    uv run marimo edit curtailiq_eda_master.py

A EDA lê DATABASE_URL do ambiente, de .env na raiz, ou de backend/.env.
Não imprime senha; a URL é mascarada na interface.
"""

import marimo

__generated_with = "0.23.9"
app = marimo.App(width="full")


@app.cell
def _():
    import os
    import re
    import math
    import unicodedata
    from pathlib import Path
    from datetime import datetime

    import marimo as mo
    import pandas as pd

    try:
        from dotenv import load_dotenv
    except Exception:  # pragma: no cover - ambiente sem python-dotenv
        load_dotenv = None

    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.exc import SQLAlchemyError
    except Exception:  # pragma: no cover - ambiente sem sqlalchemy/psycopg
        create_engine = None
        text = None
        SQLAlchemyError = Exception

    ROOT_DIR = Path(__file__).resolve().parent
    BACKEND_ENV = ROOT_DIR / "backend" / ".env"
    ROOT_ENV = ROOT_DIR / ".env"
    OUTPUT_DIR = ROOT_DIR / "eda_outputs"

    if load_dotenv is not None:
        if ROOT_ENV.exists():
            load_dotenv(ROOT_ENV, override=False)
        if BACKEND_ENV.exists():
            load_dotenv(BACKEND_ENV, override=False)

    pd.set_option("display.max_columns", 200)
    pd.set_option("display.width", 220)
    return (
        BACKEND_ENV,
        OUTPUT_DIR,
        SQLAlchemyError,
        create_engine,
        datetime,
        math,
        mo,
        os,
        pd,
        re,
        text,
        unicodedata,
    )


@app.cell
def _(mo):
    mo.md("""
    # CurtailIQ — EDA de Maturidade dos Dados e Prontidão do Produto

    Esta EDA foi desenhada para responder, com visão de cientista de dados sênior:

    1. **O que existe no banco?** Schemas, tabelas, colunas, volumes e cobertura temporal.
    2. **Como os dados se conectam?** Possíveis chaves, joins, órfãos e lacunas de relacionamento.
    3. **Onde está o curtailment/restrição?** Eventos, razões, energia restringida, granularidade e confiabilidade.
    4. **O banco sustenta a solução atual?** Perda financeira, elegibilidade regulatória, forecast, BESS, dossiê e seleção de usinas.
    5. **Quais são os riscos?** Nulos, duplicatas, gaps temporais, tipos incorretos, ausência de PLD/razão/cadastro e dados sem ligação.
    6. **Qual deveria ser a camada gold?** Contratos de dados recomendados para produção.

    A proposta não é fazer apenas gráficos. É gerar uma **avaliação de prontidão dos dados para o CurtailIQ**.
    """)
    return


@app.cell
def _(os, re, unicodedata):
    def _strip_accents(value: str) -> str:
        return "".join(
            char for char in unicodedata.normalize("NFKD", value or "")
            if not unicodedata.combining(char)
        )

    def normalize_name(value: str) -> str:
        value = _strip_accents(str(value or "")).lower().strip()
        value = re.sub(r"[^a-z0-9]+", "_", value)
        value = re.sub(r"_+", "_", value).strip("_")
        return value

    def quote_ident(identifier: str) -> str:
        return '"' + str(identifier).replace('"', '""') + '"'

    def qname(schema_name: str, table_name: str) -> str:
        return f"{quote_ident(schema_name)}.{quote_ident(table_name)}"

    def get_database_url() -> str | None:
        return os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("DB_URL")

    def mask_database_url(url: str | None) -> str:
        if not url:
            return "DATABASE_URL não encontrada"
        return re.sub(r"(://[^:/@]+:)([^@]+)(@)", r"\1***\3", url)

    def classify_table_relevance(schema_name: str, table_name: str, column_names: list[str]) -> dict:
        raw = " ".join([schema_name, table_name, *column_names])
        name = normalize_name(raw)

        keyword_groups = {
            "restricoes_curtailment": ["restr", "curtail", "corte", "constrained", "constrainedoff", "limitacao", "limitada", "razaorestricao", "razao_restricao"],
            "preco_pld_financeiro": ["pld", "preco", "price", "valor", "receita", "perda", "financeiro", "ressarc"],
            "usinas_cadastro": ["usina", "usi", "ativo", "empreendimento", "eolica", "solar", "fonte", "submercado"],
            "disponibilidade_operacao": ["dispon", "indispon", "falha", "manut", "operacao", "geracao", "potencia", "capacidade", "fator_capacidade"],
            "meteorologia_recurso": ["vento", "irradi", "radiacao", "temperatura", "clima", "weather", "velocidade"],
            "dessem_balanco_programacao": ["dessem", "balanco", "program", "carga", "geracao_programada"],
        }
        hits = {
            group: sorted({kw for kw in keywords if kw in name})
            for group, keywords in keyword_groups.items()
        }
        hits = {group: kws for group, kws in hits.items() if kws}

        if hits.get("restricoes_curtailment"):
            priority = "essencial"
            product_use = "Identificação de restrições/curtailment e razão do corte"
        elif hits.get("preco_pld_financeiro"):
            priority = "essencial"
            product_use = "Precificação de energia restringida e perda financeira"
        elif hits.get("usinas_cadastro") and hits.get("disponibilidade_operacao"):
            priority = "essencial"
            product_use = "Cadastro operacional, disponibilidade, geração e seleção de usinas"
        elif hits.get("usinas_cadastro"):
            priority = "útil"
            product_use = "Cadastro/enriquecimento de usinas e chaves de join"
        elif hits.get("disponibilidade_operacao"):
            priority = "útil"
            product_use = "Geração, disponibilidade e validação operacional"
        elif hits.get("dessem_balanco_programacao"):
            priority = "útil"
            product_use = "Programação/balanço e comparação esperado vs verificado"
        elif hits.get("meteorologia_recurso"):
            priority = "enriquecimento"
            product_use = "Forecast e validação de geração disponível"
        else:
            priority = "investigar"
            product_use = "Uso não evidente para o MVP; avaliar amostra e relacionamentos"

        return {
            "prioridade_produto": priority,
            "uso_potencial": product_use,
            "grupos_detectados": ", ".join(hits.keys()) if hits else "nenhum",
            "keywords_detectadas": "; ".join(f"{g}: {', '.join(k)}" for g, k in hits.items()) if hits else "",
        }

    def classify_reason_value(reason: object) -> str:
        normalized = normalize_name(str(reason or ""))
        if not normalized or normalized in {"nan", "none", "null", "indefinido", "na", "n_a"}:
            return "indefinido/revisão humana"
        if any(token in normalized for token in ["cnf", "confiab", "confiabilidade", "rel", "restricao_eletrica", "eletrica", "transmiss", "sistem"]):
            return "potencialmente ressarcível"
        if any(token in normalized for token in ["ene", "energet", "energia"]):
            return "energético/dependente da regra"
        if any(token in normalized for token in ["loc", "local", "interna", "falha", "manut", "indispon"]):
            return "não automático/revisão"
        return "não mapeado/revisão humana"

    def safe_percent(numerator: float, denominator: float) -> float:
        if denominator is None or denominator == 0:
            return 0.0
        return 100.0 * float(numerator or 0) / float(denominator)

    return (
        classify_reason_value,
        classify_table_relevance,
        get_database_url,
        mask_database_url,
        normalize_name,
        qname,
        quote_ident,
    )


@app.cell
def _(mo):
    mo.md("""
    ## 1. Configuração da EDA
    """)
    return


@app.cell
def _(BACKEND_ENV, get_database_url, mask_database_url, mo):
    database_url_value = get_database_url()
    connection_hint = mo.callout(
        f"Conexão detectada: `{mask_database_url(database_url_value)}`\n\n"
        f"Fonte esperada: variável `DATABASE_URL`, `.env` na raiz ou `backend/.env` ({BACKEND_ENV}).",
        kind="info" if database_url_value else "warn",
    )
    connection_hint
    return (database_url_value,)


@app.cell
def _(mo):
    exact_counts_toggle = mo.ui.checkbox(
        label="Executar COUNT(*) exato por tabela (mais lento, mas preciso)",
        value=False,
    )
    sample_limit_slider = mo.ui.slider(100, 10000, value=1000, step=100, label="Linhas máximas para amostras/profiling por tabela")
    top_n_slider = mo.ui.slider(5, 50, value=15, step=5, label="Top N em rankings")
    mo.vstack([exact_counts_toggle, sample_limit_slider, top_n_slider])
    return exact_counts_toggle, sample_limit_slider


@app.cell
def _(SQLAlchemyError, create_engine, database_url_value):
    engine_obj = None
    engine_error = None
    if create_engine is None:
        engine_error = "SQLAlchemy/psycopg não estão instalados neste ambiente."
    elif not database_url_value:
        engine_error = "DATABASE_URL não encontrada. Configure a variável ou backend/.env."
    else:
        try:
            engine_obj = create_engine(database_url_value, pool_pre_ping=True)
        except SQLAlchemyError as exc:
            engine_error = str(exc)
        except Exception as exc:  # noqa: BLE001
            engine_error = str(exc)
    return engine_error, engine_obj


@app.cell
def _(engine_error, engine_obj, mo, text):
    connection_ok = False
    connection_message = None
    if engine_obj is None:
        connection_message = mo.callout(f"Sem conexão ativa: {engine_error}", kind="warn")
    else:
        try:
            with engine_obj.connect() as _conn:
                db_identity = _conn.execute(text("select current_database(), current_user, version()")) .fetchone()
            connection_ok = True
            connection_message = mo.callout(
                f"Conexão OK. Database: `{db_identity[0]}` | User: `{db_identity[1]}`",
                kind="success",
            )
        except Exception as exc:  # noqa: BLE001
            connection_message = mo.callout(f"Falha ao conectar no banco: {exc}", kind="danger")
    connection_message
    return (connection_ok,)


@app.cell
def _(mo):
    mo.md("""
    ## 2. Inventário automático do banco

    Esta seção cria o mapa de schemas, tabelas, colunas, tipos e volumes.
    Se `COUNT(*)` exato estiver desligado, usamos estimativas do PostgreSQL (`pg_class.reltuples`) para não travar a análise em tabelas grandes.
    """)
    return


@app.cell
def _(connection_ok, engine_obj, exact_counts_toggle, pd, qname, text):
    schemas_df = pd.DataFrame()
    tables_df = pd.DataFrame()
    columns_df = pd.DataFrame()

    if connection_ok:
        with engine_obj.connect() as _conn:
            schemas_df = pd.read_sql(
                text(
                    """
                    select schema_name
                    from information_schema.schemata
                    where schema_name not in ('pg_catalog', 'information_schema')
                      and schema_name not like 'pg_toast%'
                    order by schema_name
                    """
                ),
                _conn,
            )

            tables_df = pd.read_sql(
                text(
                    """
                    select
                        t.table_schema,
                        t.table_name,
                        t.table_type,
                        coalesce(c.reltuples::bigint, 0) as estimated_rows
                    from information_schema.tables t
                    left join pg_namespace n on n.nspname = t.table_schema
                    left join pg_class c on c.relnamespace = n.oid and c.relname = t.table_name
                    where t.table_schema not in ('pg_catalog', 'information_schema')
                      and t.table_schema not like 'pg_toast%'
                    order by t.table_schema, t.table_name
                    """
                ),
                _conn,
            )

            columns_df = pd.read_sql(
                text(
                    """
                    select
                        table_schema,
                        table_name,
                        ordinal_position,
                        column_name,
                        data_type,
                        udt_name,
                        is_nullable,
                        character_maximum_length,
                        numeric_precision,
                        numeric_scale
                    from information_schema.columns
                    where table_schema not in ('pg_catalog', 'information_schema')
                      and table_schema not like 'pg_toast%'
                    order by table_schema, table_name, ordinal_position
                    """
                ),
                _conn,
            )

            if exact_counts_toggle.value and not tables_df.empty:
                exact_counts = []
                for _row in tables_df.itertuples(index=False):
                    if _row.table_type != "BASE TABLE":
                        exact_counts.append(None)
                        continue
                    try:
                        count_value = _conn.execute(text(f"select count(*) from {qname(_row.table_schema, _row.table_name)}")).scalar()
                    except Exception:
                        count_value = None
                    exact_counts.append(count_value)
                tables_df["exact_rows"] = exact_counts
            else:
                tables_df["exact_rows"] = pd.NA
    return columns_df, schemas_df, tables_df


@app.cell
def _(columns_df, mo, schemas_df, tables_df):
    if tables_df.empty:
        inventory_summary_card = mo.callout("Inventário ainda vazio: conecte no banco para carregar schemas/tabelas.", kind="warn")
    else:
        total_tables = len(tables_df)
        total_base_tables = int((tables_df["table_type"] == "BASE TABLE").sum())
        total_views = int((tables_df["table_type"] != "BASE TABLE").sum())
        total_columns = len(columns_df)
        inventory_summary_card = mo.md(
            f"""
            **Resumo do inventário**

            - Schemas analisados: **{len(schemas_df):,}**
            - Tabelas/views: **{total_tables:,}**
            - Tabelas físicas: **{total_base_tables:,}**
            - Views/outros objetos: **{total_views:,}**
            - Colunas: **{total_columns:,}**
            """
        )
    inventory_summary_card
    return


@app.cell
def _(mo, tables_df):
    _display = mo.md("Sem tabelas carregadas.") if tables_df.empty else mo.ui.table(tables_df, selection=None, page_size=20)
    _display
    return


@app.cell
def _(classify_table_relevance, columns_df, pd, tables_df):
    product_map_df = pd.DataFrame()
    if not tables_df.empty and not columns_df.empty:
        grouped_columns = (
            columns_df.groupby(["table_schema", "table_name"])["column_name"]
            .apply(lambda values: list(values.astype(str)))
            .reset_index(name="columns")
        )
        product_map_df = tables_df.merge(grouped_columns, on=["table_schema", "table_name"], how="left")
        classified_rows = []
        for _row in product_map_df.itertuples(index=False):
            classified_rows.append(classify_table_relevance(_row.table_schema, _row.table_name, _row.columns or []))
        classified_df = pd.DataFrame(classified_rows)
        product_map_df = pd.concat([product_map_df.reset_index(drop=True), classified_df], axis=1)
        product_map_df["n_colunas"] = product_map_df["columns"].apply(lambda cols: len(cols) if isinstance(cols, list) else 0)
        product_map_df = product_map_df.drop(columns=["columns"])
        product_map_df = product_map_df.sort_values(
            by=["prioridade_produto", "estimated_rows", "table_schema", "table_name"],
            ascending=[True, False, True, True],
        )
    return (product_map_df,)


@app.cell
def _(mo, product_map_df):
    _display = mo.vstack([
        mo.md("## 3. Mapa tabela → utilidade para o CurtailIQ"),
        mo.md("Sem dados para classificar.") if product_map_df.empty else mo.ui.table(product_map_df, selection=None, page_size=20),
    ])
    _display
    return


@app.cell
def _(mo):
    mo.md("""
    ## 4. Relacionamentos possíveis entre tabelas

    Esta seção procura chaves candidatas. Ela não assume que o banco já tenha FK formal.
    Em dados reais de energia, a ligação frequentemente depende de normalização por `nome_usina`, `cod_usina`, `submercado` e tempo.
    """)
    return


@app.cell
def _(columns_df, normalize_name, pd):
    relationship_candidates_df = pd.DataFrame()
    if not columns_df.empty:
        rel_cols = columns_df.copy()
        rel_cols["column_norm"] = rel_cols["column_name"].map(normalize_name)
        rel_cols["table_ref"] = rel_cols["table_schema"] + "." + rel_cols["table_name"]
        rel_cols["is_join_like"] = rel_cols["column_norm"].str.contains(
            "id|cod|codigo|usina|usi|ativo|empreendimento|submercado|data|hora|timestamp|instante|dt|periodo|fonte|razao|restr",
            regex=True,
            na=False,
        )
        candidates = rel_cols[rel_cols["is_join_like"]].copy()
        if not candidates.empty:
            relationship_candidates_df = (
                candidates.groupby(["column_norm", "data_type"])
                .agg(
                    ocorrencias=("table_ref", "count"),
                    tabelas=("table_ref", lambda values: ", ".join(sorted(set(values))[:20])),
                    colunas_originais=("column_name", lambda values: ", ".join(sorted(set(values))[:20])),
                )
                .reset_index()
                .query("ocorrencias >= 2")
                .sort_values(["ocorrencias", "column_norm"], ascending=[False, True])
            )
    return (relationship_candidates_df,)


@app.cell
def _(mo, relationship_candidates_df):
    _display = mo.callout("Nenhuma chave candidata compartilhada encontrada automaticamente.", kind="warn") if relationship_candidates_df.empty else mo.ui.table(relationship_candidates_df, selection=None, page_size=20)
    _display
    return


@app.cell
def _(mo, product_map_df):
    if product_map_df.empty:
        selected_table_ui = mo.ui.dropdown(options=[], label="Tabela para inspeção detalhada")
    else:
        table_options = [f"{_row.table_schema}.{_row.table_name}" for _row in product_map_df.itertuples(index=False)]
        selected_table_ui = mo.ui.dropdown(options=table_options, value=table_options[0], label="Tabela para inspeção detalhada")
    selected_table_ui
    return (selected_table_ui,)


@app.cell
def _(mo):
    mo.md("""
    ## 5. Profiling detalhado da tabela selecionada
    """)
    return


@app.cell
def _(
    connection_ok,
    engine_obj,
    pd,
    qname,
    sample_limit_slider,
    selected_table_ui,
    text,
):
    selected_table_name = selected_table_ui.value
    selected_schema = None
    selected_table = None
    sample_df = pd.DataFrame()
    selected_count = None
    selected_error = None

    if connection_ok and selected_table_name:
        try:
            selected_schema, selected_table = selected_table_name.split(".", 1)
            with engine_obj.connect() as _conn:
                selected_count = _conn.execute(text(f"select count(*) from {qname(selected_schema, selected_table)}")).scalar()
                sample_df = pd.read_sql(
                    text(f"select * from {qname(selected_schema, selected_table)} limit :limit"),
                    _conn,
                    params={"limit": int(sample_limit_slider.value)},
                )
        except Exception as exc:  # noqa: BLE001
            selected_error = str(exc)
    return sample_df, selected_count, selected_error, selected_table_name


@app.cell
def _(mo, sample_df, selected_count, selected_error, selected_table_name):
    if selected_error:
        _display = mo.callout(f"Erro ao carregar `{selected_table_name}`: {selected_error}", kind="danger")
    elif not selected_table_name:
        _display = mo.md("Selecione uma tabela.")
    else:
        _display = mo.md(
            f"""
            **Tabela:** `{selected_table_name}`
            **Linhas totais:** `{selected_count}`
            **Amostra carregada:** `{len(sample_df)}` linhas
            """
        )
    _display
    return


@app.cell
def _(mo, sample_df):
    _display = mo.md("Sem amostra para exibir.") if sample_df.empty else mo.ui.table(sample_df.head(200), selection=None, page_size=15)
    _display
    return


@app.cell
def _(pd, sample_df):
    selected_profile_df = pd.DataFrame()
    if not sample_df.empty:
        profile_rows = []
        for column in sample_df.columns:
            series = sample_df[column]
            non_null = int(series.notna().sum())
            nulls = int(series.isna().sum())
            distinct = int(series.nunique(dropna=True))
            example_values = series.dropna().astype(str).head(5).tolist()
            numeric_series = pd.to_numeric(series, errors="coerce")
            numeric_non_null = int(numeric_series.notna().sum())
            profile_rows.append(
                {
                    "coluna": column,
                    "dtype_pandas": str(series.dtype),
                    "nulos_amostra": nulls,
                    "%_nulos_amostra": round(100 * nulls / max(len(series), 1), 2),
                    "nao_nulos_amostra": non_null,
                    "distintos_amostra": distinct,
                    "parece_numerica": numeric_non_null >= max(3, int(0.8 * non_null)) if non_null else False,
                    "min_num": float(numeric_series.min()) if numeric_non_null else None,
                    "max_num": float(numeric_series.max()) if numeric_non_null else None,
                    "exemplos": " | ".join(example_values),
                }
            )
        selected_profile_df = pd.DataFrame(profile_rows)
    return (selected_profile_df,)


@app.cell
def _(mo, selected_profile_df):
    _display = mo.md("Sem profiling de colunas.") if selected_profile_df.empty else mo.ui.table(selected_profile_df, selection=None, page_size=25)
    _display
    return


@app.cell
def _(mo):
    mo.md("""
    ## 6. Cobertura temporal e granularidade

    Para CurtailIQ, tempo é uma dimensão crítica: restrição, PLD, disponibilidade, geração e previsão precisam se encontrar em janelas compatíveis.
    """)
    return


@app.cell
def _(
    columns_df,
    connection_ok,
    engine_obj,
    normalize_name,
    pd,
    qname,
    quote_ident,
    text,
):
    temporal_coverage_df = pd.DataFrame()
    temporal_errors = []
    temporal_keywords = "data|hora|timestamp|instante|periodo|dt|datetime|time"

    if connection_ok and not columns_df.empty:
        temporal_columns = columns_df[
            columns_df["column_name"].map(normalize_name).str.contains(temporal_keywords, regex=True, na=False)
        ].copy()
        rows = []
        with engine_obj.connect() as _conn:
            for item in temporal_columns.itertuples(index=False):
                full_name = qname(item.table_schema, item.table_name)
                col_name = quote_ident(item.column_name) if "quote_ident" in globals() else '"' + item.column_name.replace('"', '""') + '"'
                try:
                    query = text(
                        f"""
                        select
                            min({col_name})::text as min_value,
                            max({col_name})::text as max_value,
                            count(*) as total_rows,
                            count({col_name}) as non_null_rows,
                            count(distinct {col_name}) as distinct_values
                        from {full_name}
                        """
                    )
                    result = _conn.execute(query).mappings().first()
                    rows.append(
                        {
                            "table_schema": item.table_schema,
                            "table_name": item.table_name,
                            "column_name": item.column_name,
                            "data_type": item.data_type,
                            "min_value": result["min_value"],
                            "max_value": result["max_value"],
                            "total_rows": result["total_rows"],
                            "non_null_rows": result["non_null_rows"],
                            "distinct_values": result["distinct_values"],
                            "coverage_non_null_%": round(100 * result["non_null_rows"] / max(result["total_rows"], 1), 2),
                        }
                    )
                except Exception as exc:  # noqa: BLE001
                    temporal_errors.append(f"{item.table_schema}.{item.table_name}.{item.column_name}: {exc}")
        temporal_coverage_df = pd.DataFrame(rows)
        if not temporal_coverage_df.empty:
            temporal_coverage_df = temporal_coverage_df.sort_values(["table_schema", "table_name", "column_name"])
    return temporal_coverage_df, temporal_errors


@app.cell
def _(mo, temporal_coverage_df, temporal_errors):
    _main = mo.callout("Nenhuma coluna temporal detectada automaticamente.", kind="warn") if temporal_coverage_df.empty else mo.ui.table(temporal_coverage_df, selection=None, page_size=20)
    _errors = mo.accordion({"Erros de cobertura temporal": "\n".join(temporal_errors[:50])}) if temporal_errors else mo.md("")
    mo.vstack([_main, _errors])
    return


@app.cell
def _(mo):
    mo.md("""
    ## 7. Curtailment, restrições e razões

    Esta é a seção central para a solução. Procuramos tabelas/colunas que indiquem:

    - evento de restrição;
    - energia cortada/restringida;
    - razão/código/motivo da restrição;
    - usina/ativo;
    - intervalo temporal;
    - origem da restrição.
    """)
    return


@app.cell
def _(columns_df, normalize_name, pd, product_map_df):
    curtailment_candidates_df = pd.DataFrame()
    if not product_map_df.empty and not columns_df.empty:
        useful = product_map_df[
            product_map_df["grupos_detectados"].fillna("").str.contains("restricoes_curtailment|disponibilidade_operacao|dessem_balanco_programacao", regex=True)
        ][["table_schema", "table_name", "prioridade_produto", "uso_potencial", "estimated_rows"]]
        if not useful.empty:
            col_summary = columns_df.copy()
            col_summary["column_norm"] = col_summary["column_name"].map(normalize_name)
            col_summary["papel_curtailiq"] = "outro"
            col_summary.loc[col_summary["column_norm"].str.contains("razao|motivo|causa|reason|cod_razao|razaorestr", regex=True, na=False), "papel_curtailiq"] = "razão/motivo da restrição"
            col_summary.loc[col_summary["column_norm"].str.contains("restr|curtail|corte|constrained|limit", regex=True, na=False), "papel_curtailiq"] = "restrição/curtailment"
            col_summary.loc[col_summary["column_norm"].str.contains("mwh|energia|geracao|generation", regex=True, na=False), "papel_curtailiq"] = "energia/geração"
            col_summary.loc[col_summary["column_norm"].str.contains("usina|usi|ativo|empreendimento", regex=True, na=False), "papel_curtailiq"] = "usina/ativo"
            col_summary.loc[col_summary["column_norm"].str.contains("data|hora|timestamp|instante|dt|periodo", regex=True, na=False), "papel_curtailiq"] = "tempo"
            curtailment_candidates_df = useful.merge(
                col_summary[["table_schema", "table_name", "column_name", "data_type", "papel_curtailiq"]],
                on=["table_schema", "table_name"],
                how="left",
            ).sort_values(["prioridade_produto", "table_schema", "table_name", "papel_curtailiq"])
    return (curtailment_candidates_df,)


@app.cell
def _(curtailment_candidates_df, mo):
    _display = mo.callout("Nenhuma tabela candidata de restrição/curtailment detectada automaticamente.", kind="warn") if curtailment_candidates_df.empty else mo.ui.table(curtailment_candidates_df, selection=None, page_size=30)
    _display
    return


@app.cell
def _(columns_df, mo, normalize_name):
    reason_column_options = []
    if not columns_df.empty:
        reason_like = columns_df[
            columns_df["column_name"].map(normalize_name).str.contains("razao|motivo|causa|reason|cod_razao|razaorestr", regex=True, na=False)
        ].copy()
        reason_column_options = [
            f"{_row.table_schema}.{_row.table_name}.{_row.column_name}" for _row in reason_like.itertuples(index=False)
        ]
    reason_column_ui = mo.ui.dropdown(
        options=reason_column_options,
        value=reason_column_options[0] if reason_column_options else None,
        label="Coluna de razão/motivo para analisar",
    )
    reason_column_ui
    return (reason_column_ui,)


@app.cell
def _(
    classify_reason_value,
    connection_ok,
    engine_obj,
    mo,
    pd,
    qname,
    quote_ident,
    reason_column_ui,
    text,
):
    reason_distribution_df = pd.DataFrame()
    reason_error = None
    if connection_ok and reason_column_ui.value:
        try:
            parts = reason_column_ui.value.split(".")
            reason_schema, reason_table = parts[0], parts[1]
            reason_col = ".".join(parts[2:])
            with engine_obj.connect() as _conn:
                reason_distribution_df = pd.read_sql(
                    text(
                        f"""
                        select {quote_ident(reason_col)}::text as razao, count(*) as registros
                        from {qname(reason_schema, reason_table)}
                        group by 1
                        order by registros desc
                        limit 200
                        """
                    ),
                    _conn,
                )
            if not reason_distribution_df.empty:
                reason_distribution_df["categoria_regulatoria_inferida"] = reason_distribution_df["razao"].map(classify_reason_value)
                total_reason_rows = reason_distribution_df["registros"].sum()
                reason_distribution_df["%_amostra"] = (100 * reason_distribution_df["registros"] / max(total_reason_rows, 1)).round(2)
        except Exception as exc:  # noqa: BLE001
            reason_error = str(exc)

    if reason_error:
        _display = mo.callout(f"Erro ao analisar razão: {reason_error}", kind="danger")
    elif reason_distribution_df.empty:
        _display = mo.callout("Nenhuma coluna de razão selecionada ou sem dados.", kind="warn")
    else:
        _display = mo.ui.table(reason_distribution_df, selection=None, page_size=20)
    _display
    return (reason_distribution_df,)


@app.cell
def _(mo):
    mo.md("""
    ## 8. Matriz de aderência dos dados às funcionalidades do CurtailIQ

    Esta matriz transforma a EDA em decisão de produto: o banco sustenta ou não cada bloco da solução?
    """)
    return


@app.cell
def _(columns_df, normalize_name, pd, product_map_df):
    def _has_any(pattern: str) -> bool:
        if columns_df.empty and product_map_df.empty:
            return False
        text_blob = " "
        if not columns_df.empty:
            text_blob += " ".join(columns_df["table_name"].astype(str).tolist() + columns_df["column_name"].astype(str).tolist())
        if not product_map_df.empty:
            text_blob += " ".join(product_map_df["table_name"].astype(str).tolist() + product_map_df["grupos_detectados"].astype(str).tolist())
        return pd.Series([normalize_name(text_blob)]).str.contains(pattern, regex=True).iloc[0]

    product_readiness_rows = [
        {
            "funcionalidade": "Identificar eventos de restrição/curtailment",
            "dados_necessarios": "usina, tempo, evento/restrição, energia restringida ou geração esperada/verificada",
            "sinais_no_banco": "restr/curtail/corte/constrained/geração",
            "status_inferido": "suportado/parcial" if _has_any("restr|curtail|corte|constrained|geracao|energia") else "não evidenciado",
            "risco_principal": "confundir perda estimada com restrição real se faltar razão/origem",
        },
        {
            "funcionalidade": "Classificar razão e elegibilidade regulatória",
            "dados_necessarios": "cod_razao_restricao, motivo, origem, regra regulatória versionada",
            "sinais_no_banco": "razao/motivo/causa/origem/cnf/ene/rel",
            "status_inferido": "suportado/parcial" if _has_any("razao|motivo|causa|origem|cnf|ene|rel") else "não evidenciado",
            "risco_principal": "percentual ressarcível vira frágil se razão estiver nula/indefinida",
        },
        {
            "funcionalidade": "Calcular perda financeira",
            "dados_necessarios": "MWh restringido + PLD/preço + submercado + timestamp compatível",
            "sinais_no_banco": "pld/preço/valor/perda/submercado/mwh",
            "status_inferido": "suportado/parcial" if _has_any("pld|preco|price|valor|perda|submercado|mwh") else "não evidenciado",
            "risco_principal": "PLD sem cobertura temporal/submercado gera perda zerada ou incorreta",
        },
        {
            "funcionalidade": "Ranking e seleção de usinas",
            "dados_necessarios": "cadastro de usina, fonte, submercado, capacidade, coordenadas opcionais",
            "sinais_no_banco": "usina/ativo/empreendimento/fonte/submercado/capacidade",
            "status_inferido": "suportado/parcial" if _has_any("usina|ativo|empreendimento|fonte|submercado|capacidade") else "não evidenciado",
            "risco_principal": "nomes/códigos inconsistentes impedem joins e mapa confiável",
        },
        {
            "funcionalidade": "Forecast de perda/corte",
            "dados_necessarios": "histórico temporal suficiente, granularidade regular, features sazonais/recurso",
            "sinais_no_banco": "séries temporais de geração/restrição/perda",
            "status_inferido": "suportado como MVP" if _has_any("data|hora|timestamp|instante|restr|geracao|perda") else "não evidenciado",
            "risco_principal": "sem recurso meteorológico/SCADA o forecast deve ser tratado como MVP/fallback",
        },
        {
            "funcionalidade": "Simulador BESS",
            "dados_necessarios": "série horária de energia perdida/recuperável e valor financeiro",
            "sinais_no_banco": "energia restringida/perda por hora",
            "status_inferido": "suportado como simulação" if _has_any("mwh|energia|perda|restr|geracao") else "não evidenciado",
            "risco_principal": "sem granularidade horária, dimensionamento técnico fica aproximado",
        },
        {
            "funcionalidade": "Dossiê/pleito regulatório",
            "dados_necessarios": "eventos, razão, memória de cálculo, evidências e revisão humana",
            "sinais_no_banco": "restrição + razão + perda financeira",
            "status_inferido": "parcial/depende de evidências" if _has_any("restr|razao|motivo|perda|pld") else "não evidenciado",
            "risco_principal": "sem trilha documental/SCADA/documentos oficiais, não vender como prova auditada completa",
        },
    ]
    product_readiness_df = pd.DataFrame(product_readiness_rows)
    return (product_readiness_df,)


@app.cell
def _(mo, product_readiness_df):
    mo.ui.table(product_readiness_df, selection=None, page_size=10)
    return


@app.cell
def _(mo):
    mo.md("""
    ## 9. Score de qualidade e utilidade por tabela

    Score heurístico para priorizar onde investigar e quais tabelas devem virar camada `gold`.
    """)
    return


@app.cell
def _(columns_df, math, pd, product_map_df, temporal_coverage_df):
    table_quality_score_df = pd.DataFrame()
    if not product_map_df.empty:
        base_quality = product_map_df.copy()
        priority_points = {
            "essencial": 35,
            "útil": 25,
            "enriquecimento": 15,
            "investigar": 5,
        }
        base_quality["score_utilidade_produto"] = base_quality["prioridade_produto"].map(priority_points).fillna(0)
        base_quality["score_volume"] = base_quality["estimated_rows"].fillna(0).clip(lower=0).map(lambda value: min(20, math.log10(value + 1) * 5) if "math" in globals() else 0)

        if not temporal_coverage_df.empty:
            temp_score = (
                temporal_coverage_df.groupby(["table_schema", "table_name"])
                .agg(
                    colunas_temporais=("column_name", "count"),
                    melhor_cobertura_temporal=("coverage_non_null_%", "max"),
                )
                .reset_index()
            )
        else:
            temp_score = pd.DataFrame(columns=["table_schema", "table_name", "colunas_temporais", "melhor_cobertura_temporal"])

        column_score = (
            columns_df.groupby(["table_schema", "table_name"])
            .agg(n_colunas_reais=("column_name", "count"))
            .reset_index()
            if not columns_df.empty else pd.DataFrame(columns=["table_schema", "table_name", "n_colunas_reais"])
        )

        table_quality_score_df = (
            base_quality.merge(temp_score, on=["table_schema", "table_name"], how="left")
            .merge(column_score, on=["table_schema", "table_name"], how="left")
        )
        table_quality_score_df["colunas_temporais"] = table_quality_score_df["colunas_temporais"].fillna(0)
        table_quality_score_df["melhor_cobertura_temporal"] = table_quality_score_df["melhor_cobertura_temporal"].fillna(0)
        table_quality_score_df["score_temporal"] = table_quality_score_df["melhor_cobertura_temporal"].map(lambda value: min(20, value / 5))
        table_quality_score_df["score_contrato"] = table_quality_score_df["n_colunas_reais"].fillna(0).map(lambda value: min(10, value / 2))
        table_quality_score_df["score_total_0_100"] = (
            table_quality_score_df["score_utilidade_produto"]
            + table_quality_score_df["score_volume"]
            + table_quality_score_df["score_temporal"]
            + table_quality_score_df["score_contrato"]
        ).round(1)
        table_quality_score_df = table_quality_score_df.sort_values("score_total_0_100", ascending=False)
    return (table_quality_score_df,)


@app.cell
def _(mo, table_quality_score_df):
    _display = mo.md("Sem score calculado.") if table_quality_score_df.empty else mo.ui.table(table_quality_score_df, selection=None, page_size=20)
    _display
    return


@app.cell
def _(mo):
    mo.md("""
    ## 10. Recomendações automáticas para camada gold e próximos passos
    """)
    return


@app.cell
def _(
    mo,
    product_map_df,
    product_readiness_df,
    relationship_candidates_df,
    table_quality_score_df,
):
    if product_map_df.empty:
        recommendations_md = "Conecte no banco para gerar recomendações."
    else:
        essential_tables = product_map_df[product_map_df["prioridade_produto"].eq("essencial")]
        useful_tables = product_map_df[product_map_df["prioridade_produto"].eq("útil")]
        gold_candidates = table_quality_score_df.head(10)[["table_schema", "table_name", "prioridade_produto", "score_total_0_100", "uso_potencial"]] if not table_quality_score_df.empty else essential_tables.head(10)
        weak_features = product_readiness_df[product_readiness_df["status_inferido"].str.contains("não evidenciado", na=False)]
        join_count = 0 if relationship_candidates_df.empty else len(relationship_candidates_df)

        recommendations_md = f"""
        **Leitura executiva automática**

        - Tabelas essenciais detectadas: **{len(essential_tables)}**
        - Tabelas úteis detectadas: **{len(useful_tables)}**
        - Chaves candidatas compartilhadas: **{join_count}**
        - Funcionalidades sem evidência clara de dados: **{len(weak_features)}**

        **Candidatas iniciais para camada gold**

        {gold_candidates.to_markdown(index=False) if not gold_candidates.empty else "Nenhuma candidata detectada."}

        **Recomendações técnicas**

        1. Criar uma `gold.restricoes_curtailment` com: `id_evento`, `cod_usina`, `nome_usina`, `timestamp_inicio`, `timestamp_fim`, `energia_restringida_mwh`, `cod_razao_restricao`, `origem_restricao`, `submercado`, `fonte_dado`.
        2. Criar uma `gold.usinas` com chave estável de usina, fonte, submercado, capacidade, coordenadas e aliases/de-para.
        3. Criar uma `gold.pld_horario` com timestamp normalizado, submercado e preço numérico auditável.
        4. Criar uma `gold.perdas_curtailment` materializada ou view com o join `restrição × PLD × usina` e memória de cálculo.
        5. Versionar a política regulatória que transforma razão da restrição em `potencialmente_ressarcivel`, `nao_ressarcivel`, `indefinido`.
        6. Separar claramente: `curtailment registrado`, `curtailment inferido`, `perda econômica estimada` e `pleito auditável`.
        7. Medir cobertura dos joins: percentual de eventos com usina encontrada, PLD encontrado, razão válida e energia não nula.
        8. Escolher uma usina-caso para demo com alto score: evento real, razão preenchida, perda financeira relevante e boa cobertura temporal.
        """

    mo.md(recommendations_md)
    return


@app.cell
def _(mo):
    mo.md("## 11. Exportar artefatos da EDA")
    export_button = mo.ui.run_button(label="Exportar CSVs para ./eda_outputs")
    export_button
    return (export_button,)


@app.cell
def _(
    OUTPUT_DIR,
    datetime,
    export_button,
    mo,
    product_map_df,
    product_readiness_df,
    reason_distribution_df,
    relationship_candidates_df,
    table_quality_score_df,
    tables_df,
    temporal_coverage_df,
):
    export_message = mo.md("Clique no botão acima para exportar.")
    if export_button.value:
        OUTPUT_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        outputs = {
            "tables_inventory": tables_df,
            "product_table_map": product_map_df,
            "relationship_candidates": relationship_candidates_df,
            "temporal_coverage": temporal_coverage_df,
            "reason_distribution": reason_distribution_df,
            "product_readiness_matrix": product_readiness_df,
            "table_quality_score": table_quality_score_df,
        }
        written = []
        for name, df in outputs.items():
            if df is not None and not df.empty:
                path = OUTPUT_DIR / f"{timestamp}_{name}.csv"
                df.to_csv(path, index=False, encoding="utf-8-sig")
                written.append(str(path.name))
        export_message = mo.callout(
            "Arquivos exportados em `./eda_outputs`:\n\n" + "\n".join(f"- {name}" for name in written),
            kind="success",
        )
    export_message
    return


@app.cell
def _(mo):
    mo.md("""
    ## 12. Checklist final para apresentação

    Use esta EDA para responder objetivamente:

    - Temos eventos reais de restrição ou apenas estimativas por diferença?
    - A razão da restrição está presente, padronizada e preenchida?
    - A energia restringida vem pronta ou precisa ser calculada?
    - O PLD cobre o mesmo período, granularidade e submercado dos eventos?
    - As tabelas de usina conectam com restrições e financeiro sem perda relevante de cobertura?
    - Quais usinas são melhores para demo?
    - Qual percentual da perda é potencialmente ressarcível por regra determinística?
    - O que ainda falta para chamar de curtailment auditável em produção?

    **Mensagem central:** a EDA deve separar dado real, inferência, estimativa econômica e evidência regulatória.
    """)
    return


if __name__ == "__main__":
    app.run()

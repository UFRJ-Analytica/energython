# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "marimo>=0.10.0",
#   "pandas>=2.2.0",
#   "sqlalchemy>=2.0.0",
#   "psycopg[binary]>=3.2.0",
#   "python-dotenv>=1.0.0",
#   "plotly>=5.20.0",
# ]
# ///
"""
CurtailIQ — EDA Dimensional do Data Warehouse (schema `dw`)
==========================================================
EDA completa do DW estrela/floco de neve do CurtailIQ, com MAPA DO BRASIL
em granularidade de UNIDADE (cada usina = 1 ponto), construída diretamente
sobre o modelo dimensional:

    dim_usina (25.265 usinas) · dim_geografia (28 UFs→subsistema)
    dim_subsistema (N/NE/S/SE) · dim_fonte_tipo (14) · dim_data · dim_hora
    fato_geracao (20M) · fato_restricao_coff (12M)
    marts: mart_geracao_mensal, mart_coff_mensal,
           mart_disponibilidade_mensal, mart_fatorcapacidade_mensal

Como rodar (na raiz do projeto):
    export DATABASE_URL="postgresql+psycopg://user:pass@host:port/db"
    marimo edit curtailiq_eda_dw.py        # modo edição
    marimo run  curtailiq_eda_dw.py        # modo dashboard (somente leitura)

A conexão é lida de DATABASE_URL (ambiente, .env raiz ou backend/.env).
"""
import marimo

__generated_with = "0.23.9"
app = marimo.App(width="full")


# --------------------------------------------------------------------------- #
# 0. Imports, conexão e helpers
# --------------------------------------------------------------------------- #
@app.cell
def _():
    import os
    import re
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    from sqlalchemy import create_engine, text

    try:
        from dotenv import load_dotenv
    except Exception:
        load_dotenv = None

    ROOT = Path(__file__).resolve().parent
    if load_dotenv is not None:
        for env_path in (ROOT / ".env", ROOT / "backend" / ".env"):
            if env_path.exists():
                load_dotenv(env_path, override=False)

    def get_db_url() -> str | None:
        url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL") or os.getenv("DB_URL")
        if url and url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url

    def mask(url: str | None) -> str:
        if not url:
            return "DATABASE_URL não encontrada"
        return re.sub(r"(://[^:/@]+:)([^@]+)(@)", r"\1***\3", url)

    DB_URL = get_db_url()
    engine = create_engine(DB_URL, pool_pre_ping=True) if DB_URL else None

    def run_sql(sql: str) -> pd.DataFrame:
        """Executa SQL e devolve DataFrame (vazio se sem conexão)."""
        if engine is None:
            return pd.DataFrame()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)

    pd.set_option("display.max_columns", 200)
    return DB_URL, engine, go, mask, mo, pd, px, run_sql, text


@app.cell
def _(mo):
    mo.md(
        """
        # CurtailIQ · EDA do Data Warehouse Dimensional

        **Objetivo:** explorar o DW (esquema estrela + floco de neve) que sustenta a
        plataforma de inteligência de *curtailment* (corte forçado de geração renovável
        pelo ONS), em **granularidade de unidade** — cada usina do Brasil é um ponto no
        mapa, com tipo de energia, geração, corte e localização.

        O DW costura **fatos** (medições) a **dimensões** (contexto) pela usina
        (`sk_usina`) e pelo tempo (`sk_data`/`sk_hora`):

        ```
            dim_tempo (dim_data + dim_hora 48 blocos 30min)
                          │
        dim_usina ───►  FATOS (fato_geracao 20M · fato_restricao_coff 12M)  ◄─── dim_fonte_tipo
            │                          │
            └► dim_geografia ──► dim_subsistema (N/NE/S/SE)   [floco de neve]
        ```
        """
    )
    return


@app.cell
def _(DB_URL, mask, mo):
    _kind = "success" if DB_URL else "danger"
    mo.callout(
        f"Conexão: `{mask(DB_URL)}`\n\n"
        "Defina `DATABASE_URL` (ambiente, `.env` raiz ou `backend/.env`) caso esteja vazia.",
        kind=_kind,
    )
    return


# --------------------------------------------------------------------------- #
# 1. Estrutura do DW: inventário de tabelas e relacionamentos
# --------------------------------------------------------------------------- #
@app.cell
def _(mo):
    mo.md("## 1. Estrutura do Data Warehouse e relacionamentos")
    return


@app.cell
def _(mo, run_sql):
    inv = run_sql(
        """
        select c.relname as tabela,
               case c.relkind when 'r' then 'tabela' when 'p' then 'particionada'
                              when 'm' then 'mat. view' else c.relkind end as tipo,
               coalesce(c.reltuples::bigint, 0) as linhas_estimadas
        from pg_class c
        join pg_namespace n on n.oid = c.relnamespace
        where n.nspname = 'dw' and c.relkind in ('r','p','m')
          and c.relname not similar to '%(_20[0-9][0-9]|_def)'
        order by linhas_estimadas desc, tabela
        """
    )
    _t = mo.md("Sem conexão.") if inv.empty else mo.ui.table(inv, selection=None, page_size=25)
    mo.vstack([mo.md("**Objetos do schema `dw`** (partições anuais ocultadas):"), _t])
    return (inv,)


@app.cell
def _(mo):
    mo.md(
        """
        ### Matriz fato × dimensão (bus matrix)

        | Fato | dim_tempo | dim_usina | dim_geografia | dim_subsistema | dim_fonte_tipo |
        |---|:--:|:--:|:--:|:--:|:--:|
        | `fato_geracao` | ✅ | ✅ | ✅ | ✅ (via geo) | ✅ |
        | `fato_restricao_coff` | ✅ | ✅ | ✅ | ✅ (via geo) | — |
        | `fato_disponibilidade` | ✅ | ✅ | ✅ | ✅ (via geo) | — |
        | `fato_fator_capacidade` | ✅ | ✅ | ✅ | ✅ (via geo) | — |
        | `fato_balanco_dessem` | ✅ | — | — | ✅ (submercado) | — |

        **Dimensões conformadas:** `dim_usina`, `dim_geografia`, `dim_subsistema` e
        `dim_data`/`dim_hora` são compartilhadas pelas fatos, permitindo *drill-across*
        (ex.: geração × corte × disponibilidade da mesma usina). O elo do **floco de
        neve** é `dim_usina → dim_geografia → dim_subsistema`.
        """
    )
    return


# --------------------------------------------------------------------------- #
# 2. Dataset mestre por usina (granularidade de unidade)
# --------------------------------------------------------------------------- #
@app.cell
def _(mo):
    mo.md(
        """
        ## 2. Dataset mestre — uma linha por usina

        Junta `dim_usina` ao floco geográfico e pré-agrega os marts por `sk_usina`
        (geração total, corte total, % corte, disponibilidade e fator de capacidade
        médios). É a base do mapa e dos rankings.
        """
    )
    return


@app.cell
def _(run_sql):
    usinas = run_sql(
        """
        with ger as (
            select sk_usina, sum(sum_geracao)/1000.0 as ger_gwh
            from dw.mart_geracao_mensal group by 1
        ),
        co as (
            select sk_usina,
                   sum(sum_corte)/1000.0 as corte_gwh,
                   100.0*sum(sum_corte)/nullif(sum(sum_referencia),0) as pct_corte
            from dw.mart_coff_mensal group by 1
        ),
        disp as (
            select sk_usina, avg(avg_dispoperacional) as disp_oper_mw
            from dw.mart_disponibilidade_mensal group by 1
        ),
        fc as (
            select sk_usina, avg(avg_fatorcapacidade) as fator_capacidade
            from dw.mart_fatorcapacidade_mensal group by 1
        )
        select u.sk_usina, u.nom_usina, u.ceg_core, u.tipo, u.municipio,
               u.lat, u.lon,
               g.id_estado, g.nom_estado,
               coalesce(s.nom_subsistema,'(sem subsistema)') as subsistema,
               coalesce(ger.ger_gwh, 0)       as ger_gwh,
               coalesce(co.corte_gwh, 0)      as corte_gwh,
               co.pct_corte,
               disp.disp_oper_mw,
               fc.fator_capacidade
        from dw.dim_usina u
        left join dw.dim_geografia  g on g.sk_geografia  = u.sk_geografia
        left join dw.dim_subsistema s on s.sk_subsistema = g.sk_subsistema
        left join ger  on ger.sk_usina  = u.sk_usina
        left join co   on co.sk_usina   = u.sk_usina
        left join disp on disp.sk_usina = u.sk_usina
        left join fc   on fc.sk_usina   = u.sk_usina
        where u.lat between -34 and 6 and u.lon between -74 and -34
        """
    )
    # rótulos amigáveis do tipo de usina
    TIPO_LABEL = {
        "UFV": "Solar (UFV)", "EOL": "Eólica (EOL)", "UTE": "Térmica (UTE)",
        "UHE": "Hidrelétrica (UHE)", "PCH": "Pequena Central Hidr. (PCH)",
        "CGH": "Central Geradora Hidr. (CGH)", "UTN": "Nuclear (UTN)",
    }
    if not usinas.empty:
        usinas["tipo_label"] = usinas["tipo"].map(TIPO_LABEL).fillna(usinas["tipo"]).fillna("Desconhecido")
        usinas["tem_corte"] = usinas["corte_gwh"] > 0
    return (usinas,)


@app.cell
def _(mo, usinas):
    if usinas.empty:
        _card = mo.callout("Sem dados — verifique a conexão.", kind="warn")
    else:
        n = len(usinas)
        com_ger = int((usinas["ger_gwh"] > 0).sum())
        com_corte = int((usinas["corte_gwh"] > 0).sum())
        corte_total = usinas["corte_gwh"].sum()
        ger_total = usinas["ger_gwh"].sum()
        _card = mo.hstack([
            mo.stat(label="Usinas no mapa", value=f"{n:,}"),
            mo.stat(label="Com geração registrada", value=f"{com_ger:,}"),
            mo.stat(label="Com curtailment", value=f"{com_corte:,}"),
            mo.stat(label="Geração total (GWh)", value=f"{ger_total:,.0f}"),
            mo.stat(label="Corte total (GWh)", value=f"{corte_total:,.0f}"),
        ], justify="start", gap=2)
    _card
    return


# --------------------------------------------------------------------------- #
# 3. MAPA DO BRASIL — granularidade de unidade
# --------------------------------------------------------------------------- #
@app.cell
def _(mo):
    mo.md(
        """
        ## 3. Mapa do Brasil — todas as usinas (granularidade de unidade)

        Cada ponto é **uma usina**. Use os controles para filtrar por tipo de fonte e
        subsistema, e escolher o que a **cor** e o **tamanho** representam.
        Passe o mouse para ver nome, tipo, município, UF, geração e corte acumulados.
        """
    )
    return


@app.cell
def _(mo, usinas):
    if usinas.empty:
        controls = mo.md("Sem dados.")
        tipo_sel = sub_sel = color_by = size_by = só_corte = None
    else:
        tipos = sorted(usinas["tipo_label"].dropna().unique().tolist())
        subs = sorted(usinas["subsistema"].dropna().unique().tolist())
        tipo_sel = mo.ui.multiselect(options=tipos, value=tipos, label="Tipo de fonte")
        sub_sel = mo.ui.multiselect(options=subs, value=subs, label="Subsistema")
        color_by = mo.ui.dropdown(
            options=["Tipo de fonte", "Subsistema", "% de corte"],
            value="Tipo de fonte", label="Cor dos pontos",
        )
        size_by = mo.ui.dropdown(
            options=["Uniforme", "Geração (GWh)", "Corte (GWh)"],
            value="Corte (GWh)", label="Tamanho dos pontos",
        )
        só_corte = mo.ui.checkbox(value=False, label="Mostrar só usinas com curtailment")
        controls = mo.hstack([tipo_sel, sub_sel, color_by, size_by, só_corte],
                             justify="start", gap=1, wrap=True)
    controls
    return color_by, size_by, sub_sel, só_corte, tipo_sel


@app.cell
def _(color_by, mo, px, size_by, sub_sel, só_corte, tipo_sel, usinas):
    if usinas.empty or tipo_sel is None:
        _fig = mo.md("Sem dados para o mapa.")
    else:
        _df = usinas[
            usinas["tipo_label"].isin(tipo_sel.value)
            & usinas["subsistema"].isin(sub_sel.value)
        ].copy()
        if só_corte.value:
            _df = _df[_df["corte_gwh"] > 0]

        color_map = {
            "Tipo de fonte": "tipo_label",
            "Subsistema": "subsistema",
            "% de corte": "pct_corte",
        }
        size_map = {"Uniforme": None, "Geração (GWh)": "ger_gwh", "Corte (GWh)": "corte_gwh"}
        color_col = color_map[color_by.value]
        size_col = size_map[size_by.value]

        kw = dict(
            lat="lat", lon="lon",
            hover_name="nom_usina",
            hover_data={
                "tipo_label": True, "municipio": True, "id_estado": True,
                "subsistema": True, "ger_gwh": ":.1f", "corte_gwh": ":.1f",
                "pct_corte": ":.1f", "lat": False, "lon": False,
            },
            zoom=3.0, height=720,
            center={"lat": -14.5, "lon": -52.0},
        )
        if size_col is not None:
            _sz = _df[size_col].clip(lower=0).fillna(0)
            _df["_size"] = _sz + (_sz.max() * 0.01 if _sz.max() else 1)  # mínimo visível
            kw["size"] = "_size"
            kw["size_max"] = 28
        if color_col == "pct_corte":
            kw["color_continuous_scale"] = "YlOrRd"
            kw["range_color"] = [0, 60]

        _fig = px.scatter_mapbox(_df, color=color_col, **kw)
        _fig.update_layout(
            mapbox_style="carto-positron",
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            legend_title_text=color_by.value,
            title=f"{len(_df):,} usinas — cor: {color_by.value} · tamanho: {size_by.value}",
        )
        _fig = mo.ui.plotly(_fig)
    _fig
    return


# --------------------------------------------------------------------------- #
# 4. Distribuição do parque gerador
# --------------------------------------------------------------------------- #
@app.cell
def _(mo):
    mo.md("## 4. Composição do parque gerador (cadastro `dim_usina`)")
    return


@app.cell
def _(mo, px, usinas):
    if usinas.empty:
        _out = mo.md("Sem dados.")
    else:
        _por_tipo = usinas.groupby("tipo_label").size().reset_index(name="usinas").sort_values("usinas")
        _f1 = px.bar(_por_tipo, x="usinas", y="tipo_label", orientation="h",
                    title="Usinas por tipo de fonte", text="usinas", height=380)
        _f1.update_layout(margin=dict(t=40, l=10, r=10, b=10), yaxis_title="", xaxis_title="nº de usinas")

        _por_sub = usinas.groupby("subsistema").size().reset_index(name="usinas")
        _f2 = px.pie(_por_sub, names="subsistema", values="usinas",
                    title="Usinas por subsistema", height=380, hole=0.4)

        _out = mo.hstack([mo.ui.plotly(_f1), mo.ui.plotly(_f2)], widths=[1, 1])
    _out
    return


@app.cell
def _(mo, px, usinas):
    if usinas.empty:
        _out = mo.md("Sem dados.")
    else:
        _df = usinas.groupby(["id_estado", "tipo_label"]).size().reset_index(name="usinas")
        ordem = (usinas.groupby("id_estado").size().sort_values(ascending=False).index.tolist())
        _fig = px.bar(_df, x="id_estado", y="usinas", color="tipo_label",
                     category_orders={"id_estado": ordem},
                     title="Usinas por UF e tipo de fonte (empilhado)", height=420)
        _fig.update_layout(margin=dict(t=40, l=10, r=10, b=10),
                          xaxis_title="UF", yaxis_title="nº de usinas", legend_title="Tipo")
        _out = mo.ui.plotly(_fig)
    _out
    return


# --------------------------------------------------------------------------- #
# 5. Curtailment — o coração do produto
# --------------------------------------------------------------------------- #
@app.cell
def _(mo):
    mo.md(
        """
        ## 5. Curtailment (restrição COFF) — evolução e composição

        `fato_restricao_coff` / `mart_coff_mensal`. **Corte** = `val_geracaoreferencia − val_geracao`
        (energia que a usina geraria mas foi mandada cortar). O % de corte cresce ano a
        ano — o cerne da tese do CurtailIQ.
        """
    )
    return


@app.cell
def _(run_sql):
    coff_mensal = run_sql(
        """
        select make_date(ano, mes, 1) as mes_ref, ano, mes, fonte,
               sum(sum_corte)/1000.0       as corte_gwh,
               sum(sum_referencia)/1000.0  as ref_gwh,
               100.0*sum(sum_corte)/nullif(sum(sum_referencia),0) as pct_corte
        from dw.mart_coff_mensal
        group by 1,2,3,4
        order by 1,4
        """
    )
    coff_razao = run_sql(
        """
        select coalesce(cod_razao,'(sem razão)') as cod_razao,
               coalesce(cod_origem,'(sem origem)') as cod_origem,
               count(*) as registros, sum(val_geracaoreferencia - val_geracao)/1000.0 as corte_gwh
        from dw.fato_restricao_coff
        where val_geracaoreferencia is not null and val_geracao is not null
        group by 1,2
        order by corte_gwh desc nulls last
        """
    )
    return coff_mensal, coff_razao


@app.cell
def _(coff_mensal, mo, px):
    if coff_mensal.empty:
        _out = mo.md("Sem dados de curtailment.")
    else:
        _f1 = px.area(coff_mensal, x="mes_ref", y="corte_gwh", color="fonte",
                     title="Energia cortada por mês e fonte (GWh)", height=380)
        _f1.update_layout(margin=dict(t=40, l=10, r=10, b=10), xaxis_title="", yaxis_title="GWh cortados")
        _f2 = px.line(coff_mensal, x="mes_ref", y="pct_corte", color="fonte", markers=True,
                     title="% de geração cortada por mês e fonte", height=380)
        _f2.update_layout(margin=dict(t=40, l=10, r=10, b=10), xaxis_title="", yaxis_title="% cortado")
        _out = mo.vstack([mo.ui.plotly(_f1), mo.ui.plotly(_f2)])
    _out
    return


@app.cell
def _(coff_razao, mo, px):
    if coff_razao.empty:
        _out = mo.md("Sem dados de razão.")
    else:
        ELIG = {
            "CNF": "Confiabilidade elétrica → RESSARCÍVEL",
            "REL": "Confiabilidade/rede → potencialmente ressarcível",
            "ENE": "Razão energética (sobreoferta) → NÃO ressarcível",
        }
        _df = coff_razao.groupby("cod_razao", as_index=False)["corte_gwh"].sum()
        _df["elegibilidade"] = _df["cod_razao"].map(ELIG).fillna("Indefinido / revisão humana")
        _df = _df[_df["corte_gwh"] > 0].sort_values("corte_gwh", ascending=False)
        _fig = px.bar(_df, x="cod_razao", y="corte_gwh", color="elegibilidade",
                     title="Corte por razão regulatória (elegibilidade de ressarcimento)",
                     text="corte_gwh", height=420)
        _fig.update_traces(texttemplate="%{text:.0f}")
        _fig.update_layout(margin=dict(t=40, l=10, r=10, b=10),
                          xaxis_title="cod_razao", yaxis_title="GWh cortados",
                          legend_title="Enquadramento (REN 1.030/2022 · Lei 15.269/2025)")
        _out = mo.vstack([
            mo.ui.plotly(_fig),
            mo.md("> **CNF/REL** (confiabilidade/rede) tendem a ser ressarcíveis; "
                  "**ENE** (sobreoferta) **não** é. Registros com razão nula exigem revisão."),
        ])
    _out
    return


# --------------------------------------------------------------------------- #
# 6. Ranking de usinas mais cortadas + destaque no mapa
# --------------------------------------------------------------------------- #
@app.cell
def _(mo):
    mo.md("## 6. Usinas mais afetadas por curtailment")
    return


@app.cell
def _(mo):
    top_n = mo.ui.slider(5, 50, value=20, step=5, label="Top N usinas por corte acumulado")
    top_n
    return (top_n,)


@app.cell
def _(mo, px, top_n, usinas):
    if usinas.empty:
        _out = mo.md("Sem dados.")
    else:
        _top = (usinas[usinas["corte_gwh"] > 0]
               .nlargest(int(top_n.value), "corte_gwh")
               .sort_values("corte_gwh"))
        _fig = px.bar(_top, x="corte_gwh", y="nom_usina", orientation="h",
                     color="tipo_label", hover_data=["id_estado", "subsistema", "pct_corte"],
                     title=f"Top {int(top_n.value)} usinas por corte acumulado (GWh)", height=600)
        _fig.update_layout(margin=dict(t=40, l=10, r=10, b=10), yaxis_title="", xaxis_title="GWh cortados",
                          legend_title="Tipo")
        _out = mo.vstack([mo.ui.plotly(_fig),
                          mo.ui.table(_top[["nom_usina", "tipo_label", "id_estado", "subsistema",
                                           "ger_gwh", "corte_gwh", "pct_corte"]].iloc[::-1],
                                      selection=None, page_size=10)])
    _out
    return


# --------------------------------------------------------------------------- #
# 7. Geração: tendência mensal e perfil semi-horário
# --------------------------------------------------------------------------- #
@app.cell
def _(mo):
    mo.md("## 7. Geração — tendência mensal e perfil intradiário")
    return


@app.cell
def _(run_sql):
    ger_mensal = run_sql(
        """
        select make_date(ano, mes, 1) as mes_ref, nom_tipousina,
               sum(sum_geracao)/1000.0 as ger_gwh
        from dw.mart_geracao_mensal
        group by 1,2 order by 1
        """
    )
    # perfil intradiário (médio) por fonte renovável — usa dim_hora (48 blocos)
    perfil_hora = run_sql(
        """
        select h.hhmm, ftt.nom_tipousina,
               avg(f.val_geracao) as ger_media_mw
        from dw.fato_geracao f
        join dw.dim_hora h        on h.hora_sk = f.sk_hora
        join dw.dim_fonte_tipo ftt on ftt.sk_fonte_tipo = f.sk_fonte_tipo
        where ftt.nom_tipousina in ('EOLIELÉTRICA','FOTOVOLTAICA')
          and f.din_instante >= date '2025-01-01'
        group by 1,2 order by 1
        """
    )
    return ger_mensal, perfil_hora


@app.cell
def _(ger_mensal, mo, perfil_hora, px):
    _parts = []
    if not ger_mensal.empty:
        _f1 = px.area(ger_mensal, x="mes_ref", y="ger_gwh", color="nom_tipousina",
                     title="Geração mensal por tipo de usina (GWh)", height=420)
        _f1.update_layout(margin=dict(t=40, l=10, r=10, b=10), xaxis_title="", yaxis_title="GWh",
                         legend_title="Tipo")
        _parts.append(mo.ui.plotly(_f1))
    if not perfil_hora.empty:
        _f2 = px.line(perfil_hora, x="hhmm", y="ger_media_mw", color="nom_tipousina", markers=False,
                     title="Perfil intradiário médio (2025) — 48 blocos de 30 min", height=380)
        _f2.update_layout(margin=dict(t=40, l=10, r=10, b=10),
                         xaxis_title="hora do dia (HH:MM)", yaxis_title="geração média (MW)",
                         legend_title="Tipo")
        _parts.append(mo.ui.plotly(_f2))
    (mo.vstack(_parts) if _parts else mo.md("Sem dados de geração."))
    return


# --------------------------------------------------------------------------- #
# 8. Síntese executiva
# --------------------------------------------------------------------------- #
@app.cell
def _(mo):
    mo.md("## 8. Síntese executiva")
    return


@app.cell
def _(coff_mensal, mo, usinas):
    if usinas.empty or coff_mensal.empty:
        _out = mo.md("Sem dados para síntese.")
    else:
        corte_tot = usinas["corte_gwh"].sum()
        pior = usinas.nlargest(1, "corte_gwh").iloc[0]
        ult = coff_mensal[coff_mensal["fonte"] == "EOLICA"].sort_values("mes_ref")
        pct_atual = ult["pct_corte"].dropna().iloc[-1] if not ult.empty else float("nan")
        _out = mo.md(
            f"""
            - **Parque mapeado:** {len(usinas):,} usinas georreferenciadas, granularidade de unidade.
            - **Solar (UFV)** domina em número de usinas; concentração no **Norte (PA)** e **Nordeste**.
            - **Curtailment acumulado (2023–2026):** ~**{corte_tot:,.0f} GWh** cortados.
            - **% de corte eólico** mais recente na série: ~**{pct_atual:.1f}%** — tendência de alta.
            - **Usina mais afetada:** **{pior['nom_usina']}** ({pior['tipo_label']}, {pior['id_estado']})
              com **{pior['corte_gwh']:,.0f} GWh** cortados.
            - **Elegibilidade:** parcela relevante do corte é por **razão energética (ENE)** —
              **não** ressarcível; o valor de produto está em isolar **CNF/REL** e documentar o pleito.

            > O DW dimensional entrega tudo que os três elos do CurtailIQ precisam:
            > físico (geração/corte por usina e hora), financeiro (corte × PLD via `public.ccee_pld_horario`)
            > e regulatório (razão/origem do corte para classificação de ressarcimento).
            """
        )
    _out
    return


if __name__ == "__main__":
    app.run()

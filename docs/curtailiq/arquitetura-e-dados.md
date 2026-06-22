# Arquitetura e Dados

## Visão geral

O app é um Streamlit monolítico (`stramlit/app.py`) que conecta diretamente ao DW PostgreSQL via DuckDB Postgres extension.

Fluxo principal:

```text
PostgreSQL DW -> DuckDB ATTACH postgres -> Pandas DataFrames -> Streamlit/Plotly/CatBoost/JupyterLite
```

## Conexão com o banco

Função:

```python
def _con():
    con = duckdb.connect()
    con.execute("INSTALL postgres; LOAD postgres;")
    con.execute(f"ATTACH '{PG_DSN}' AS pg (TYPE postgres, READ_ONLY)")
    return con
```

A conexão é read-only e sempre fecha após consulta.

## Schema utilizado

```python
SCHEMA = "dw"
```

## Tabelas principais

### `dw.mart_eolica`

Usada para a frota/complexos e séries temporais por `nom_usina`.

Campos usados:

| Campo | Uso |
|---|---|
| `din_instante` | eixo temporal de 30 minutos |
| `nom_usina` | chave de seleção da usina/complexo |
| `id_estado`, `nom_estado` | região/UF |
| `nom_subsistema` | subsistema elétrico |
| `potencia_mw` | potência instalada quando disponível |
| `val_geracao` | geração observada MW |
| `val_geracaoreferencia` | geração de referência MW |
| `val_disponibilidade` | disponibilidade MW |
| `val_geracaolimitada` | geração limitada |
| `cod_razaorestricao` | ENE/CNF/REL |
| `cod_origemrestricao` | SIS/LOC/etc. |

Regras:

```text
corte_mw = max(val_geracaoreferencia - val_geracao, 0)
aplica corte apenas quando cod_razaorestricao IS NOT NULL
MWh = soma(MW por intervalo de 30min) / 2
```

### `dw.dim_usina`

Usada para coordenadas reais e normalização geográfica.

Campos usados:

| Campo | Uso |
|---|---|
| `sk_usina` | chave unitária |
| `ceg_core` | filtro EOL |
| `nom_usina` | match por nome |
| `lat`, `lon` | mapa |
| `id_ons`, `municipio` | metadados unitários |
| `sk_geografia` | join com dimensão geográfica |

Observação: `dim_usina.fonte` não é confiável neste DW; o app filtra eólicas por `ceg_core LIKE 'EOL%'`.

### `dw.dim_geografia`

Usada para centróides por estado como fallback de coordenada.

### `dw.fato_restricao_coff`

Usada para a aba **Unidades Individuais** e série por `sk_usina`.

Campos usados:

| Campo | Uso |
|---|---|
| `sk_usina` | unidade individual |
| `din_instante` | série temporal |
| `id_estado` | UF |
| `val_geracao` | geração observada |
| `val_geracaoreferencia` | referência |
| `val_disponibilidade` | proxy de potência/disponibilidade |
| `cod_razao`, `cod_origem` | restrição |

Importante: no DW atual, apenas 11 unidades têm dados unitários reais; muitas linhas agregadas aparecem como `sk_usina = 0`, que o app ignora para não inventar granularidade.

## Caches locais

### `.cache_frota_eolica.parquet`

Criado por `carregar_frota()` para evitar varrer `mart_eolica` em toda carga.

Contém 205 usinas/complexos.

### `.cache_unidades_eolica.parquet`

Criado por `build_unit_cache.py`.

Contém 11 unidades individuais com `sk_usina` real.

### `jupyterlite_content/`

Conteúdo do Analyst Lab:

```text
jupyterlite_content/
  data/<slug>_serie.csv
  eda_<slug>.ipynb
  <slug>_metadata.json
```

### `jupyterlite_site/`

Build estático do JupyterLite, servido por `jupyter lite serve`.

## Regras regulatórias implementadas

| Código | Interpretação | Ressarcível? |
|---|---|---|
| `ENE` | energética / sobreoferta | não |
| `CNF` | confiabilidade elétrica | sim |
| `REL` | rede/confiabilidade | sim |

Cálculos:

```python
corte_ene_mwh = corte onde cod_razao == 'ENE'
corte_ressarc_mwh = corte onde cod_razao in ('CNF', 'REL')
perda_reais = corte_mwh * PLD_PADRAO
perda_ressarcivel_reais = corte_ressarc_mwh * PLD_PADRAO
```

## Constantes

```python
PLD_PADRAO = 135.35
JUPYTERLITE_PORT = 8766
```

# Documentação das Abas

## Aba 1 — Control Tower

### Objetivo

Visão executiva da frota eólica em estilo Palantir: KPIs, mapa, alertas e corte por estado.

### Fonte de dados

Função `carregar_frota()`:

- base: `dw.mart_eolica`
- coordenadas: `dw.dim_usina`
- centróides: `dw.dim_geografia`
- cache: `.cache_frota_eolica.parquet`

### KPIs

| KPI | Fórmula |
|---|---|
| Usinas monitoradas | `len(frota)` |
| Energia cortada | `sum(corte_mwh)` |
| Perda financeira | `sum(perda_reais)` |
| Potencial ressarcível | `sum(perda_ressarcivel_reais)` |
| Corte médio | `sum(corte_mwh) / sum(ref_mwh)` |

### Mapa

Plotly Mapbox:

- latitude/longitude por `dim_usina` ou centróide estadual;
- tamanho por `sqrt(corte_mwh)`;
- cor selecionável por:
  - Health Score;
  - `% Corte`;
  - `Perda R$`.

### Painel lateral

Lista as 8 piores usinas por `pct_corte`.

### Corte por estado

Agrupa por `id_estado` e `nom_estado`, somando corte/perda e calculando score médio.

---

## Aba 2 — Detalhe & Previsão

### Objetivo

Drill-down de uma usina/complexo e previsão de geração por modelo híbrido.

### Fonte de dados

- seleção: `frota[nom_usina]`
- série: `carregar_serie(nom_usina)` usando `dw.mart_eolica`

### Ficha da usina

- estado/subsistema;
- potência;
- rank/score;
- `% corte`;
- perda financeira;
- perda ressarcível;
- fator de capacidade.

### Composição de corte

Pie chart:

- `corte_ene_mwh`;
- `corte_ressarc_mwh`.

### Previsão

Controles:

- pontos históricos;
- horizonte.

Modelo:

```text
LinearRegression baseline + CatBoostRegressor no resíduo
```

Gráficos:

- histórico;
- real;
- baseline linear;
- híbrido;
- banda P10/P90;
- importância de features.

Métricas:

- MAE baseline;
- MAE híbrido;
- ganho percentual.

---

## Aba 3 — Anomalias

### Objetivo

Detectar eventos fora do padrão em geração/referência/disponibilidade.

### Fonte de dados

`carregar_serie(nom_usina)` → `dw.mart_eolica`.

### Modelo

`IsolationForest` com contaminação ajustável.

### Features

- geração;
- referência;
- gap;
- hora;
- disponibilidade.

### Visualizações

- série referência x geração;
- pontos anômalos;
- heatmap hora x dia;
- tabela dos eventos mais severos.

---

## Aba 4 — Inteligência (Notícias)

### Objetivo

Buscar e relacionar notícias à usina escolhida.

### Motor

Função `buscar_noticias_relacionadas`.

### Processo

1. limpa nome da usina;
2. gera múltiplas consultas Google News RSS;
3. deduplica links;
4. calcula relevância;
5. exibe cards ordenados.

### Relevância

Pontua por:

- nome da usina;
- nome completo;
- termos do setor elétrico/eólico;
- município/estado;
- penalidade por homônimos sem contexto energético.

---

## Aba 5 — Ranking Top Tier

### Objetivo

Rankear melhores e piores usinas por UF/região.

### Fonte

`frota` carregada de `dw.mart_eolica`.

### Score

```text
50% baixo corte
20% baixa perda
30% fator de capacidade
```

### Componentes

- filtro de UF;
- tabela melhores 10;
- tabela piores 10;
- score médio por UF;
- dispersão risco x perda.

---

## Aba 6 — Unidades Individuais

### Objetivo

Dashboard sem agrupamento por complexo: cada linha/ponto é uma unidade individual `sk_usina`.

### Fonte

- `dw.fato_restricao_coff`
- `dw.dim_usina`
- cache `.cache_unidades_eolica.parquet`

### Observação de granularidade

O DW tem muitas linhas agregadas em `sk_usina = 0`; a aba usa apenas unidades com `sk_usina` real para evitar granularidade falsa.

### KPIs

- número de unidades;
- corte total;
- perda;
- ressarcível;
- corte médio.

### Componentes

- mapa por unidade;
- ranking unitário;
- seleção de unidade;
- KPIs unitários;
- composição de corte;
- previsão híbrida da unidade.

### Série unitária

`carregar_serie_unidade(sk_usina)` usa `dw.fato_restricao_coff`.

---

## Aba 7 — Analyst Lab (JupyterLite)

### Objetivo

Permitir que analistas façam EDA manual no navegador a partir da usina escolhida.

### Fluxo

1. usuário escolhe usina;
2. escolhe número de pontos;
3. clica em gerar Lab;
4. app exporta CSV;
5. app gera notebook `.ipynb`;
6. app executa `jupyter lite init` e `jupyter lite build`;
7. app sobe `jupyter lite serve` na porta 8766;
8. app embedda o Lab via iframe.

### Saídas

- `jupyterlite_content/data/<slug>_serie.csv`
- `jupyterlite_content/eda_<slug>.ipynb`
- `jupyterlite_content/<slug>_metadata.json`
- `jupyterlite_site/`

### Notebook gerado

Células:

1. introdução e metadados;
2. setup Pyodide/pandas/matplotlib;
3. carga CSV;
4. resumo executivo;
5. série geração x referência x corte;
6. perfil horário;
7. razão de restrição;
8. outliers por z-score;
9. ideias de investigação.

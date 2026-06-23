# Relatório técnico — técnicas usadas no Streamlit CurtailIQ

> Escopo analisado: `stramlit/app.py`, `stramlit/build_unit_cache.py`, `stramlit/requirements.txt`, `stramlit/jupyterlite_content/` e o build em `stramlit/jupyterlite_site/`.
>
> Observação de segurança: o código atual contém string de conexão com banco diretamente no arquivo. Este relatório descreve a técnica de conexão, mas não replica credenciais.

## 1. Visão geral do app

O CurtailIQ é um app Streamlit monolítico, em estilo **control tower**, para análise de curtailment eólico. A aplicação combina:

- leitura direta de Data Warehouse PostgreSQL via DuckDB;
- agregações SQL e engenharia de métricas em Pandas/Numpy;
- visualizações Plotly interativas;
- previsão com modelo híbrido `LinearRegression + CatBoostRegressor`;
- detecção de anomalias com `IsolationForest`;
- busca de notícias via Google News RSS com ranking de relevância;
- laboratório JupyterLite embutido para EDA manual no navegador.

Arquivos principais:

| Arquivo/pasta | Papel |
|---|---|
| `stramlit/app.py` | App Streamlit principal, abas, funções de dados, modelos, UI e JupyterLite. |
| `stramlit/build_unit_cache.py` | Script auxiliar para cache de unidades individuais por `sk_usina`. |
| `stramlit/requirements.txt` | Dependências Python do app e do JupyterLite. |
| `stramlit/jupyterlite_content/` | Conteúdo-fonte do Analyst Lab: notebooks, CSVs e metadados. |
| `stramlit/jupyterlite_site/` | Site estático gerado pelo `jupyter lite build`. |
| `stramlit/catboost_info/` | Artefatos automáticos de treinamento CatBoost. |

## 2. Técnicas de arquitetura e dados

### 2.1 Streamlit monolítico com abas

O app organiza a experiência em 7 abas por `st.tabs`, mantendo todo o fluxo em `app.py`:

1. Control Tower;
2. Detalhe & Previsão;
3. Anomalias;
4. Inteligência (Notícias);
5. Ranking Top Tier;
6. Unidades Individuais;
7. Analyst Lab (JupyterLite).

Técnicas usadas:

- `st.set_page_config(layout="wide")` para tela larga;
- CSS customizado via `st.markdown(..., unsafe_allow_html=True)`;
- estado global da seleção via `st.session_state.usina_sel`;
- KPIs reutilizáveis com helper `kpi(col, label, value, sub)`;
- widgets por aba: `selectbox`, `slider`, `radio`, `button`, `download_button`;
- renderização de gráficos Plotly por `st.plotly_chart`;
- embedding de JupyterLite por `components.iframe`.

### 2.2 Conexão DW via DuckDB Postgres extension

A função `_con()` abre uma conexão DuckDB em memória, instala/carrega a extensão Postgres e faz `ATTACH` do DW em modo read-only.

Técnica aplicada:

```text
PostgreSQL DW -> DuckDB ATTACH postgres -> SQL -> Pandas DataFrame -> Streamlit
```

Benefícios:

- usa DuckDB como camada analítica local;
- permite SQL direto em tabelas PostgreSQL;
- retorna resultados com `.df()` já em Pandas;
- evita ORM e mantém queries analíticas explícitas.

Ponto de melhoria recomendado:

- mover a DSN para `st.secrets`, variável de ambiente ou arquivo `.streamlit/secrets.toml`, sem hard-code em `app.py` e `build_unit_cache.py`.

### 2.3 Caches com `st.cache_data` e Parquet local

O app usa dois níveis de cache:

1. **cache Streamlit**: `@st.cache_data` em funções caras;
2. **cache físico Parquet**: arquivos locais para evitar varredura completa do DW.

Funções cacheadas:

| Função | Técnica |
|---|---|
| `carregar_frota()` | Carrega frota agregada e salva/lê `.cache_frota_eolica.parquet`. |
| `carregar_serie()` | Baixa série temporal por usina. |
| `carregar_unidades()` | Lê `.cache_unidades_eolica.parquet`. |
| `carregar_serie_unidade()` | Baixa série por `sk_usina`. |
| `treinar_hibrido()` | Cacheia resultado do treinamento para mesmos parâmetros. |
| `detectar_anomalias()` | Cacheia detecção para mesma série/contaminação. |
| `buscar_noticias_relacionadas()` | Cache com TTL de 1800s para reduzir chamadas RSS. |

### 2.4 Agregação de frota a partir de mart granular

`carregar_frota()` agrega `dw.mart_eolica` por `nom_usina` sem depender de rollups pré-computados.

Métricas calculadas no SQL:

- potência máxima (`max(potencia_mw)`);
- número de registros (`count(*)`);
- geração MWh (`sum(val_geracao) / 2`);
- referência MWh (`sum(val_geracaoreferencia) / 2`);
- corte MWh baseado no gap positivo entre referência e geração;
- corte energético `ENE`;
- corte potencialmente ressarcível `CNF`/`REL`.

Regra de conversão:

```text
intervalos de 30 minutos -> MWh = soma(MW) / 2
```

Regra de corte:

```text
corte_mw = max(val_geracaoreferencia - val_geracao, 0)
só entra como corte quando existe cod_razaorestricao
```

### 2.5 Enriquecimento geográfico

Técnicas usadas para posicionar usinas no mapa:

- busca de coordenadas reais em `dw.dim_usina` filtrando eólicas por `ceg_core LIKE 'EOL%'`;
- normalização de nomes com remoção de termos como `CONJ.`, `CONJUNTO`, `EÓLICO`, `COMPLEXO`, `PARQUE`;
- merge por chave textual limpa (`nom_key`);
- fallback por centróide estadual em `dw.dim_geografia`;
- jitter aleatório determinístico (`np.random.default_rng(42)`) para reduzir sobreposição visual.

### 2.6 Métricas regulatórias e financeiras

O app implementa uma classificação simplificada de curtailment:

| Código | Interpretação no app | Tratamento |
|---|---|---|
| `ENE` | Energética / sobreoferta | Não ressarcível |
| `CNF` | Confiabilidade elétrica | Ressarcível |
| `REL` | Rede/confiabilidade | Ressarcível |

Cálculos derivados:

- `% corte = corte_mwh / ref_mwh`;
- `% ressarcível = corte_ressarc_mwh / corte_mwh`;
- `perda_reais = corte_mwh * PLD_PADRAO`;
- `perda_ressarcivel_reais = corte_ressarc_mwh * PLD_PADRAO`;
- fator de capacidade aproximado por geração média dividida pela potência.

### 2.7 Health Score 0–100

A pontuação combina risco operacional e performance:

```text
score = 100 * (
    0.50 * (1 - norm(pct_corte)) +
    0.20 * (1 - norm(log1p(perda_reais))) +
    0.30 * norm(fator_capacidade)
)
```

Técnicas usadas:

- normalização min-max;
- penalização de corte;
- penalização logarítmica de perda financeira;
- bonificação de fator de capacidade;
- ranking global por score.

## 3. Técnicas de machine learning e séries temporais

### 3.1 Feature engineering temporal, sazonal e operacional

Função: `montar_features(df)`.

Features temporais:

| Feature | Técnica |
|---|---|
| `hora` | Hora decimal do dia. |
| `dow` | Dia da semana. |
| `mes` | Mês. |
| `t_idx` | Índice sequencial como tendência. |

Features sazonais de Fourier:

| Feature | Técnica |
|---|---|
| `sin_d1/cos_d1` | Ciclo diário fundamental. |
| `sin_d2/cos_d2` | Segundo harmônico diário. |
| `sin_d3/cos_d3` | Terceiro harmônico diário. |
| `sin_w/cos_w` | Ciclo semanal. |

Features operacionais:

| Feature | Técnica |
|---|---|
| `disp` | Disponibilidade preenchida pela mediana. |
| `ref` | Referência com forward-fill. |
| `restrito` | Indicador binário de restrição. |
| `razao_ene` | Indicador binário de restrição energética. |

Features autoregressivas:

| Feature | Técnica |
|---|---|
| `lag_1` | Defasagem de 1 ponto. |
| `lag_2` | Defasagem de 2 pontos. |
| `lag_48` | Defasagem diária em série de 30 min. |
| `roll_mean_6` | Média móvel curta. |
| `roll_mean_48` | Média móvel diária. |

Tratamento de nulos:

- `ffill` para referência;
- preenchimento por mediana para disponibilidade;
- `bfill` e `fillna(0)` após criar lags/rollings.

### 3.2 Modelo híbrido Linear Regression + CatBoost no resíduo

Função: `treinar_hibrido(df, horizonte)`.

A técnica substitui o antigo Prophet por um modelo híbrido em duas camadas:

1. `LinearRegression` aprende baseline interpretável com tendência, sazonalidade e contexto;
2. `CatBoostRegressor` aprende o resíduo não-linear do baseline.

Fluxo:

```text
features -> split temporal -> LinearRegression -> resíduo -> CatBoost -> predição final
```

Predição final:

```text
pred_hibrido = clip(pred_linear + pred_catboost_residuo, 0, infinito)
```

Hiperparâmetros usados no CatBoost:

| Parâmetro | Valor |
|---|---:|
| `iterations` | 400 |
| `depth` | 6 |
| `learning_rate` | 0.05 |
| `loss_function` | RMSE |
| `random_seed` | 42 |
| `l2_leaf_reg` | 3.0 |

Métricas:

- MAE do baseline;
- MAE do híbrido;
- ganho percentual de redução de erro;
- importância das features do CatBoost.

### 3.3 Banda de incerteza aproximada P10/P90

A incerteza é estimada pelo desvio padrão do resíduo final in-sample:

```text
sigma = std(y_train - pred_train_hibrido)
p10 = pred_hibrido - 1.28 * sigma
p90 = pred_hibrido + 1.28 * sigma
```

A técnica é simples e operacional, adequada para visualização rápida, mas não substitui calibração probabilística formal.

### 3.4 Detecção de anomalias com Isolation Forest

Função: `detectar_anomalias(df, contaminacao=0.04)`.

Modelo:

- `IsolationForest`;
- `n_estimators=200`;
- `random_state=42`;
- contaminação controlada por slider na UI.

Features:

| Feature | Uso |
|---|---|
| `val_geracao` | Observado. |
| `val_geracaoreferencia` | Referência. |
| `gap` | Referência - geração. |
| `hora` | Padrão intradiário. |
| `disp` | Disponibilidade. |

Saídas:

- `anomalia = True/False`;
- `score_anom = -score_samples`, onde maior significa mais anômalo.

Visualizações associadas:

- série geração x referência com pontos anômalos;
- heatmap hora x dia;
- tabela dos eventos mais severos.

## 4. Técnicas por aba

### Aba 1 — Control Tower

Objetivo: visão executiva da frota.

Técnicas:

- KPIs HTML customizados;
- mapa `px.scatter_mapbox` com estilo `carto-darkmatter`;
- seleção de ponto no mapa com `on_select="rerun"`;
- uso de `custom_data` para atualizar `st.session_state.usina_sel`;
- tamanho dos pontos por `sqrt(corte_mwh)`;
- cor dinâmica por Health Score, `% Corte` ou Perda;
- painel lateral com alertas das piores usinas;
- agregação por UF e gráfico de barras.

### Aba 2 — Detalhe & Previsão

Objetivo: drill-down por usina e previsão.

Técnicas:

- seleção da usina sincronizada com o mapa;
- ficha da usina por KPIs;
- decomposição `ENE` vs `CNF/REL` por pie chart;
- sliders para histórico e horizonte;
- treinamento sob demanda com botão;
- gráfico temporal com histórico, real, baseline, híbrido e banda P10/P90;
- barras de importância de features.

### Aba 3 — Anomalias

Objetivo: detectar comportamentos atípicos de corte.

Técnicas:

- `IsolationForest` com contaminação ajustável;
- cálculo de gap `referência - geração`;
- gráfico temporal com marcadores `x` em vermelho;
- heatmap de contagem de anomalias por hora e dia;
- ranking dos eventos mais severos por score.

### Aba 4 — Inteligência (Notícias)

Objetivo: relacionar notícias à usina escolhida.

Técnicas:

- Google News RSS via `urllib.request`;
- múltiplas consultas por nome limpo, parque eólico, usina eólica, município e termos extras;
- normalização textual sem acento;
- regex com limite de palavra para evitar falsos positivos;
- deduplicação por link;
- score de relevância com pesos;
- bônus para nome completo + contexto energético;
- penalidade para homônimos sem contexto;
- corte mínimo de relevância `>= 8.0`;
- cards HTML com links externos.

### Aba 5 — Ranking Top Tier

Objetivo: ranquear melhores e piores usinas por score.

Técnicas:

- filtro por UF;
- tabelas lado a lado de top 10 e bottom 10;
- `st.column_config.ProgressColumn` para score;
- score médio por UF;
- dispersão risco x perda com bolha dimensionada por corte.

### Aba 6 — Unidades Individuais

Objetivo: dashboard por unidade real `sk_usina`, sem agrupamento por complexo.

Técnicas:

- leitura do cache `.cache_unidades_eolica.parquet`;
- granularidade unitária via `dw.fato_restricao_coff`;
- mapa por unidade;
- ranking unitário;
- drill-down por unidade;
- previsão híbrida reaproveitando `treinar_hibrido()`;
- uso de `val_disponibilidade` como proxy de potência/disponibilidade na série unitária.

### Aba 7 — Analyst Lab (JupyterLite)

Objetivo: gerar ambiente de EDA manual por usina.

Técnicas:

- slug seguro para nomes de arquivo;
- exportação de CSV com série temporal;
- geração de metadados JSON;
- criação programática de notebook com `nbformat`;
- build do JupyterLite por `subprocess.run`;
- servidor `jupyter lite serve` em background;
- teste de porta via `socket`;
- URL direta para abrir o notebook no Lab;
- iframe embutido no Streamlit;
- botões para baixar CSV e notebook.

Notebook gerado inclui:

1. introdução e metadados;
2. setup Pyodide/pandas/matplotlib;
3. carga do CSV;
4. resumo executivo;
5. série geração x referência x corte;
6. perfil horário médio;
7. quebra por razão de restrição;
8. outliers por z-score;
9. ideias de investigação manual.

## 5. Técnicas nas pastas do Streamlit

### `jupyterlite_content/`

Pasta de conteúdo-fonte do Lab.

Técnicas observadas:

- notebook `.ipynb` extraído/gerado por `nbformat`;
- CSV em `data/` para rodar no Pyodide;
- metadados JSON por usina;
- notebook autoexplicativo para investigação offline/no navegador.

Exemplo encontrado:

| Arquivo | Papel |
|---|---|
| `eda_conjunto_eolico_kairos.ipynb` | Notebook EDA gerado para uma usina. |
| `conjunto_eolico_kairos_metadata.json` | Metadados usados no notebook. |
| `data/conjunto_eolico_kairos_serie.csv` | Série exportada para análise. |

### `jupyterlite_site/`

Pasta de build estático do JupyterLite.

Técnicas:

- empacotamento de Lab/Tree/REPL/Consoles estáticos;
- kernels Pyodide em browser;
- extensões JupyterLab/Plotly/CatBoost copiadas para o site;
- arquivos de API estática (`api/contents`, `api/translations`, workspaces etc.).

### `catboost_info/`

Pasta gerada pelo CatBoost durante treinamentos.

Técnica:

- log/artefatos de treinamento (`catboost_training.json`) para rastrear iterações e métricas internas.

### `requirements.txt`

Dependências indicam as técnicas do projeto:

| Pacote | Técnica habilitada |
|---|---|
| `streamlit` | UI web data app. |
| `duckdb` | engine analítica e conexão Postgres. |
| `pandas`, `numpy` | dataframes, métricas, features. |
| `scikit-learn` | regressão linear e IsolationForest. |
| `catboost` | modelo não-linear de resíduos. |
| `plotly` | mapas e gráficos interativos. |
| `matplotlib` | visualização no notebook JupyterLite. |
| `jupyterlite`, `jupyterlite-core`, `jupyterlite-pyodide-kernel` | Lab no navegador. |
| `jupyter_server`, `jupyterlab_server` | suporte/serviço Jupyter. |
| `nbformat` | geração programática de notebooks. |

Observação: `lightgbm` e `prophet` aparecem nas dependências, mas o `app.py` atual usa CatBoost e não usa Prophet no fluxo principal.

## 6. Skills reutilizáveis derivadas das técnicas

As técnicas abaixo podem virar “skills” reutilizáveis em outros projetos. Cada skill resume um padrão replicável.

### Skill 1 — Streamlit Control Tower

**Quando usar:** dashboards executivos com KPIs, mapa e alertas.

**Passos:**

1. configurar tema e layout wide;
2. criar helper de KPI;
3. carregar dataframe principal cacheado;
4. montar mapa com métrica de cor e tamanho;
5. sincronizar seleção com `st.session_state`;
6. exibir alertas/rankings laterais.

### Skill 2 — DuckDB como ponte para PostgreSQL analítico

**Quando usar:** app Python precisa consultar DW sem ORM e entregar Pandas.

**Passos:**

1. abrir conexão DuckDB;
2. carregar extensão Postgres;
3. fazer `ATTACH` read-only;
4. executar SQL analítico;
5. converter com `.df()`;
6. fechar conexão em `finally`.

### Skill 3 — Métricas de curtailment e ressarcimento

**Quando usar:** análise de geração renovável com referência e restrição.

**Passos:**

1. calcular `gap = ref - geração`;
2. aplicar `max(gap, 0)`;
3. contabilizar apenas eventos com razão de restrição;
4. converter MW de 30 min em MWh por `/2`;
5. separar `ENE` de `CNF/REL`;
6. estimar perda por PLD.

### Skill 4 — Forecast híbrido Linear + CatBoost residual

**Quando usar:** série temporal com sazonalidade e não-linearidades, sem depender de Prophet.

**Passos:**

1. criar features temporais/Fourier/lags/rolling;
2. separar treino/teste por horizonte final;
3. treinar regressão linear como baseline;
4. calcular resíduo;
5. treinar CatBoost no resíduo;
6. somar baseline + correção;
7. avaliar MAE e ganho;
8. plotar importância das features.

### Skill 5 — Anomalias operacionais com IsolationForest

**Quando usar:** detectar pontos atípicos sem rótulo.

**Passos:**

1. criar gap e contexto horário;
2. selecionar features numéricas;
3. definir contaminação ajustável;
4. treinar `IsolationForest`;
5. marcar `fit_predict == -1`;
6. inverter `score_samples` para severidade;
7. exibir série, heatmap e tabela.

### Skill 6 — News intelligence com RSS e score de relevância

**Quando usar:** relacionar notícias externas a ativos específicos.

**Passos:**

1. limpar nome do ativo;
2. gerar múltiplas queries;
3. buscar RSS;
4. deduplicar links;
5. normalizar texto;
6. pontuar nome, contexto, município/UF;
7. penalizar homônimos;
8. filtrar por score mínimo.

### Skill 7 — JupyterLite Analyst Lab dentro do Streamlit

**Quando usar:** oferecer EDA manual sem sair do app.

**Passos:**

1. exportar dataset filtrado para CSV;
2. gerar notebook por `nbformat`;
3. gravar metadados JSON;
4. executar `jupyter lite init/build`;
5. subir servidor local em porta definida;
6. montar URL do notebook;
7. embutir via iframe;
8. disponibilizar downloads.

### Skill 8 — Dashboard por granularidade unitária

**Quando usar:** evitar análise enganosa por agregados e expor entidades reais.

**Passos:**

1. escolher chave unitária (`sk_usina`);
2. filtrar dimensões válidas;
3. gerar cache dedicado;
4. calcular métricas por unidade;
5. preservar drill-down e previsão reaproveitando funções comuns.

## 7. Riscos e melhorias recomendadas

| Tema | Situação atual | Recomendação |
|---|---|---|
| Segredos | DSN hard-coded nos scripts. | Migrar para `st.secrets` ou variáveis de ambiente. |
| Monólito | `app.py` concentra dados, modelos, UI e Lab. | Modularizar em `data.py`, `models.py`, `ui.py`, `lab.py`. |
| Cache | Parquet local acelera, mas pode ficar desatualizado. | Incluir botão/TTL de refresh e data de geração. |
| Incerteza | P10/P90 por sigma in-sample. | Calibrar por backtesting/quantile regression. |
| News | RSS pode falhar ou mudar formato. | Adicionar fallback e logs de erro. |
| JupyterLite | Build pode ser lento dentro do clique. | Cachear por slug e rebuildar só quando dados mudarem. |
| Dependências | `prophet` e `lightgbm` estão instalados mas não usados no app atual. | Remover ou documentar uso futuro. |

## 8. Referências diretas no código

- `stramlit/app.py:94` — conexão DuckDB/Postgres.
- `stramlit/app.py:101` — cache e carga da frota.
- `stramlit/app.py:281` — feature engineering.
- `stramlit/app.py:317` — modelo híbrido Linear + CatBoost.
- `stramlit/app.py:377` — detecção de anomalias.
- `stramlit/app.py:424` — busca de notícias relacionada à usina.
- `stramlit/app.py:557` — geração do notebook EDA.
- `stramlit/app.py:657` — preparação/build do JupyterLite.
- `stramlit/app.py:773` — criação das 7 abas.
- `stramlit/build_unit_cache.py:7` — cache unitário por `sk_usina`.

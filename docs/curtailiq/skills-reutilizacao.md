# Skills de reutilização — técnicas do CurtailIQ Streamlit

Este documento transforma as técnicas usadas em `stramlit/app.py` em skills reutilizáveis. As skills abaixo são padrões de implementação que podem ser reaplicados em outros apps de dados.

## Skill 1 — Streamlit Control Tower

**Objetivo:** criar uma tela executiva com KPIs, mapa interativo, alertas e drill-down.

**Quando usar:** monitoramento de ativos, frota, unidades operacionais, risco, perdas ou performance.

**Entradas típicas:**

- dataframe principal com uma linha por ativo;
- colunas de latitude/longitude;
- métricas de severidade, score e perda;
- identificador do ativo para seleção.

**Passos:**

1. configurar `st.set_page_config(layout="wide")`;
2. aplicar CSS customizado com `st.markdown(..., unsafe_allow_html=True)`;
3. criar helper de KPI em HTML;
4. cachear a base principal;
5. montar `px.scatter_mapbox` com cor e tamanho configuráveis;
6. passar identificador do ativo em `custom_data`;
7. usar `st.plotly_chart(..., on_select="rerun")`;
8. salvar seleção em `st.session_state`;
9. exibir painel lateral com top riscos/alertas.

**Implementado em:** `stramlit/app.py`, Aba 1.

---

## Skill 2 — DuckDB como camada analítica para PostgreSQL

**Objetivo:** consultar um DW PostgreSQL diretamente a partir do app, retornando Pandas DataFrames.

**Quando usar:** consultas analíticas, agregações pesadas e prototipagem rápida sem ORM.

**Passos:**

1. abrir conexão DuckDB local;
2. carregar extensão Postgres;
3. anexar banco externo em modo read-only;
4. executar SQL analítico;
5. converter resultado com `.df()`;
6. fechar conexão em `finally`.

**Cuidados:**

- não hard-code credenciais;
- preferir `st.secrets` ou variáveis de ambiente;
- cachear resultados caros.

**Implementado em:** `_con()`, `carregar_frota()`, `carregar_serie()`, `carregar_serie_unidade()`.

---

## Skill 3 — Métricas de curtailment e ressarcimento

**Objetivo:** calcular corte de geração, perda financeira e parcela potencialmente ressarcível.

**Quando usar:** dados com geração observada, geração de referência e razão de restrição.

**Regras:**

1. `gap = val_geracaoreferencia - val_geracao`;
2. `corte = max(gap, 0)`;
3. considerar corte apenas se existe código de restrição;
4. converter intervalo de 30 minutos para MWh com `/2`;
5. separar `ENE` de `CNF/REL`;
6. estimar perda com `corte_mwh * PLD`.

**Saídas:**

- `corte_mwh`;
- `corte_ene_mwh`;
- `corte_ressarc_mwh`;
- `perda_reais`;
- `perda_ressarcivel_reais`;
- `pct_corte`;
- `pct_ressarcivel`.

**Implementado em:** `carregar_frota()` e `build_unit_cache.py`.

---

## Skill 4 — Health Score operacional

**Objetivo:** produzir um score 0–100 para ranquear ativos.

**Quando usar:** ranking comparativo de performance, risco ou prioridade.

**Fórmula usada:**

```text
score = 100 * (
    0.50 * (1 - norm(pct_corte)) +
    0.20 * (1 - norm(log1p(perda_reais))) +
    0.30 * norm(fator_capacidade)
)
```

**Técnicas:**

- normalização min-max;
- penalização de variáveis de risco;
- transformação logarítmica para perdas monetárias;
- ranking por score descendente.

**Implementado em:** `carregar_frota()` e `build_unit_cache.py`.

---

## Skill 5 — Feature engineering para série temporal operacional

**Objetivo:** criar variáveis para previsão de geração.

**Quando usar:** séries com sazonalidade diária/semanal, tendência, contexto operacional e autocorrelação.

**Features:**

- calendário: `hora`, `dow`, `mes`, `t_idx`;
- Fourier diário: `sin_d1/cos_d1`, `sin_d2/cos_d2`, `sin_d3/cos_d3`;
- Fourier semanal: `sin_w/cos_w`;
- contexto: disponibilidade, referência, restrição, razão ENE;
- lags: `lag_1`, `lag_2`, `lag_48`;
- médias móveis: `roll_mean_6`, `roll_mean_48`.

**Implementado em:** `montar_features(df)`.

---

## Skill 6 — Forecast híbrido Linear + CatBoost residual

**Objetivo:** combinar interpretabilidade linear com correção não-linear.

**Quando usar:** previsão rápida e robusta sem stack de séries complexa.

**Pipeline:**

1. gerar features;
2. separar treino/teste pelo horizonte final;
3. treinar `LinearRegression`;
4. calcular resíduo `y - pred_linear`;
5. treinar `CatBoostRegressor` no resíduo;
6. somar baseline + correção;
7. aplicar `clip` para evitar geração negativa;
8. calcular MAE e ganho percentual;
9. expor importância das features.

**Implementado em:** `treinar_hibrido(df, horizonte)` e Abas 2/6.

---

## Skill 7 — Banda de incerteza operacional P10/P90

**Objetivo:** mostrar faixa de incerteza simples para previsão.

**Quando usar:** visualização executiva de previsão onde uma estimativa rápida é suficiente.

**Técnica:**

1. calcular resíduo final in-sample;
2. estimar `sigma = std(residuo)`;
3. definir `p10 = pred - 1.28*sigma`;
4. definir `p90 = pred + 1.28*sigma`;
5. plotar como área preenchida.

**Limitação:** não é calibração probabilística formal.

**Implementado em:** `treinar_hibrido()` e gráficos das Abas 2/6.

---

## Skill 8 — Detecção de anomalias com IsolationForest

**Objetivo:** encontrar eventos atípicos em séries operacionais sem rótulo.

**Quando usar:** corte inesperado, queda anormal, gaps elevados ou comportamento fora do padrão.

**Pipeline:**

1. calcular gap entre referência e geração;
2. montar matriz com geração, referência, gap, hora e disponibilidade;
3. treinar `IsolationForest`;
4. marcar anomalias com `fit_predict(X) == -1`;
5. usar `-score_samples(X)` como severidade;
6. exibir série, heatmap e tabela.

**Implementado em:** `detectar_anomalias()` e Aba 3.

---

## Skill 9 — Motor de notícias com Google News RSS e ranking

**Objetivo:** relacionar notícias externas a um ativo específico.

**Quando usar:** inteligência competitiva, regulação, eventos operacionais e monitoramento de contexto.

**Pipeline:**

1. limpar nome do ativo;
2. criar várias queries direcionadas;
3. consultar Google News RSS;
4. parsear XML;
5. deduplicar links;
6. normalizar texto sem acentos;
7. pontuar hits de nome, contexto, município e UF;
8. dar bônus para nome completo + contexto;
9. penalizar homônimos sem contexto;
10. filtrar por relevância mínima.

**Implementado em:** `_gnews()` e `buscar_noticias_relacionadas()`.

---

## Skill 10 — JupyterLite Analyst Lab dentro do Streamlit

**Objetivo:** gerar um notebook EDA executável no navegador a partir do ativo selecionado.

**Quando usar:** quando o dashboard precisa dar liberdade para analistas investigarem dados manualmente.

**Pipeline:**

1. receber ativo e metadados;
2. baixar série temporal;
3. calcular colunas auxiliares (`gap`, `corte`, flags);
4. exportar CSV;
5. gravar metadados JSON;
6. criar notebook com `nbformat`;
7. executar `jupyter lite init`;
8. executar `jupyter lite build`;
9. subir `jupyter lite serve` se a porta não estiver aberta;
10. embedar URL via iframe;
11. liberar download de CSV e notebook.

**Implementado em:** `_make_eda_notebook()`, `preparar_jupyterlite_lab()`, `_ensure_jupyterlite_server()` e Aba 7.

---

## Skill 11 — Cache unitário por granularidade real

**Objetivo:** evitar que análises por unidade usem dados agregados como se fossem unitários.

**Quando usar:** datasets com múltiplas granularidades misturadas.

**Pipeline:**

1. escolher chave unitária confiável (`sk_usina`);
2. fazer join com dimensão do ativo;
3. filtrar entidades reais e coordenadas válidas;
4. agregar métricas por chave unitária;
5. salvar cache Parquet;
6. consumir cache no dashboard;
7. fazer drill-down por unidade.

**Implementado em:** `build_unit_cache.py` e Aba 6.

---

## Skill 12 — Notebook EDA template para dados operacionais

**Objetivo:** entregar um notebook padrão para investigação manual.

**Células recomendadas:**

1. contexto e metadados;
2. setup de bibliotecas;
3. carga e ordenação da série;
4. resumo executivo;
5. gráfico geração x referência x corte;
6. perfil horário;
7. quebra por razão/origem;
8. outliers por z-score;
9. hipóteses de investigação.

**Implementado em:** notebook gerado pela Aba 7 e exemplo em `stramlit/jupyterlite_content/eda_conjunto_eolico_kairos.ipynb`.

# Modelos e Algoritmos

## 1. Feature Engineering

Função: `montar_features(df)`

Entrada esperada:

- `din_instante`
- `val_geracao`
- `val_geracaoreferencia`
- `val_disponibilidade`
- `cod_razaorestricao`

Features criadas:

| Feature | Tipo | Objetivo |
|---|---|---|
| `hora` | temporal | hora decimal do dia |
| `dow` | temporal | dia da semana |
| `mes` | temporal | mês |
| `t_idx` | tendência | ordem do ponto na série |
| `sin_d1/cos_d1` | Fourier | ciclo diário primário |
| `sin_d2/cos_d2` | Fourier | ciclo diário harmônico 2 |
| `sin_d3/cos_d3` | Fourier | ciclo diário harmônico 3 |
| `sin_w/cos_w` | Fourier | ciclo semanal |
| `disp` | operacional | disponibilidade |
| `ref` | operacional | referência de geração |
| `restrito` | binária | evento com restrição |
| `razao_ene` | binária | restrição energética |
| `lag_1`, `lag_2`, `lag_48` | autoregressiva | memória curta e diária |
| `roll_mean_6` | rolling | média curta |
| `roll_mean_48` | rolling | média diária |

Preenchimento:

```python
ffill/bfill/fillna(0)
```

## 2. Modelo híbrido Linear + CatBoost

Função: `treinar_hibrido(df, horizonte)`

Objetivo: substituir Prophet por um baseline interpretável + corretor não-linear.

### Passo a passo

1. Cria features com `montar_features`.
2. Separa treino e teste pelo horizonte.
3. Treina `LinearRegression`.
4. Calcula predição linear in-sample.
5. Calcula resíduo:

```python
resid = y_real - y_linear
```

6. Treina `CatBoostRegressor` no resíduo.
7. Predição final:

```python
pred_hibrido = clip(pred_linear + pred_catboost_residuo, 0, None)
```

### Hiperparâmetros CatBoost

```python
CatBoostRegressor(
    iterations=400,
    depth=6,
    learning_rate=0.05,
    loss_function="RMSE",
    verbose=False,
    random_seed=42,
    l2_leaf_reg=3.0,
)
```

### Incerteza

A banda P10/P90 é aproximada com desvio padrão do resíduo final in-sample:

```python
sigma = std(y_train - pred_train_hibrido)
p10 = pred_hibrido - 1.28 * sigma
p90 = pred_hibrido + 1.28 * sigma
```

### Métricas

```python
mae_base = mean(abs(real - pred_linear))
mae_hibrido = mean(abs(real - pred_hibrido))
melhora_pct = (1 - mae_hibrido / mae_base) * 100
```

### Saídas

- histórico de treino
- real no horizonte
- baseline linear
- híbrido final
- P10/P90
- MAE base
- MAE híbrido
- ganho percentual
- importância das features do CatBoost

## 3. Detecção de anomalias

Função: `detectar_anomalias(df, contaminacao=0.04)`

Modelo:

```python
IsolationForest(contamination=contaminacao, random_state=42, n_estimators=200)
```

Features:

| Feature | Objetivo |
|---|---|
| `val_geracao` | geração observada |
| `val_geracaoreferencia` | referência |
| `gap` | referência - geração |
| `hora` | comportamento horário |
| `disp` | disponibilidade |

Saídas:

```python
anomalia: bool
score_anom: -score_samples
```

Interpretação: maior `score_anom` = mais anômalo.

## 4. Health Score

Aplicado em frota e unidades.

Formula geral:

```python
score = 100 * (
    0.50 * (1 - norm(pct_corte)) +
    0.20 * (1 - norm(log1p(perda_reais))) +
    0.30 * norm(fator_capacidade)
)
```

Peso das dimensões:

| Dimensão | Peso | Direção |
|---|---:|---|
| baixo corte | 50% | menor é melhor |
| baixa perda | 20% | menor é melhor |
| fator de capacidade | 30% | maior é melhor |

## 5. Motor de notícias

Função: `buscar_noticias_relacionadas`

Etapas:

1. Limpa nome da usina removendo prefixos (`CONJ.`, `CONJUNTO`, `EÓLICO`, etc.).
2. Cria múltiplas queries para Google News RSS.
3. Deduplica por link.
4. Normaliza texto sem acento.
5. Calcula score de relevância por:
   - match de nome;
   - contexto energético (`eolic`, `curtailment`, `ons`, `aneel`, etc.);
   - município/UF;
   - bônus para nome completo + contexto energético;
   - penalidade para homônimos sem contexto.
6. Mantém apenas relevância >= 8.

## 6. JupyterLite Analyst Lab

Funções:

- `_make_eda_notebook`
- `preparar_jupyterlite_lab`
- `_ensure_jupyterlite_server`

O notebook gerado já contém análise manual e usa Pyodide no navegador.

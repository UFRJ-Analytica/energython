# Operação e extensão do app Streamlit

Este documento resume como operar, validar e estender o app `stramlit/app.py`.

## Execução local

A partir da raiz do repositório:

```bash
cd stramlit
source venv/bin/activate
streamlit run app.py --server.headless true --server.port 8765
```

O JupyterLite, quando gerado pela Aba 7, é servido em:

```text
http://localhost:8766/
```

## Dependências

Arquivo: `stramlit/requirements.txt`.

Principais grupos:

| Grupo | Pacotes |
|---|---|
| UI | `streamlit`, `plotly` |
| Dados | `duckdb`, `pandas`, `numpy` |
| ML | `scikit-learn`, `catboost` |
| Notebook/Lab | `jupyterlite`, `jupyterlite-core`, `jupyterlite-pyodide-kernel`, `nbformat` |
| Visualização notebook | `matplotlib` |

Observação: `prophet` e `lightgbm` aparecem nas dependências, mas o fluxo atual do `app.py` usa o híbrido Linear + CatBoost.

## Caches e artefatos

| Artefato | Origem | Uso |
|---|---|---|
| `.cache_frota_eolica.parquet` | `carregar_frota()` | Evita varrer o mart inteiro a cada carga. |
| `.cache_unidades_eolica.parquet` | `build_unit_cache.py` | Alimenta Aba 6. |
| `catboost_info/` | CatBoost | Logs/artefatos automáticos de treinamento. |
| `jupyterlite_content/` | Aba 7 | Conteúdo-fonte do Analyst Lab. |
| `jupyterlite_site/` | `jupyter lite build` | Site estático servido no navegador. |

## Regerar cache de unidades

```bash
cd stramlit
source venv/bin/activate
python build_unit_cache.py
```

Esse script consulta `dw.fato_restricao_coff`, junta com `dw.dim_usina`, calcula métricas unitárias e salva `.cache_unidades_eolica.parquet`.

## Validações recomendadas

### Sintaxe Python

```bash
cd stramlit
python -m py_compile app.py build_unit_cache.py
```

### Smoke test Streamlit

```bash
cd stramlit
streamlit run app.py --server.headless true --server.port 8765
```

Depois testar:

```bash
curl -I http://localhost:8765
```

### JupyterLite

Gerar pela Aba 7 e testar:

```bash
curl -I http://localhost:8766/
```

## Como criar nova aba

1. Definir objetivo e fonte de dados.
2. Criar função de carga cacheada se a consulta for cara.
3. Reutilizar helpers (`kpi`, `fmt_reais`, `fmt_mwh`).
4. Adicionar o título da aba em `st.tabs([...])`.
5. Implementar o bloco `with tabX:`.
6. Reutilizar `st.session_state.usina_sel` se houver seleção por usina.
7. Preferir Plotly para manter padrão visual.
8. Documentar a nova aba em `docs/curtailiq/abas.md`.

## Como adicionar novo modelo

1. Criar função pura com entrada `DataFrame` e parâmetros explícitos.
2. Usar `@st.cache_data` se o treino for caro e determinístico.
3. Reutilizar `montar_features()` quando possível.
4. Separar treino/teste temporalmente, sem shuffle.
5. Expor métricas comparáveis: MAE, ganho, score ou erro percentual.
6. Exibir resultados e limitações na UI.
7. Documentar em `docs/curtailiq/modelos-e-algoritmos.md`.

## Troubleshooting

| Problema | Possível causa | Ação |
|---|---|---|
| App para em “carregando frota” | DW indisponível ou cache ausente | Verificar conexão, gerar/usar cache. |
| Aba 6 mostra erro de cache | `.cache_unidades_eolica.parquet` ausente | Rodar `python build_unit_cache.py`. |
| Previsão não roda | Histórico insuficiente | Aumentar pontos históricos ou reduzir horizonte. |
| JupyterLite não abre | Porta 8766 ocupada ou build falhou | Verificar processo/porta e erro mostrado na Aba 7. |
| Notícias não aparecem | RSS sem resultados relevantes | Usar termos extras ou outra usina. |
| Mapas com coordenada aproximada | Falha de match por nome | Revisar `dim_usina` e normalização de nomes. |

## Melhorias operacionais recomendadas

- mover credenciais para `st.secrets` ou variáveis de ambiente;
- separar `app.py` em módulos (`data`, `features`, `models`, `ui`, `lab`);
- adicionar botão de refresh para caches locais;
- registrar data/hora de geração dos caches;
- remover dependências não usadas ou justificar seu uso futuro;
- evitar rebuild completo do JupyterLite se CSV/notebook não mudaram.

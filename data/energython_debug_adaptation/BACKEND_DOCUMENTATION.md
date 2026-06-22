# Documentação Backend — DEBUG Energython

## Objetivo

Adicionar uma camada DEBUG no backend sem alterar o contrato existente das rotas de produção.

## Arquivos propostos

| Arquivo nesta pasta | Destino sugerido no backend real | Papel |
|---|---|---|
| `backend/debug_schemas.py` | `backend/app/schemas/debug.py` | Modelos Pydantic das respostas DEBUG. |
| `backend/debug_service.py` | `backend/app/services/debug_service.py` | Métricas, score, anomalias e forecast experimental. |
| `backend/debug_router.py` | `backend/app/routers/debug.py` | Endpoints `/api/debug/*`. |
| `backend/postgres_repo_dw_queries.py` | consulta de apoio para `PostgresRepository` | SQLs com aliases do contrato atual. |

## Endpoints implementados

Todos já registrados em `backend/app/routers/debug.py` e expostos via `app.include_router(debug_router)`.

| Endpoint | Aba Streamlit equivalente | Objetivo |
|---|---|---|
| `GET /api/debug/health-dados` | — | Diagnóstico de backend, repositório e amostra de usinas. |
| `GET /api/debug/control-tower` | 1. Control Tower | KPIs de frota + ranking por Health Score. |
| `GET /api/debug/ranking` | 5. Ranking Top Tier | Melhores e piores usinas por score. |
| `GET /api/debug/unidades` | 6. Unidades Individuais | Diagnóstico por granularidade (ponte para `sk_usina` real). |
| `GET /api/debug/usinas/{usina_id}` | 2. Detalhe & Previsão | Ficha, KPIs e série amostral da usina. |
| `GET /api/debug/usinas/{usina_id}/anomalias` | 3. Anomalias | IsolationForest com fallback z-score. |
| `GET /api/debug/usinas/{usina_id}/forecast` | 2. Detalhe & Previsão | Forecast híbrido Linear + GradientBoosting residual. |
| `GET /api/debug/usinas/{usina_id}/noticias` | 4. Inteligência (Notícias) | Google News RSS com ranking de relevância. |
| `GET /api/debug/usinas/{usina_id}/lab-template` | 7. Analyst Lab | Template de notebook EDA + preview CSV. |

### Parâmetros de query comuns

| Parâmetro | Endpoints | Default | Observação |
|---|---|---|---|
| `limit` | health-dados, control-tower, ranking, unidades | 5/20/30 | tamanho da amostra/ranking |
| `dias` | control-tower, ranking, unidades, usinas, anomalias, forecast | 90/120 | janela histórica |
| `limit_serie` | usinas, lab-template | 200 | pontos da série amostral |
| `horizonte` | forecast | 48 | passos previstos |
| `termos_extra` | noticias | "" | termos extras de busca |
| `max_itens` | noticias | 12 | máximo de notícias |

## Técnica adaptada do Streamlit

| Streamlit | Backend DEBUG Energython |
|---|---|
| `carregar_frota()` | `DebugService.control_tower()` |
| Ranking Top Tier | `DebugService.ranking()` |
| Unidades Individuais | `DebugService.unidades()` |
| `carregar_serie()` | `DebugService.detalhe_usina()` |
| `detectar_anomalias()` | `DebugService.anomalias()` |
| `treinar_hibrido()` | `DebugService.forecast()` |
| `buscar_noticias_relacionadas()` | `DebugService.noticias()` |
| `preparar_jupyterlite_lab()` | `DebugService.lab_template()` |
| Health Score | `DebugService._score_from_metrics()` |

## Dependências

O backend atual já possui `pandas` e `scikit-learn` em `requirements.txt`. Por isso:

- anomalias usam `IsolationForest` quando disponível;
- forecast usa `LinearRegression` + `GradientBoostingRegressor`, ambos de `scikit-learn`;
- não exige `catboost` para não alterar dependências do projeto.

## Registro do router (já aplicado)

Em `backend/app/main.py`:

```python
from app.routers.debug import router as debug_router

app.include_router(debug_router)
```

## Segurança funcional

- DEBUG é isolado em `/api/debug`.
- Não substitui rotas `/api/usinas`, `/api/financeiro`, `/api/regulatorio`.
- Não altera schemas existentes.
- Deve ser acessado pelo frontend apenas após clique no botão DEBUG.

## Observação sobre leitura do banco

A alteração de leitura do banco deve ocorrer em `PostgresRepository`, mantendo os aliases esperados. O serviço DEBUG usa o repositório existente e, portanto, se beneficia da nova leitura sem duplicar credenciais.

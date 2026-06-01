# Pipeline de Dados e Machine Learning (MVP Curtailment)

Esta pasta (`data_ml`) é um workspace de analytics/data-science (offline), não o caminho crítico de runtime da API FastAPI.

Objetivo:
- apoiar exploração de dados, treino e inspeção de modelos;
- gerar artefatos auxiliares (cache CSV, visualizações streamlit);
- sem acoplar ingestão ao backend de produto.

## Componentes

1) `data_extraction.py`
- utilitário OFFLINE de extração e cache.
- conecta no Postgres via `DATABASE_URL` do ambiente.
- gera `temp_cache/flat_dados_eolica.csv`, `temp_cache/flat_dados_solar.csv`, `temp_cache/ccee_cache.csv`.

2) `models.py`
- classes de inferência analítica (inclui `AdvancedCurtailmentPredictor`).
- voltado para exploração/explicabilidade/diagnóstico de modelo.

3) `dashboard.py`
- dashboard Streamlit para análise local.
- consome cache local quando disponível; caso contrário consulta banco via `DATABASE_URL`.

## Boundary (importante)

- Este diretório NÃO substitui o pipeline oficial de dados.
- Ingestão/normalização pesada deve permanecer no pipeline de dados (camada gold/public).
- O backend FastAPI deve consumir dados prontos dos repositórios, sem depender de CSV local deste diretório.

## Configuração

Use `backend/.env` (ou variável de ambiente) com:

- `DATABASE_URL=postgresql+psycopg://...`

Nunca hardcode credenciais nos scripts.

## Execução local

1. Gerar cache:

```bash
cd backend/models_ml/data_ml
DATABASE_URL='postgresql+psycopg://user:pass@host:port/db' python data_extraction.py
```

2. Subir dashboard:

```bash
cd backend/models_ml/data_ml
streamlit run dashboard.py
```

## Observações

- O dashboard é ferramenta de análise local; não endpoint de produção.
- Se faltar dependência (streamlit/plotly etc.), instale no ambiente de DS, não no runtime mínimo da API.

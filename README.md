# Energython - CurtailIQ Backend MVP

Repositório do projeto Energython com foco inicial no backend da solução CurtailIQ.

## Escopo atual
- Backend FastAPI organizado em camadas (routers -> services -> repositories).
- Pipeline de consumo de dados via repositório:
  - `PostgresRepository` (camada `gold` no PostgreSQL)
  - `MockRepository` (CSVs em `backend/data/samples`)
- Implementação dos elos:
  - Elo 2 (financeiro + simulação BESS)
  - Elo 3 (regulatório com agentes e RAG base)
- Elo 1 mantido como stub para evolução posterior.

## Estrutura
- `backend/` contém todo o código e artefatos do escopo backend.
- Documentos de contexto do negócio e especificação podem ficar na raiz durante a fase de definição.

## Como executar localmente
```bash
cd backend
python -m unittest discover -s tests -p "test_*"
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`

# Energython Debug Adaptation

Pacote de implementação **isolado dentro de `data/`** para adaptar as técnicas documentadas do protótipo `stramlit/app.py` ao projeto Energython, sem alterar o código original agora.

## Objetivo

Criar uma área DEBUG acessível por botão na tela principal, com diagnósticos de dados, métricas de curtailment, score, anomalias e forecast experimental, mantendo o fluxo principal intacto.

## Regra principal

> Fora desta pasta, a única alteração planejada no app real deve ser leitura de banco/SQL/aliases no repositório e a inclusão controlada do botão DEBUG/rota DEBUG. Nenhuma variável pública, schema ou contrato existente deve ser renomeado.

## Estrutura

```text
data/energython_debug_adaptation/
├── README.md
├── TASK_DIAGRAM.md
├── DATABASE_READING_MAP.md
├── BACKEND_DOCUMENTATION.md
├── FRONTEND_DOCUMENTATION.md
├── IMPLEMENTATION_CHECKLIST.md
├── backend/
│   ├── debug_schemas.py
│   ├── debug_service.py
│   ├── debug_router.py
│   └── postgres_repo_dw_queries.py
└── frontend/
    ├── DebugPage.tsx
    ├── debugApi.ts
    ├── useDebug.ts
    ├── types_debug.ts
    ├── homeDebugButton.snippet.tsx
    └── routerDebugRoute.snippet.tsx
```

## Como usar este pacote

### Backend

1. Revisar `backend/postgres_repo_dw_queries.py`.
2. Copiar somente os SQLs/aliases necessários para `backend/app/repositories/postgres_repo.py`.
3. Se for habilitar DEBUG, copiar:
   - `backend/debug_schemas.py` para `backend/app/schemas/debug.py`;
   - `backend/debug_service.py` para `backend/app/services/debug_service.py`;
   - `backend/debug_router.py` para `backend/app/routers/debug.py`.
4. Registrar o router em `backend/app/main.py`.

### Frontend

1. Copiar `frontend/types_debug.ts` para `front/src/types/debug.ts`.
2. Copiar `frontend/debugApi.ts` para `front/src/api/debug.ts`.
3. Copiar `frontend/useDebug.ts` para `front/src/hooks/useDebug.ts`.
4. Copiar `frontend/DebugPage.tsx` para `front/src/pages/Debug/index.tsx`.
5. Aplicar os snippets:
   - `homeDebugButton.snippet.tsx` em `front/src/pages/Home/index.tsx`;
   - `routerDebugRoute.snippet.tsx` em `front/src/router.tsx`.

## Escopo das telas DEBUG

As telas DEBUG devem mostrar:

- status da fonte de dados;
- amostras de usinas;
- métricas agregadas no padrão Control Tower;
- Health Score experimental;
- eventos de curtailment;
- anomalias por IsolationForest/fallback z-score;
- forecast experimental Linear + corretor não-linear quando dependências existirem.

## Importante

Este pacote não substitui o app Energython. Ele é um kit documentado e isolado para implementação controlada.

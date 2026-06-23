# Documentação Frontend — DEBUG Energython

## Objetivo

Adicionar uma tela DEBUG ao frontend React, acessível somente pelo botão DEBUG na Home.

## Arquivos propostos

| Arquivo nesta pasta | Destino sugerido no front real | Papel |
|---|---|---|
| `frontend/types_debug.ts` | `front/src/types/debug.ts` | Tipos TypeScript das respostas DEBUG. |
| `frontend/debugApi.ts` | `front/src/api/debug.ts` | Chamadas HTTP para `/api/debug/*`. |
| `frontend/useDebug.ts` | `front/src/hooks/useDebug.ts` | Hooks React Query. |
| `frontend/DebugPage.tsx` | `front/src/pages/Debug/index.tsx` | Tela DEBUG. |
| `frontend/homeDebugButton.snippet.tsx` | aplicar em `front/src/pages/Home/index.tsx` | Botão DEBUG. |
| `frontend/routerDebugRoute.snippet.tsx` | aplicar em `front/src/router.tsx` | Rota `/debug`. |

## Proteção da tela

A tela DEBUG usa `sessionStorage`:

```text
1. Botão DEBUG na Home grava: energython.debugAccess=true
2. Botão navega para /debug
3. DebugPage verifica a flag
4. Sem flag, redireciona para /
```

Isso não é autenticação de segurança; é só uma proteção de UX para garantir que a tela DEBUG só apareça pelo botão.

## Integração com API

A API base continua sendo a constante existente:

```ts
API_BASE = "/api"
```

Chamadas implementadas em `front/src/api/debug.ts` (hooks em `front/src/hooks/useDebug.ts`):

```text
GET /api/debug/health-dados
GET /api/debug/control-tower
GET /api/debug/ranking
GET /api/debug/unidades
GET /api/debug/usinas/{id}
GET /api/debug/usinas/{id}/anomalias
GET /api/debug/usinas/{id}/forecast
GET /api/debug/usinas/{id}/noticias
GET /api/debug/usinas/{id}/lab-template
```

## Abas da página DEBUG

A página `front/src/pages/Debug/index.tsx` usa `Tabs` (shadcn) replicando as 7 abas do Streamlit:

| Aba | Conteúdo | Hooks |
|---|---|---|
| 1. Control Tower | KPIs de frota + tabela de ranking | `useDebugHealthDados`, `useDebugControlTower` |
| 2. Detalhe & Previsão | Ficha da usina + forecast híbrido | `useDebugUsina`, `useDebugForecast` |
| 3. Anomalias | Eventos anômalos (IsolationForest/z-score) | `useDebugAnomalias` |
| 4. Notícias | Notícias relacionadas à usina | `useDebugNoticias` |
| 5. Ranking | Melhores e piores usinas | `useDebugRanking` |
| 6. Unidades | Granularidade unitária (ponte) | `useDebugUnidades` |
| 7. Analyst Lab | Template de notebook + preview CSV | `useDebugLabTemplate` |

A usina ativa é escolhida clicando em "Selecionar" em qualquer tabela; o estado fica em `selectedId` (com fallback no topo do ranking).

## Regra visual

A Home normal e o fluxo `/usinas` devem continuar iguais. A única mudança visível na Home é o botão DEBUG secundário.

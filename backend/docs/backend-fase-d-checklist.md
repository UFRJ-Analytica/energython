# Fase D — Checklist de qualidade e prontidão (backend)

Status: concluída nesta iteração.

## 1) Padrão de erros de API
- Formato padronizado: `{"detail": {"code": "...", "detail": "..."}}`
- Coberto em rotas de usinas, financeiro e regulatório.
- Testes de contrato 404/422 presentes.

## 2) Paginação e filtros
- `GET /api/usinas` com `limit` e `offset`.
- Metadados de paginação no payload: `total_count`, `limit`, `offset`, `items`.
- Filtros suportados: `fonte`, `submercado`.
- Teste de filtro de `submercado=NE` adicionado.

## 3) Health/Readiness
- `GET /health`: liveness simples (`status=ok`).
- `GET /readiness`: readiness com checks de dependência.
  - Em `mock`: `checks.mock_repository=ok`.
  - Em `postgres`: tentativa de `SELECT 1`.
    - sucesso: `status=ready`, `checks.db_connection=ok`
    - falha: `status=not_ready`, `checks.db_connection=error`
    - sem driver/engine: `status=not_ready`, `driver_or_engine_unavailable`

## 4) Logging estruturado
- Middleware HTTP com log JSON por request:
  - método, path, status, elapsed_ms.
- Pronto para observabilidade básica no ambiente de execução.

## 5) Parametrização regulatória
- Regras de elegibilidade por variável de ambiente:
  - `ELEGIVEL_CONFIABILIDADE`
  - `ELEGIVEL_INDISPONIBILIDADE_EXTERNA`
  - `ELEGIVEL_ENERGETICO`
  - `ELEGIVEL_INDEFINIDO`
- `.env.example` atualizado.

## 6) Prontidão para integração futura com frontend
- Contratos de resposta estáveis nos endpoints principais.
- Endpoint agregador `/api/usinas/{usina_id}/resumo` já disponível.
- Recomendação para próxima etapa (frontend):
  1. Consumir `/docs` para geração inicial de client.
  2. Começar por `/api/usinas` e `/api/usinas/{id}/resumo`.
  3. Tratar `status=not_ready` em `/readiness` como bloqueio operacional.
  4. Exibir campos de qualidade de dados (`qualidade_dados`) e classificação (`qualidade_classificacao`).

## 7) Validação realizada
- Suíte unitária/smoke completa executada com sucesso.
- Resultado atual esperado: todos os testes passando.

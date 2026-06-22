# Checklist de implementação

## Antes de alterar o app real

- [ ] Confirmar qual é o banco novo e schema definitivo.
- [ ] Confirmar identificador estável de usina (`usina_id`).
- [ ] Confirmar se `dw.mart_eolica` possui `id_ons` ou se será necessário usar `nom_usina` como chave.
- [ ] Confirmar tabela de PLD atual.
- [ ] Confirmar se o front deve continuar com filtro `solar/eolica` ou se DEBUG será só eólico.

## Backend — leitura do banco

- [ ] Abrir `backend/app/repositories/postgres_repo.py`.
- [ ] Trocar SQL de `get_usina` mantendo aliases.
- [ ] Trocar SQL de `get_constrained_off` mantendo aliases.
- [ ] Trocar SQL de `get_geracao_horaria` mantendo aliases.
- [ ] Trocar SQL de `get_disponibilidade_usina` mantendo aliases.
- [ ] Trocar SQL de `get_pld` se o PLD mudou.
- [ ] Não alterar `FinanceiroService`.
- [ ] Não alterar `RegulatorioService`.
- [ ] Não alterar schemas existentes.

## Backend — DEBUG

- [ ] Copiar `debug_schemas.py` para `backend/app/schemas/debug.py`.
- [ ] Copiar `debug_service.py` para `backend/app/services/debug_service.py`.
- [ ] Copiar `debug_router.py` para `backend/app/routers/debug.py`.
- [ ] Registrar router no `main.py`.
- [ ] Testar `/api/debug/health-dados`.
- [ ] Testar `/api/debug/control-tower`.
- [ ] Testar `/api/debug/usinas/{usina_id}`.

## Frontend — DEBUG

- [ ] Copiar `types_debug.ts` para `front/src/types/debug.ts`.
- [ ] Copiar `debugApi.ts` para `front/src/api/debug.ts`.
- [ ] Copiar `useDebug.ts` para `front/src/hooks/useDebug.ts`.
- [ ] Copiar `DebugPage.tsx` para `front/src/pages/Debug/index.tsx`.
- [ ] Aplicar snippet de rota em `front/src/router.tsx`.
- [ ] Aplicar snippet de botão em `front/src/pages/Home/index.tsx`.
- [ ] Testar clique no botão DEBUG.
- [ ] Testar acesso direto a `/debug` sem flag.

## Validação

- [ ] `cd backend && python -m unittest discover -s tests -p "test_*"`.
- [ ] `cd front && npm run typecheck`.
- [ ] `cd front && npm run build`.
- [ ] Validar Home normal.
- [ ] Validar Portfolio normal.
- [ ] Validar detalhe de usina.
- [ ] Validar rotas financeiro/regulatório.

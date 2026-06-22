# Implementação DEBUG aplicada ao Energython

Este documento registra a adaptação inicial das funcionalidades do protótipo Streamlit para o projeto Energython.

## Escopo aplicado

Foram criados arquivos reais no backend e frontend para disponibilizar telas DEBUG isoladas, acessíveis pelo botão `DEBUG` na Home.

## Backend aplicado

Arquivos criados:

```text
backend/app/schemas/debug.py
backend/app/services/debug_service.py
backend/app/routers/debug.py
```

Arquivo alterado:

```text
backend/app/main.py
```

Alteração no `main.py`:

```python
from app.routers.debug import router as debug_router
app.include_router(debug_router)
```

## Endpoints DEBUG disponíveis

```text
GET /api/debug/health-dados
GET /api/debug/control-tower
GET /api/debug/ranking
GET /api/debug/unidades
GET /api/debug/usinas/{usina_id}
GET /api/debug/usinas/{usina_id}/anomalias
GET /api/debug/usinas/{usina_id}/forecast
GET /api/debug/usinas/{usina_id}/noticias
GET /api/debug/usinas/{usina_id}/lab-template
```

## Funcionalidades Streamlit adaptadas

| Aba Streamlit | Adaptação Energython DEBUG |
|---|---|
| 1. Control Tower | `/api/debug/control-tower` + aba `Control Tower` no front |
| 2. Detalhe & Previsão | `/api/debug/usinas/{id}` e `/forecast` + aba `Detalhe & Previsão` |
| 3. Anomalias | `/api/debug/usinas/{id}/anomalias` + aba `Anomalias` |
| 4. Notícias | `/api/debug/usinas/{id}/noticias` + aba `Notícias` |
| 5. Ranking Top Tier | `/api/debug/ranking` + aba `Ranking` |
| 6. Unidades Individuais | `/api/debug/unidades` + aba `Unidades` |
| 7. Analyst Lab | `/api/debug/usinas/{id}/lab-template` + aba `Analyst Lab` |

## Frontend aplicado

Arquivos criados:

```text
front/src/types/debug.ts
front/src/api/debug.ts
front/src/hooks/useDebug.ts
front/src/pages/Debug/index.tsx
```

Arquivos alterados:

```text
front/src/router.tsx
front/src/pages/Home/index.tsx
```

### Botão DEBUG

Na Home, foi adicionado um botão `DEBUG` ao lado do botão `Selecione a usina`.

Fluxo:

```text
1. usuário clica DEBUG
2. sessionStorage.energython.debugAccess = true
3. navega para /debug
4. DebugPage verifica a flag
5. sem flag, /debug redireciona para /
```

## Observações importantes

- As rotas normais do Energython não foram substituídas.
- A lógica principal de financeiro/regulatório/curtailment continua intacta.
- A camada DEBUG usa o repositório atual (`get_repo`) para ler dados.
- A alteração real da leitura do banco ainda deve ser feita em `PostgresRepository`, mantendo aliases e contratos existentes.
- O endpoint de unidades é uma ponte de teste: hoje usa a granularidade disponível em `list_usinas`; para `sk_usina` real, conectar `dw.fato_restricao_coff`.
- O Analyst Lab retorna template JSON/CSV preview, não sobe JupyterLite dentro do backend FastAPI.

## Próximo passo de banco

Aplicar gradualmente as consultas de:

```text
data/energython_debug_adaptation/backend/postgres_repo_dw_queries.py
```

em:

```text
backend/app/repositories/postgres_repo.py
```

mantendo os aliases:

```text
usina_id, nome, fonte, potencia_mw, submercado,
latitude, longitude, timestamp,
geracao_verificada_mwh, geracao_referencia_mwh,
energia_restringida_mwh, cod_razaorestricao,
cod_origemrestricao, origem_restricao
```

## Validações executadas

### Backend

```bash
cd backend
.venv/bin/python -m py_compile app/schemas/debug.py app/services/debug_service.py app/routers/debug.py app/main.py
.venv/bin/python -m unittest discover -s tests -p 'test_*'
```

Resultado:

```text
Ran 62 tests in 2.920s
OK (skipped=1)
```

Smoke test dos endpoints DEBUG com `fastapi.testclient`:

```text
/api/debug/health-dados                              200
/api/debug/control-tower?limit=3                    200
/api/debug/ranking?limit=3                          200
/api/debug/unidades?limit=3                         200
/api/debug/usinas/USI_NE_001                        200
/api/debug/usinas/USI_NE_001/anomalias              200
/api/debug/usinas/USI_NE_001/forecast?horizonte=4   200
/api/debug/usinas/USI_NE_001/lab-template           200
```

### Frontend

```bash
cd front
npm run typecheck
npm run build
```

Resultado:

```text
tsc --noEmit: OK
vite build: ✓ built
```

## Atualização — banco novo + JupyterLite (aplicado)

### Carregamento de dados (única mudança no código de produção)

`backend/app/repositories/postgres_repo.py` — `get_constrained_off`, bloco COFF:

- Antes: `public.restricao_coff_eolica_usi` UNION `public.restricao_coff_fotovoltaica` (não existem na base nova).
- Agora: `public.restricao_coff_eolica_detail` (base `hacka-energinn` atualizada).
- Mapeamento mantendo os MESMOS aliases do contrato:
  - `geracao_verificada_mwh` ← `val_geracaoverificada * 0.5`
  - `geracao_referencia_mwh` ← `val_geracaoestimada * 0.5`
  - `energia_restringida_mwh` ← `GREATEST(estimada - verificada, 0) * 0.5`
  - `cod_razaorestricao` ← sentinela `'COFF'` (a tabela não traz razão)
  - chave da usina ← `nom_usina`
- Não foram alterados services, schemas, domain nem o fallback `gold.*`.

Referência SQL atualizada em `backend/postgres_repo_dw_queries.py` (geração, disponibilidade, despacho, COFF) para as tabelas reais: `geracao_usina_2`, `disponibilidade_usina`, `fator_capacidade_2`, `restricao_coff_eolica_detail`, `ccee_pld_horario`.

### JupyterLite (agora aparece)

- Backend: novos endpoints de download replicando o Analyst Lab do Streamlit:
  - `GET /api/debug/usinas/{id}/lab-template/notebook` → `.ipynb`
  - `GET /api/debug/usinas/{id}/lab-template/csv` → `.csv`
- Frontend: a aba **Analyst Lab** passou a exibir um `<iframe>` do JupyterLite (Pyodide) + botões de download do notebook/CSV + preview, em vez de só JSON.

### Validações

```text
backend py_compile: OK
backend unittest: Ran 62 tests — OK (skipped=1)
download notebook: 200 application/x-ipynb+json
download csv: 200 text/csv
front typecheck: OK
front /debug: 200 · proxy /api: 200
```

### Pendência conhecida

A `restricao_coff_eolica_detail` não traz `cod_razaorestricao` (ENE/CNF/REL). Com a sentinela `COFF`, a classificação regulatória cai em `indefinido`. Para recuperar a razão, mapear de outra fonte do banco novo quando disponível.

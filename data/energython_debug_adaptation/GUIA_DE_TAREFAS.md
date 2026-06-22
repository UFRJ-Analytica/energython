# Guia de Tarefas — Adaptação ao banco atualizado + JupyterLite

Este guia organiza, em ordem, as tarefas para (1) adaptar o carregamento de dados ao banco atualizado, (2) preservar a lógica/contratos atuais e (3) fazer o Analyst Lab (JupyterLite) aparecer de fato na tela DEBUG.

## Regra de ouro

> No backend, a ÚNICA coisa que pode mudar é a forma de carregar os dados do banco (SQL/aliases) em `backend/app/repositories/postgres_repo.py`. Nada de renomear variáveis, schemas, contratos ou lógica de serviço.

## Banco atualizado (referência: `data/ETL_CAMADA_PRATA_DOCUMENTACAO_COMPLETA.md` e `data/etl_unificado.py`)

Banco: `hacka-energinn` (PostgreSQL). Schema `public`. Tabelas reais:

| Tabela | Granularidade | Colunas-chave conhecidas |
|---|---|---|
| `geracao_usina_2` | horário | `din_instante, id_estado, nom_estado, nom_usina, nom_subsistema, nom_tipousina, nom_tipocombustivel, val_geracao` |
| `disponibilidade_usina` | horário | `din_instante, id_estado, nom_usina, nom_subsistema, val_potenciainstalada, val_dispoperacional, val_dispsincronizada` |
| `fator_capacidade_2` | horário | `din_instante, id_estado, nom_localizacao, nom_pontoconexao, nom_tipousina, val_geracaoprogramada, val_geracaoverificada, val_capacidadeinstalada, val_fatorcapacidade, val_latitudesecoletora, val_longitudesecoletora` |
| `restricao_coff_eolica_detail` | 30 min | `din_instante, id_estado, nom_usina, nom_conjuntousina, nom_modalidadeoperacao, val_ventoverificado, val_geracaoestimada, val_geracaoverificada` |
| `ccee_pld_horario` | horário | `submercado, dia, hora, mes_referencia, pld_hora` |

### Mudança crítica vs. código atual

| Código atual usava | Base atualizada tem | Ação |
|---|---|---|
| `public.restricao_coff_eolica_usi` | `public.restricao_coff_eolica_detail` | trocar tabela e colunas |
| `public.restricao_coff_fotovoltaica` | (não existe) | remover do UNION |
| `cod_razaorestricao` na COFF | (não existe na detail) | emitir sentinela `COFF` p/ não perder evento |
| `val_geracaoreferencia(final)` | `val_geracaoestimada` | referência = estimada |
| `val_geracao` (COFF) | `val_geracaoverificada` | geração verificada |

## Mapeamento contrato → banco atualizado (aliases NÃO mudam)

### Curtailment (`get_constrained_off`)

```sql
SELECT
  nom_usina                                   AS usina_id,
  din_instante::timestamp                     AS timestamp,
  'eolica'                                     AS fonte,
  val_geracaoverificada                       AS geracao_verificada_mwh,
  val_geracaoestimada                         AS geracao_referencia_mwh,
  GREATEST(val_geracaoestimada - val_geracaoverificada, 0) AS energia_restringida_mwh,
  'COFF'                                       AS cod_razaorestricao,   -- detail não traz razão
  NULL                                         AS cod_origemrestricao,
  <submercado normalizado>                     AS submercado
FROM public.restricao_coff_eolica_detail
WHERE nom_usina = :usina_id
  AND din_instante BETWEEN :inicio AND :fim
  AND GREATEST(val_geracaoestimada - val_geracaoverificada, 0) > 0
```

### Geração (`get_geracao_horaria`) → `geracao_usina_2`
### Disponibilidade (`get_disponibilidade_usina`) → `disponibilidade_usina`
### Despacho (`get_despacho_dessem`) → `fator_capacidade_2` (val_geracaoprogramada)
### PLD (`get_pld`) → `ccee_pld_horario`
### Usina (`get_usina`/`list_usinas`) → derivada de `fator_capacidade_2`/`geracao_usina_2`

## Ordem das tarefas

```mermaid
flowchart TD
    A[1. Confirmar tabelas/colunas no MD] --> B[2. Atualizar postgres_repo_dw_queries.py de referência]
    B --> C[3. Editar SOMENTE SQL de postgres_repo.py]
    C --> D[4. Manter aliases e fallbacks gold]
    D --> E[5. Validar import/compile do backend]
    E --> F[6. Fazer JupyterLite aparecer no front]
    F --> G[7. Backend lab-template + downloads]
    G --> H[8. Iframe JupyterLite na aba Analyst Lab]
    H --> I[9. typecheck + build front]
    I --> J[10. Rodar app e validar /debug]
```

### Tarefa 1 — Referência de SQL
- Atualizar `data/energython_debug_adaptation/backend/postgres_repo_dw_queries.py` com as tabelas reais.

### Tarefa 2 — Carregamento de dados (backend)
- Em `postgres_repo.py`, trocar APENAS os SQL de fallback `public.*`:
  - `get_constrained_off`: usar `restricao_coff_eolica_detail`.
  - `get_geracao_horaria`: priorizar `geracao_usina_2`.
  - `get_disponibilidade_usina`: `disponibilidade_usina`.
  - `get_despacho_dessem`: `fator_capacidade_2`.
  - `get_pld`: `ccee_pld_horario` (já compatível).
  - `get_usina`/`list_usinas`: derivar de `fator_capacidade_2`/`geracao_usina_2`.
- Manter tentativa `gold.*` no topo (não quebra se o gold existir).
- Não tocar em services, schemas, domain.

### Tarefa 3 — JupyterLite aparecer
- Causa de não aparecer hoje: a aba Analyst Lab só mostra JSON do notebook; não há iframe de JupyterLite.
- Adaptação da lógica do Streamlit (que faz build + serve + iframe):
  - Backend: `lab-template` já gera notebook + CSV (preview). Adicionar endpoints de download do `.ipynb` e `.csv`.
  - Frontend: na aba Analyst Lab, embutir `<iframe>` de uma instância JupyterLite (REPL/Lab) e oferecer download do notebook/CSV gerados, replicando o fluxo do Streamlit (gerar artefatos + abrir Lab).

### Tarefa 4 — Validação
- Backend: `python -m py_compile` dos arquivos alterados; subir `uvicorn`; checar `/api/debug/*`.
- Frontend: `npm run typecheck && npm run build`; abrir `/debug` e ver o Lab.

## Granularidade única — dw.mart_eolica + dw.mart_solar (APLICADO)

Os marts `dw.mart_eolica` e `dw.mart_solar` são **por usina, grão semi-horário (30min), colunas cruas** — exatamente a granularidade única para análise e treino dos modelos. Colunas relevantes:

```text
nom_usina, id_estado, nom_estado, id_subsistema, nom_subsistema, tipo,
potencia_mw, lat, lon, din_instante,
val_geracao, val_geracaoreferencia, val_geracaoreferenciafinal,
val_geracaolimitada, val_disponibilidade,
cod_razaorestricao, cod_origemrestricao, mes_ref
```

Aplicado no `PostgresRepository` (apenas carregamento de dados):

| Método novo | Fonte | Saída (aliases) |
|---|---|---|
| `list_usinas_mart(limit)` | `dw.mart_eolica` UNION `dw.mart_solar` | `usina_id, nome, fonte, potencia_mw, submercado, latitude, longitude, n_reg, ger_mwh, corte_mwh` |
| `get_serie_mart(usina_id, inicio, fim, limit)` | idem (filtra por usina) | `timestamp, fonte, geracao_mwh, geracao_referencia_mwh, energia_restringida_mwh, cod_razaorestricao, cod_origemrestricao` |

Conversões: MWh = MW/2 (grão 30min); corte = `GREATEST(referenciafinal|referencia − geracao, 0)/2`; submercado normalizado para `NE/N/S/SE`.

Ligação na camada DEBUG (`DebugService`):

- `unidades()` → usa `list_usinas_mart` (eólica + solar) quando disponível; KPIs incluem contagem Eólica/Solar; metadata `granularidade = usina_unica_30min`.
- `detalhe_usina()` / `anomalias()` / `forecast()` → usam `get_serie_mart` (grão único) quando disponível; metadata informa `granularidade`.
- Fallback automático para o caminho atual quando os marts não existem (ex.: `MockRepository`), sem quebrar.

> A ativação do caminho mart exige `DATA_BACKEND=postgres` + `DATABASE_URL`. Em mock, o endpoint indica o fallback na `observacao`.

## STATUS: conectado ao banco real (APLICADO)

O backend foi ligado ao Postgres `hacka-energinn` e os endpoints DEBUG usam os marts.

### .env aplicado (`backend/.env`)

```ini
DATA_BACKEND=postgres
DATABASE_URL=postgresql+psycopg://analytica:Data%26Dorme@177.7.55.100:32775/hacka-energinn
MVP_ONLY_NORDESTE=false
```

### Leitura completa do banco (126 objetos)

Schemas: `dw` (estrela/floco + marts), `public` (raw ONS/CCEE), `stg_ccee`.
Marts de granularidade única confirmados: **`dw.mart_eolica`** (9,47M linhas, 205 usinas, 2023→2026‑06‑20) e **`dw.mart_solar`** (2,57M linhas, 97 usinas, 2024‑04→2026‑06‑20). Grão 30min; `id_subsistema` já em NE/N/S/SE; `fonte` = EOLICA/FOTOVOLTAICA; sem lat/lon (potência parcial no próprio mart).

### Métodos de carregamento (PostgresRepository)

| Método | Fonte | Observação |
|---|---|---|
| `list_usinas_mart(limit)` | `dw.mart_eolica` ∪ `dw.mart_solar` | agrega por `nom_usina`; ger/corte/n_reg |
| `get_usina_mart(usina_id)` | idem | ficha única |
| `get_serie_mart(usina_id, ini, fim)` | idem | série 30min para modelos |

### DEBUG agora usa os marts como fonte primária

- `control_tower`/`ranking` → `list_usinas_mart` (métricas direto dos agregados, sem N queries).
- `detalhe`/`anomalias`/`forecast`/`lab` → `get_serie_mart` (grão único 30min); métricas calculadas da própria série (não passam pela validação top‑50).
- `unidades` → KPIs com contagem Eólica/Solar e `granularidade = usina_unica_30min`.

### Validações reais

```text
/readiness -> postgres ok
/api/debug/control-tower -> 200 (corte ~7,1M MWh top-5, eólica+solar)
/api/debug/unidades -> 200 (granularidade usina_unica_30min, "4 / 1" eól/solar)
/api/debug/usinas/{CONJ. SERRA DO MEL A} -> 200 (50 pts, gran=usina_unica_30min_mart)
/api/debug/.../anomalias -> 200 (isolation_forest, 80 anomalias)
/api/debug/.../forecast -> 200 (linear+gradient_boosting_residual, mae_hib≈11,77)
/api/debug/.../lab-template -> 200
unittest produção -> 62 OK (1 skip)
```

### Artefatos trazidos para `data/`

```text
data/models_artifacts/catboost_info/     # logs/artefatos do CatBoost (do Streamlit)
data/jupyter/jupyterlite_content/        # notebooks/CSVs/metadados do Analyst Lab
data/jupyter/jupyterlite_site/           # build estático do JupyterLite (73 MB)
```

### JupyterLite quase fullscreen

A aba **Analyst Lab** agora embute o iframe com `height: calc(100vh - 150px)` (quase a tela toda), controles compactos no topo e URL configurável por `VITE_JUPYTERLITE_URL` (default: demo pública; para self‑host, sirva `data/jupyter/jupyterlite_site`).

## Riscos / pendências
- A `restricao_coff_eolica_detail` não traz código de razão (ENE/CNF/REL). Sem isso, a classificação regulatória cai em `indefinido`. Próximo passo: mapear razão por outra fonte (ex.: tabela COFF com `cod_razaorestricao`, se existir no banco novo).
- Sem `.env` com `DATABASE_URL`, o backend roda em `mock`. A validação real do SQL exige `DATA_BACKEND=postgres` + credenciais.
- O identificador de usina passa a ser `nom_usina` (chave textual) na base atualizada, salvo se houver `id_ons`. Manter `usina_id` como alias.

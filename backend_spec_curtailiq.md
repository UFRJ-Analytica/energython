# Backend Spec — CurtailIQ API (FastAPI + Python)

> **Para o agente de código:** Este documento é a especificação completa do **backend** do projeto CurtailIQ, uma plataforma de inteligência de *curtailment* (corte de geração) para geradores renováveis no Brasil. Você trabalha **exclusivamente no backend**. Não cria frontend, não mexe no pipeline de dados (outra pessoa cuida), não sobe banco (outra pessoa cuida). Sua entrega são as **funcionalidades, funções, arquitetura, agentes de IA e endpoints FastAPI** que o frontend (React/JS) vai consumir.
>
> Leia este documento inteiro antes de escrever qualquer código. Onde houver instrução sobre a API da Anthropic ou datasets do ONS/CCEE, **confirme na documentação oficial** antes de fixar versões — esses detalhes mudam.

---

## 0. Contexto do produto (o que estamos construindo e por quê)

O ONS (Operador Nacional do Sistema) corta a geração de usinas eólicas e solares quando há excesso de oferta ou restrição de transmissão. Esse corte (*curtailment* / *constrained-off*) gerou ~R$6,5 bilhões de prejuízo aos geradores em 2025 (20,6% da geração renovável cortada). O gerador hoje não tem ferramenta que: (1) preveja o corte, (2) quantifique a perda financeira em tempo quase real, e (3) identifique quanto é ressarcível e monte o pleito.

O backend entrega três "elos" de valor:
- **Elo 1 — Físico/Preditivo:** modelo de ML que prevê risco de corte por usina (24–48h).
- **Elo 2 — Financeiro:** quantifica perda (MWh cortado × PLD), projeta exposição, e roda um business case de bateria (BESS).
- **Elo 3 — Regulatório:** agentes de IA (Anthropic API) que classificam cada corte por motivação regulatória, marcam elegibilidade de ressarcimento e geram dossiês; mais um agente RAG sobre as regras.

---

## 1. Decisões de arquitetura (já tomadas — siga-as)

| Item | Decisão |
|------|---------|
| Linguagem/Framework | Python 3.11+ e **FastAPI** |
| Fonte de dados | **PostgreSQL**, populado por um pipeline em **arquitetura medalhão** (bronze → silver → **gold**) que outra pessoa mantém. Seu backend lê **apenas a camada `gold`** (tabelas limpas e prontas). |
| Acesso ao banco | **SQLAlchemy 2.x** (core + ORM) + **psycopg** (driver). Conexão via `DATABASE_URL`. |
| Agentes de IA | **Anthropic API** via SDK oficial `anthropic` (Python). |
| ML | Modelo treinado de verdade (scikit-learn / LightGBM). Treino offline, inferência servida pelo backend. |
| Servidor | `uvicorn` (dev) / `gunicorn`+`uvicorn workers` (prod no Docker que o colega sobe). |
| Validação/Schemas | **Pydantic v2** para todos os modelos de request/response. |
| Gerência de dependências | `uv` ou `pip` + `pyproject.toml`. |

**Princípio de desacoplamento:** você NÃO depende do pipeline de dados estar pronto para começar. Toda leitura de dados passa por uma camada de **repositório** (`app/repositories/`) com uma interface única. Implemente **duas** versões dela: (a) `PostgresRepository` (real, lê a camada gold) e (b) `MockRepository` (lê CSVs de exemplo de uma pasta `data/samples/` que você mesmo cria com dados fictícios no formato do contrato). Um flag de config (`DATA_BACKEND=postgres|mock`) escolhe qual usar. Assim você desenvolve e testa endpoints sem esperar o banco.

---

## 2. Contrato de dados (camada `gold` — o que você pode assumir)

> Esta é a fronteira entre você e quem puxa os dados. Estas são as tabelas/colunas que você **assume existir** na camada gold. Se o nome real divergir, ajusta só o repositório — o resto do backend não muda. Confirme os nomes finais com quem montou o pipeline; abaixo está o contrato proposto, derivado dos datasets abertos reais do ONS/CCEE/ANEEL.

### 2.1 `gold.usinas` — cadastro de usinas (origem: ANEEL/SIGA + ONS)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `usina_id` | text (PK) | Identificador único da usina (CEG ou código ONS) |
| `nome` | text | Nome da usina |
| `fonte` | text | `eolica` ou `solar` |
| `potencia_mw` | float | Potência instalada outorgada (MW) |
| `submercado` | text | `NE`, `N`, `SE_CO`, `S` (define qual PLD se aplica) |
| `latitude` | float | Para casar com clima |
| `longitude` | float | Para casar com clima |
| `garantia_fisica_mwm` | float | Garantia física (MW médios), se disponível |

### 2.2 `gold.constrained_off` — eventos de corte (origem: ONS, detalhamento por usina)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `usina_id` | text (FK) | |
| `timestamp` | timestamp | Início do período (granularidade horária ou semi-horária) |
| `fonte` | text | `eolica` / `solar` |
| `geracao_verificada_mwh` | float | O que a usina de fato gerou |
| `geracao_referencia_mwh` | float | O que poderia ter gerado (estimativa de disponível) |
| `energia_restringida_mwh` | float | **MWh cortados** = referência − verificada (já vem calculado no gold) |
| `razao_restricao` | text | Motivo do corte. Valores esperados: `confiabilidade`, `energetico` (razão energética/sobreoferta), `indisponibilidade_externa`. **Esta coluna é central para o Elo 3.** |
| `submercado` | text | |

### 2.3 `gold.geracao_horaria` — geração verificada horária (origem: ONS)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `usina_id` | text (FK) | |
| `timestamp` | timestamp | |
| `geracao_mwh` | float | |
| `fator_capacidade` | float | 0–1, se disponível |

### 2.4 `gold.pld_horario` — preço de liquidação (origem: CCEE)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `timestamp` | timestamp | |
| `submercado` | text | |
| `pld_reais_mwh` | float | PLD em R$/MWh |

### 2.5 `gold.clima_horario` — features climáticas (origem: Open-Meteo, por usina)
| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `usina_id` | text (FK) | |
| `timestamp` | timestamp | |
| `irradiancia_wm2` | float | GHI — relevante p/ solar |
| `vento_ms` | float | Velocidade do vento — relevante p/ eólica |
| `temperatura_c` | float | Proxy de demanda |
| `is_forecast` | bool | `true` se previsão futura, `false` se observado |

> **Importante sobre o `razao_restricao`:** no dado bruto do ONS o motivo pode vir codificado ou com nomenclatura diferente. Assuma que a camada gold já normalizou para os três valores acima. Se vier sujo, o Elo 3 tem um classificador que lida com isso (ver §5).

---

## 3. Estrutura de pastas do backend

```
backend/
├── pyproject.toml
├── .env.example                 # DATABASE_URL, ANTHROPIC_API_KEY, DATA_BACKEND, etc.
├── README.md
├── data/
│   └── samples/                 # CSVs fictícios no formato do contrato (você cria)
├── models_ml/                   # artefatos de ML treinados (.pkl/.txt) + script de treino
│   ├── train_curtailment_model.py
│   └── curtailment_model.pkl
├── app/
│   ├── main.py                  # instancia FastAPI, inclui routers, CORS
│   ├── config.py                # Pydantic Settings (lê .env)
│   ├── database.py              # engine SQLAlchemy, session
│   ├── deps.py                  # dependências FastAPI (get_db, get_repo, get_settings)
│   ├── schemas/                 # Pydantic v2 (request/response) por domínio
│   │   ├── usinas.py
│   │   ├── curtailment.py
│   │   ├── financeiro.py
│   │   ├── bess.py
│   │   └── regulatorio.py
│   ├── repositories/            # camada de acesso a dados (interface + postgres + mock)
│   │   ├── base.py              # ABC com a interface
│   │   ├── postgres_repo.py
│   │   └── mock_repo.py
│   ├── services/                # regras de negócio (NÃO acessa HTTP nem DB direto)
│   │   ├── curtailment_service.py   # Elo 1
│   │   ├── financeiro_service.py    # Elo 2
│   │   ├── bess_service.py          # Elo 2 (business case)
│   │   └── regulatorio_service.py   # Elo 3 (orquestra agentes)
│   ├── ml/
│   │   ├── features.py          # engenharia de features
│   │   └── predictor.py         # carrega modelo, expõe predict()
│   ├── agents/                  # agentes de IA (Anthropic)
│   │   ├── anthropic_client.py  # wrapper único do SDK
│   │   ├── classifier_agent.py  # classifica corte por motivação
│   │   ├── dossier_agent.py     # gera dossiê de pleito
│   │   └── rag_agent.py         # RAG sobre regras regulatórias
│   ├── routers/                 # endpoints FastAPI (fino: chama services)
│   │   ├── usinas.py
│   │   ├── curtailment.py
│   │   ├── financeiro.py
│   │   ├── bess.py
│   │   └── regulatorio.py
│   └── knowledge/               # base normativa p/ RAG (textos .md das regras)
└── tests/
    ├── test_repositories.py
    ├── test_financeiro.py
    └── test_endpoints.py
```

**Regra de camadas (respeite estritamente):** `routers` → chamam `services` → chamam `repositories` e `ml`/`agents`. Routers nunca tocam SQL nem o SDK da Anthropic direto. Services contêm a lógica e são testáveis sem FastAPI.

---

## 4. Funcionalidades por elo (o que implementar)

### Elo 1 — Curtailment (ML preditivo)

**Objetivo:** dado uma usina, retornar (a) histórico de cortes e (b) previsão de risco de corte para as próximas 24–48h.

`services/curtailment_service.py`:
- `get_historico_cortes(usina_id, inicio, fim)` → agrega `gold.constrained_off`: total de MWh restringidos, nº de eventos, distribuição por `razao_restricao`, série temporal.
- `prever_risco(usina_id, horizonte_horas=48)` → usa `ml/predictor.py`.

`ml/`:
- **`features.py`** — monta a matriz de features por (usina, hora): irradiância/vento/temp (clima), fator de capacidade recente, hora do dia, dia da semana, submercado (one-hot), PLD recente, média móvel de corte nas últimas N horas/dias, flag fim de semana (domingos de manhã são pico de corte solar — feature importante).
- **`train_curtailment_model.py`** — script offline. Target: classificação binária `houve_corte` (energia_restringida > limiar) **e/ou** regressão da magnitude (MWh cortados). Sugestão: **LightGBM** (lida bem com tabular, rápido, bom com features mistas). Treina sobre o histórico do gold, salva `curtailment_model.pkl` + metadados (features, métricas). Reporta AUC/PR para classificação e MAE para magnitude.
- **`predictor.py`** — carrega o `.pkl` uma vez (no startup), expõe `predict(features_df) -> [{timestamp, prob_corte, magnitude_estimada_mwh}]`.

> Para o MVP: treine com o que houver no gold. Se o volume for pequeno, um modelo simples bem-feito (LightGBM com poucas features) supera um complexo mal-validado. Use validação temporal (split por data, nunca aleatório) — corte é série temporal, vazamento temporal mata a credibilidade no pitch.

### Elo 2 — Financeiro

`services/financeiro_service.py`:
- `calcular_perda(usina_id, inicio, fim)` → para cada evento de corte, junta com `gold.pld_horario` pelo `submercado` e `timestamp`, calcula `perda_reais = energia_restringida_mwh × pld_reais_mwh`. Retorna total, série temporal e quebra por `razao_restricao`.
- `projetar_exposicao(usina_id, horizonte)` → combina a previsão do Elo 1 com PLD esperado para estimar exposição financeira futura (cenário simples: PLD médio recente; cenário avançado opcional: distribuição de PLD).

`services/bess_service.py` (business case de bateria):
- `simular_bess(usina_id, potencia_bateria_mw, duracao_horas, eficiencia=0.85, capex_opcional)` → simula, sobre o histórico de cortes, quanta energia a bateria teria "salvado" (carregar no excedente, descarregar depois), valora ao PLD, e estima retorno. Retorna energia recuperada (MWh), receita recuperada (R$), % do corte mitigado. Parâmetros default alinhados ao leilão BESS 2026 (≥30 MW, 4h, η≥85%). Mantenha a física simples e honesta: limite por potência e por energia da bateria, sem otimização sofisticada no MVP (deixe `# TODO: otimização de despacho` como gancho).

### Elo 3 — Regulatório (agentes de IA)

`services/regulatorio_service.py` orquestra três agentes (§5):
- `classificar_eventos(usina_id, inicio, fim)` → para eventos com `razao_restricao` ambígua/ausente, usa o `classifier_agent`; senão usa o valor do gold. Marca elegibilidade de ressarcimento: elegível se `confiabilidade` ou `indisponibilidade_externa`; **não** elegível se `energetico` (regra atual pós-Lei 15.269/2025 — deixe a regra parametrizável num dict, porque pode mudar).
- `gerar_dossie(usina_id, inicio, fim)` → seleciona eventos elegíveis, calcula valoração (via Elo 2), e chama `dossier_agent` para redigir o relatório de pleito.
- `consultar_regra(pergunta)` → chama `rag_agent`.

---

## 5. Agentes de IA — Anthropic API (detalhes de implementação)

**SDK:** pacote `anthropic` (Python). Padrão de chamada:
```python
from anthropic import Anthropic
client = Anthropic()  # lê ANTHROPIC_API_KEY do ambiente
msg = client.messages.create(
    model="claude-haiku-4-5",      # confirmar nome atual na doc oficial
    max_tokens=1024,
    system="...",
    messages=[{"role": "user", "content": "..."}],
)
text = msg.content[0].text
```
> **Confirme os nomes de modelo na doc oficial** (`https://platform.claude.com/docs/en/about-claude/models/overview`) antes de fixar. Diretriz de escolha: use um modelo **rápido e barato (Haiku)** para classificação em volume (muitos eventos), e um modelo **mais capaz (Sonnet/Opus)** para redação do dossiê e para o RAG. Não exponha a API key; ela vive só no backend, nunca vai pro frontend.

**`agents/anthropic_client.py`** — wrapper único: encapsula criação do client, retries, timeout, e uma função `complete(system, user, model, max_tokens)`. Todos os agentes usam este wrapper (facilita trocar modelo/provider depois).

**`agents/classifier_agent.py`** — recebe os dados de um evento de corte (contexto: hora, submercado, se havia sobreoferta no sistema, geração vs. referência) e retorna a classificação em **JSON estruturado** (`{razao, confianca, justificativa}`). Instrua o modelo no system prompt a responder **somente JSON**, e faça parse seguro (try/except, com fallback para "indefinido"). Para o MVP, a maioria dos eventos já vem classificada do ONS — o agente é para os casos ambíguos e para gerar a *justificativa* legível.

**`agents/dossier_agent.py`** — recebe a lista de eventos elegíveis + valoração e redige um dossiê de pleito (texto estruturado: resumo, tabela de eventos, enquadramento na REN 1.030/2022 e Lei 15.269/2025, valor total pleiteado). Saída em markdown. **Humano no loop:** o endpoint retorna o rascunho; nunca "submete" nada a lugar nenhum.

**`agents/rag_agent.py`** — RAG simples sobre `app/knowledge/` (arquivos .md com as regras: REN 1.030/2022, resumo da Lei 15.269/2025, regras de comercialização CCEE relevantes). Para o MVP, RAG leve: carregue os .md, faça chunking simples, e para uma pergunta recupere os trechos mais relevantes (pode ser por embedding com um modelo leve, ou — mais simples e suficiente no MVP — busca por palavra-chave/BM25) e passe como contexto ao modelo. Responda citando de qual documento veio. Não invente norma; se não achar no contexto, diga que não encontrou.

> **Custo/latência:** classificação de muitos eventos pode estourar tempo no pitch. Implemente (a) cache dos resultados por evento e (b) processamento em lote opcional. Não chame o LLM dentro de loops grandes sem batch.

---

## 6. Endpoints FastAPI (o contrato com o frontend React)

Todos sob prefixo `/api`. Respostas sempre Pydantic. Habilite **CORS** para o domínio do frontend. Documentação automática em `/docs` (Swagger) — entregue isso funcionando, o frontend vai usar para se guiar.

### Usinas
- `GET /api/usinas` → lista usinas (id, nome, fonte, potência, submercado). Suporta `?fonte=&submercado=`.
- `GET /api/usinas/{usina_id}` → detalhe de uma usina.

### Elo 1 — Curtailment
- `GET /api/usinas/{usina_id}/cortes?inicio=&fim=` → histórico agregado de cortes (total MWh, nº eventos, quebra por razão, série temporal).
- `GET /api/usinas/{usina_id}/risco?horizonte=48` → previsão de risco de corte por hora (`[{timestamp, prob_corte, magnitude_estimada_mwh}]`).

### Elo 2 — Financeiro
- `GET /api/usinas/{usina_id}/perda?inicio=&fim=` → perda financeira (total R$, série temporal, quebra por razão).
- `GET /api/usinas/{usina_id}/exposicao?horizonte=48` → exposição financeira projetada.
- `POST /api/usinas/{usina_id}/bess/simular` → body `{potencia_mw, duracao_horas, eficiencia, capex?}`; retorna energia recuperada, receita recuperada, % mitigado.

### Elo 3 — Regulatório
- `GET /api/usinas/{usina_id}/elegibilidade?inicio=&fim=` → eventos classificados + flag de elegibilidade + valor potencialmente ressarcível.
- `POST /api/usinas/{usina_id}/dossie` → body `{inicio, fim}`; retorna o dossiê de pleito em markdown (rascunho).
- `POST /api/regulatorio/consulta` → body `{pergunta}`; retorna resposta do RAG com fontes.

### Dashboard (conveniência p/ o frontend)
- `GET /api/usinas/{usina_id}/resumo?inicio=&fim=` → **endpoint agregador** que devolve num só payload: dados da usina, total de MWh cortados, perda R$, % ressarcível, e risco próximas 48h. Serve a tela principal do pitch (evita o frontend fazer 5 chamadas).

**Padrões transversais:** validação de datas e `usina_id` (404 se não existe); erros em formato JSON consistente (`{detail, code}`); paginação onde a lista puder crescer; timezone explícito (use UTC no banco, converta para America/Sao_Paulo na resposta se o front pedir); todos os valores monetários em R$ e energia em MWh, com a unidade no nome do campo.

---

## 7. Config, segurança e execução

- **`config.py`** (Pydantic Settings): `DATABASE_URL`, `ANTHROPIC_API_KEY`, `DATA_BACKEND` (`postgres`/`mock`), `CORS_ORIGINS`, `ANTHROPIC_MODEL_FAST`, `ANTHROPIC_MODEL_SMART`. Tudo via `.env`; entregue `.env.example` sem segredos.
- **Segredos:** `ANTHROPIC_API_KEY` só no backend. Nunca logue a key nem a mande na resposta. Nada de credenciais no código ou no git.
- **CORS:** liberar só a origem do frontend (em dev, `http://localhost:5173` ou o que o time usar).
- **Execução dev:** `uvicorn app.main:app --reload`. O colega empacota no Docker para prod — entregue um `Dockerfile` simples e funcional, mas não configure o ambiente dele.
- **Dependências mínimas:** `fastapi`, `uvicorn`, `pydantic`, `pydantic-settings`, `sqlalchemy`, `psycopg[binary]`, `anthropic`, `pandas`, `lightgbm`, `scikit-learn`, `python-dotenv`. (RAG por palavra-chave evita dependência de vetor; se for usar embeddings, adicione o que precisar.)

---

## 8. Ordem de implementação sugerida (para destravar o time rápido)

1. **Esqueleto + Mock:** `main.py`, `config.py`, `MockRepository` lendo `data/samples/*.csv`, e o endpoint `GET /api/usinas` + `/api/usinas/{id}/resumo` devolvendo dados fictícios. → **O frontend já pode começar contra `/docs`.**
2. **Elo 2 (financeiro)** sobre o mock — é só junção + multiplicação, entrega valor visível cedo (o número de R$ perdido é o "uau" do pitch).
3. **PostgresRepository** com o contrato da §2 (quando a camada gold existir, só troca o flag).
4. **Elo 1 (ML):** features + treino + predictor + endpoints de risco.
5. **Elo 3 (agentes):** wrapper Anthropic → classifier → elegibilidade → dossiê → RAG.
6. **Polimento:** caching dos agentes, tratamento de erro, testes, README.

> Entregue cada etapa funcionando ponta a ponta (endpoint testável no `/docs`) antes de ir para a próxima. Num hackathon, três elos com um demo simples valem mais que um elo perfeito sem demo.

---

## 9. Notas de honestidade técnica (para não furar no pitch)

- **Validação temporal no ML:** nunca split aleatório em série temporal. Reporte a métrica honestamente.
- **Regra de elegibilidade parametrizável:** a regra "energético não é ressarcível" reflete a Lei 15.269/2025 (com veto ao ressarcimento amplo), mas está sob disputa/regulamentação. Deixe num dict de config, não hardcoded espalhado.
- **Agentes com humano no loop:** o dossiê é rascunho; o backend nunca submete pleito a sistema externo.
- **Dados reais no caminho crítico:** o MVP deve rodar sobre dados abertos reais (ONS/CCEE) assim que a camada gold existir; o mock é andaime de desenvolvimento, não a demo final.

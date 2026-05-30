# CurtailIQ — Contrato e Instruções para o Frontend (consumo da API)

Objetivo deste documento
- Guiar o time de frontend sobre O QUE consumir do backend, PARA QUE cada endpoint serve no produto, e COMO isso gera valor para o cliente.
- Não prescrever layout, design system, componentes, nem narrativa visual. Isso fica aberto para criatividade do front.

Escopo atual do backend
- Backend-first, com foco em geradoras renováveis do Nordeste (submercado NE) no MVP.
- Elo 2 (Financeiro) e Elo 3 (Regulatório) já funcionais.
- Elo 1 (ML de risco) integrado no resumo e já com pipeline base de treino/inferência no backend.


## 1) Quem é o cliente e qual problema estamos resolvendo

Cliente principal
- Geradoras renováveis (eólica/solar), especialmente times de:
  - Operação
  - Comercial/Risco
  - Regulação/Jurídico técnico

Problema resolvido
- Transformar curtailment (corte de geração) em decisão gerenciável:
  1. Quantificar perdas financeiras rapidamente
  2. Estimar exposição futura
  3. Identificar potencial ressarcível por regra regulatória
  4. Gerar rascunho de dossiê de pleito
  5. Apoiar decisão de investimento em BESS


## 2) Princípios de integração frontend

1. Front consome endpoints de produto; não acessa banco e não chama LLM diretamente.
2. Agentes de IA são orquestrados no backend (frontend só chama endpoints de negócio).
3. Datas devem ser enviadas em ISO-8601.
4. Sempre tratar estados de qualidade de dados retornados pela API (ex.: PLD parcial).
5. Tratar erros padronizados: {"code": "...", "detail": "..."}.


## 3) Base URL e observabilidade mínima

- Base: `/api`
- Saúde básica: `GET /health`
- Prontidão: `GET /readiness`

Uso no frontend
- /health: indicador simples de disponibilidade.
- /readiness: distingue backend pronto em mock/postgres e check de conexão.


## 4) Contrato funcional por endpoint

### 4.1 Catálogo de usinas

`GET /api/usinas?fonte=&submercado=&limit=&offset=`

Para que serve
- Alimentar seleção de usina/filtros.
- Base para qualquer jornada analítica subsequente.

Retorno (shape)
- `total_count: int`
- `limit: int`
- `offset: int`
- `items: UsinaOut[]`
  - `usina_id, nome, fonte, potencia_mw, submercado`


`GET /api/usinas/{usina_id}`

Para que serve
- Detalhe da usina selecionada.


### 4.2 Endpoint agregador (ideal para tela principal)

`GET /api/usinas/{usina_id}/resumo?inicio=&fim=`

Para que serve
- Entregar, em uma chamada, os principais KPIs de negócio para a usina.

Retorno (shape)
- `usina`
- `total_corte_mwh`
- `total_perda_reais`
- `percentual_ressarcivel`
- `total_eventos_corte`
- `ticket_medio_evento_reais`
- `risco_48h: list[dict]` (saída do Elo 1)

Valor para cliente
- Dá visão executiva imediata (impacto + risco + recuperabilidade) para priorização operacional/comercial.


### 4.3 Elo 2 — Financeiro

`GET /api/usinas/{usina_id}/perda?inicio=&fim=`

Para que serve
- Quantificar perda realizada no período (evento a evento e agregado).

Retorno (shape)
- `usina_id`
- `total_perda_reais`
- `total_energia_restringida_mwh`
- `por_razao: {razao: valor_reais}`
- `qualidade_dados`
  - `status: completo | parcial | sem_pld`
  - `pld_faltante_eventos`
  - `total_eventos`
- `serie[]`
  - `timestamp`
  - `energia_restringida_mwh`
  - `pld_reais_mwh`
  - `perda_reais`
  - `razao_restricao`

Valor para cliente
- Mostra dinheiro perdido com rastreabilidade horária e por motivo regulatório.


`GET /api/usinas/{usina_id}/exposicao?horizonte=48`

Para que serve
- Estimar exposição futura simplificada.

Retorno (shape)
- `usina_id`
- `horizonte_horas`
- `exposicao_estimada_reais`
- `premissas`
  - `energia_media_restringida_mwh_por_hora`
  - `pld_medio_reais_mwh`
  - `metodo`

Valor para cliente
- Suporte rápido a decisão tática (risco de curto prazo).


`POST /api/usinas/{usina_id}/bess/simular?inicio=&fim=`

Body
- `potencia_mw` (>0)
- `duracao_horas` (>0)
- `eficiencia` (0..1, default 0.85)
- `capex` (opcional)

Para que serve
- Simular mitigação de curtailment com bateria.

Retorno (shape)
- `usina_id`
- `energia_recuperada_mwh`
- `receita_recuperada_reais`
- `percentual_mitigado`
- `capex` (opcional)
- `payback_anos` (opcional)

Valor para cliente
- Apoia business case de armazenamento (BESS) com dados da própria usina.


### 4.4 Elo 3 — Regulatório (agentes)

`GET /api/usinas/{usina_id}/elegibilidade?inicio=&fim=`

Para que serve
- Classificar eventos e marcar elegibilidade de ressarcimento.

Como os agentes entram
- O frontend chama este endpoint.
- O backend decide se usa:
  - classificação já existente no dado (gold), ou
  - `classifier_agent` (IA) para caso ambíguo.

Retorno (shape)
- `usina_id`
- `total_potencial_ressarcivel_reais`
- `qualidade_classificacao`
  - `eventos_totais`
  - `eventos_classificados_por_ia`
  - `eventos_com_razao_gold`
- `qualidade_dados`
  - `status: completo | parcial`
  - `pld_faltante_eventos`
  - `eventos_sem_razao_original`
  - `eventos_com_razao_normalizada`
  - `total_eventos`
- `eventos[]`
  - `timestamp`
  - `razao_restricao`
  - `energia_restringida_mwh`
  - `elegivel_ressarcimento`
  - `valor_potencial_reais`
  - `classificacao_fonte` (gold|ia)
  - `classificacao_confianca`
  - `classificacao_justificativa`

Valor para cliente
- Conecta operação à tese regulatória de recuperação de receita.


`POST /api/usinas/{usina_id}/dossie`

Body
- `inicio`
- `fim`

Para que serve
- Gerar rascunho de dossiê (markdown) com base nos eventos elegíveis.

Como os agentes entram
- O frontend chama o endpoint.
- O backend usa `dossier_agent` para produzir texto estruturado.

Retorno (shape)
- `usina_id`
- `dossie_markdown`

Valor para cliente
- Reduz tempo operacional para preparar pleito técnico-regulatório.


`POST /api/regulatorio/consulta`

Body
- `pergunta`

Para que serve
- Consulta de regras com RAG regulatório.

Como os agentes entram
- O backend usa `rag_agent` e devolve resposta + fontes.

Retorno (shape)
- `resposta`
- `fontes: string[]`

Valor para cliente
- Acelera interpretação normativa com rastreabilidade de fonte.


## 5) Contrato de erros e validações (importante para UX)

Erros esperados
- 404: usina inexistente
  - `{ "code": "usina_nao_encontrada", "detail": "Usina não encontrada" }`
- 422: data inválida
  - `{ "code": "parametro_data_invalido", "detail": "..." }`

Regras de input
- Datas em formato ISO-8601.
- Horizonte de exposição: 1 a 168 horas.
- BESS: potencia/duração > 0; eficiência entre 0 e 1.


## 6) Fluxos recomendados de consumo (sem impor UI)

Fluxo A — visão executiva da usina
1. `GET /api/usinas` (lista/seleção)
2. `GET /api/usinas/{id}/resumo` (KPI principal)
3. Drill-down opcional em perda/elegibilidade

Fluxo B — análise financeira
1. `GET /api/usinas/{id}/perda`
2. `GET /api/usinas/{id}/exposicao`
3. `POST /api/usinas/{id}/bess/simular`

Fluxo C — recuperação regulatória
1. `GET /api/usinas/{id}/elegibilidade`
2. `POST /api/usinas/{id}/dossie`
3. `POST /api/regulatorio/consulta` para dúvidas de regra


## 7) Agentes e scripts: o que o frontend precisa saber

Agentes (consumo indireto via API)
- `classifier_agent`: classifica eventos ambíguos para elegibilidade.
- `dossier_agent`: gera texto do dossiê.
- `rag_agent`: responde perguntas regulatórias com fontes.

Importante
- Frontend NÃO chama agentes diretamente.
- Frontend chama endpoints de negócio; backend orquestra IA + regras + cache.

Scripts de ML (consumo operacional, não via UI de usuário final)
- `models_ml/train_curtailment_model.py`
  - serve para treinar/atualizar modelo de risco (Elo 1).
- Resultado impacta o campo `risco_48h` no endpoint de resumo.

Importante
- Script de treino é responsabilidade de operação/backend.
- Frontend apenas consome o resultado já publicado pela API.


## 8) Orientações de produto para o front (sem engessar design)

Foco de valor percebido
- Sempre explicitar:
  1) quanto foi perdido,
  2) quanto pode ser ressarcido,
  3) qual risco próximo,
  4) qual ação recomendada (ex.: simular BESS, gerar dossiê, consultar regra).

Transparência
- Exibir qualidade de dados (`completo/parcial/sem_pld`).
- Exibir origem da classificação (`gold` vs `ia`) e confiança.

Confiabilidade
- Mostrar fontes nas respostas regulatórias.
- Tratar indisponibilidade parcial de dados sem quebrar jornada.


## 9) Estado atual x evolução prevista

Já disponível
- Usinas, resumo, perda, exposição, BESS, elegibilidade, dossiê, consulta regulatória, health/readiness.

Evolução provável
- Endpoint dedicado de risco (`/risco`) e histórico de cortes (`/cortes`) no Elo 1.
- Sem impacto estrutural para frontend se já estiver consumindo `/resumo` como endpoint agregador.


## 10) Referência rápida de payloads (mínimos)

BESS (request)
```json
{
  "potencia_mw": 30,
  "duracao_horas": 4,
  "eficiencia": 0.85,
  "capex": 120000000
}
```

Dossiê (request)
```json
{
  "inicio": "2026-05-01T00:00:00",
  "fim": "2026-05-31T23:59:59"
}
```

Consulta regulatória (request)
```json
{
  "pergunta": "Cortes por razão energética são elegíveis a ressarcimento no cenário atual?"
}
```


---

Resumo final para o time front
- Liberdade total de design/visualização.
- Obrigações de integração: consumir estes endpoints, tratar erros/qualidade, e comunicar claramente o valor de negócio para geradoras renováveis do NE (perda, risco, ressarcimento, decisão).

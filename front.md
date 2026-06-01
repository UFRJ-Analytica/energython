# CurtailIQ — Contrato e instruções para o Frontend

Objetivo
- Guiar o front sobre o que consumir da API e como representar histórico vs previsão com transparência.
- Não prescrever layout/design system.

Escopo
- MVP backend-first, foco em geradoras renováveis do submercado NE.
- ML-first com fallback robusto (sazonal) quando modelo/deps não estiverem disponíveis.

## 1) Regras de integração

1. Front consome apenas endpoints de negócio (`/api`).
2. Datas em ISO-8601.
3. Tratar erros padronizados (`code`, `detail`).
4. Sempre exibir estado/qualidade de dados quando disponível.
5. Sempre distinguir dado histórico de dado previsto na UI.

## 2) Endpoints principais e contratos

### Catálogo / contexto

GET `/api/usinas`
- Lista usinas para seleção.

GET `/api/usinas/{usina_id}`
- Detalhe da usina.

GET `/api/usinas/{usina_id}/resumo?inicio=&fim=`
- KPI agregado da usina.
- Destaque novo: `perda_esperada_30d` com `metodo` (`ml_advanced | ml_base_random_forest | fallback_sazonal`).

### Financeiro

GET `/api/usinas/{usina_id}/perda?inicio=&fim=`
- Perda histórica realizada (série e agregados).

GET `/api/usinas/{usina_id}/exposicao?horizonte=48`
- Exposição futura estimada.
- Retorna:
  - `premissas.historico_ultimos_30d` (`tipo_dado=historico`)
  - `premissas.previsao_futura` (`tipo_dado=previsao`, `metodo_previsao`)
  - `serie_previsao[]` com `tipo_dado=previsao`

GET `/api/usinas/{usina_id}/previsao-perdas?horizonte=48&historico_horas=168`
- Série comparativa explícita de histórico x previsão.
- Retorna:
  - `serie_historico[]` (`tipo_dado=historico`)
  - `serie_previsao[]` (`tipo_dado=previsao`)
  - `metodo_previsao`, `resumo`

POST `/api/usinas/{usina_id}/bess/simular?inicio=&fim=`
- Simulação de BESS.
- Retorna também `dimensionamento_com_previsao` (quando disponível):
  - `tipo_dado=previsao`
  - `metodo_previsao`
  - `energia_perdida_prevista_mwh`
  - `energia_recuperavel_prevista_mwh`
  - `perda_financeira_evitavel_prevista_reais`

### Curtailement (Elo 1 dedicado)

GET `/api/usinas/{usina_id}/risco-corte?horizonte=48`
- Previsão operacional simples:
  - `previsoes[]`: `timestamp`, `prob_corte`, `magnitude_estimada_mwh`
  - `modelo`

GET `/api/usinas/{usina_id}/curtailment/previsao-detalhada?horizonte=48`
- Previsão analítica detalhada:
  - `tipo_dado=previsao`
  - `previsoes[]`, `alertas[]`, `resumo`
  - `decomposicao_temporal` (opcional)
  - `knn_insights` (opcional)

### Regulatório (assistente)

GET `/api/usinas/{usina_id}/elegibilidade?inicio=&fim=`
- Classificação e potencial ressarcível.

POST `/api/usinas/{usina_id}/dossie`
- Geração de rascunho de dossiê.

POST `/api/regulatorio/consulta`
- Body:
  - `pergunta`
  - `usina_id` (opcional)
  - `inicio` (opcional)
  - `fim` (opcional)
- Retorno:
  - `resposta`
  - `fontes[]`
  - `agente="assistente_ia"`

## 3) Erros e validações

- 404: usina inexistente (`usina_nao_encontrada`)
- 422: data inválida (`parametro_data_invalido`)
- Horizonte: respeitar limites de cada endpoint.
- BESS: potência/duração > 0; eficiência entre 0 e 1.

## 4) Melhorias concretas de UI (implementáveis já)

1. Histórico vs previsão sempre separados
- Dois estilos de série + divisor visual no “agora”.

2. Badge de método da previsão
- Exibir: `ml_advanced`, `ml_base_random_forest` ou `fallback_sazonal`.

3. Tela de usina com três blocos
- Histórico realizado
- Previsão futura
- Ação potencial (ressarcimento + BESS)

4. Financeiro com projeção acionável
- Consumir `serie_previsao` de `/exposicao`.
- Exibir `perda_financeira_evitavel_prevista_reais` do BESS.

5. Assistente regulatório contextual
- Quando houver usina selecionada, enviar `usina_id/inicio/fim` em `/api/regulatorio/consulta`.
- Mostrar fontes e selo `assistente_ia`.

6. Drill-down de risco
- Taba/página dedicada para `/curtailment/previsao-detalhada` com foco em alertas.

## 5) Payloads mínimos

BESS request
```json
{
  "potencia_mw": 30,
  "duracao_horas": 4,
  "eficiencia": 0.85,
  "capex": 120000000
}
```

Consulta regulatória request
```json
{
  "pergunta": "Quais eventos têm maior potencial ressarcível neste período?",
  "usina_id": "USI_NE_001",
  "inicio": "2026-05-01T00:00:00",
  "fim": "2026-05-31T23:59:59"
}
```

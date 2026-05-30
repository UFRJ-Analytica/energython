CurtailIQ Backend (MVP)

Escopo atual (parte 1):
- Pipeline de consumo de dados via repositório (Postgres gold + Mock CSV)
- Estrutura e endpoints do Elo 2 (financeiro + BESS)
- Estrutura e endpoints do Elo 3 (classificação/elegibilidade, dossiê, consulta regulatória)
- Elo 1 mantido como stub para evolução posterior

Como rodar:
1) cd backend
2) copie .env.example para .env e ajuste DATA_BACKEND=mock (ou postgres)
3) pip install -e .  (ou uv sync)
4) uvicorn app.main:app --reload
5) abra http://127.0.0.1:8000/docs

Decisão de negócio para MVP:
- Filtrar usinas do Nordeste (submercado NE) por padrão, controlado por MVP_ONLY_NORDESTE=true.

Padrões de API implementados (parte 2):
- Datas ISO-8601 com parsing robusto e normalização para UTC interno.
- Erros padronizados: {"code": "...", "detail": "..."}.
- Paginação em GET /api/usinas via limit/offset.
- /api/usinas/{usina_id}/resumo inclui métricas de dashboard: total_eventos_corte e ticket_medio_evento_reais.

Evolução implementada (parte 3):
- Cache TTL local no Elo 3 para classificar_eventos e gerar_dossie (chave por usina+período).
- GET /api/usinas passou a retornar metadados de paginação: total_count, limit, offset, items.
- Endpoints de observabilidade: /health e /readiness.
- Logging estruturado de requests HTTP (JSON por requisição).
- Testes de contrato para 404/422 e smoke de readiness.

Onde colocar regra de negócio:
- Limpeza/normalização de dados fica no pipeline do banco (bronze/silver/gold).
- Regras de domínio (perda, elegibilidade, BESS, exposição) ficam em app/services.
- Regras regulatórias parametrizadas em dict central no serviço regulatório.

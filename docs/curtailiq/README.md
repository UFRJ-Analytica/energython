# CurtailIQ — Documentação Técnica do App Streamlit

Este diretório documenta a lógica completa do app `stramlit/app.py`: fontes de dados, regras de negócio, modelo híbrido, anomalias, busca de notícias, ranking, dashboard unitário e Analyst Lab com JupyterLite.

## Objetivo do produto

O CurtailIQ transforma dados de curtailment e geração renovável em uma central de decisão para:

1. monitorar a frota eólica em mapa;
2. escolher uma usina e investigar métricas operacionais/financeiras;
3. prever geração com modelo híbrido Linear + CatBoost;
4. detectar anomalias de comportamento;
5. relacionar notícias/regulação à usina escolhida;
6. rankear melhores/piores usinas por região;
7. abrir um laboratório JupyterLite para EDA manual por analistas.

## Arquivo principal

```text
stramlit/app.py
```

## Abas atuais

| Aba | Nome | Objetivo |
|---|---|---|
| 1 | Control Tower | Mapa e KPIs da frota em estilo Palantir |
| 2 | Detalhe & Previsão | Drill-down por usina + previsão híbrida |
| 3 | Anomalias | IsolationForest para eventos anômalos |
| 4 | Inteligência (Notícias) | Busca web ranqueada por relevância à usina |
| 5 | Ranking Top Tier | Melhores/piores usinas por score |
| 6 | Unidades Individuais | Dashboard por `sk_usina`, sem agrupamento por complexo |
| 7 | Analyst Lab (JupyterLite) | Notebook EDA gerado a partir da usina escolhida |

## Documentos deste diretório

- [`relatorio-tecnicas-streamlit.md`](./relatorio-tecnicas-streamlit.md): relatório consolidado das técnicas usadas no `app.py`, nas pastas do Streamlit/JupyterLite e nas abas.
- [`arquitetura-e-dados.md`](./arquitetura-e-dados.md): conexões, DW, tabelas, caches e contratos de dados.
- [`abas.md`](./abas.md): documentação funcional e técnica de cada aba.
- [`modelos-e-algoritmos.md`](./modelos-e-algoritmos.md): feature engineering, Linear Regression + CatBoost, IsolationForest e score.
- [`jupyterlite-analyst-lab.md`](./jupyterlite-analyst-lab.md): lógica do Analyst Lab, build, serve e notebook gerado.
- [`operacao-e-extensao.md`](./operacao-e-extensao.md): execução, dependências, troubleshooting e como criar novas abas.
- [`skills-reutilizacao.md`](./skills-reutilizacao.md): quais skills Hermes foram criadas e como reutilizar.

## Como rodar

```bash
cd stramlit
source venv/bin/activate
streamlit run app.py --server.headless true --server.port 8765
```

JupyterLite é gerado pela aba 7 e servido em:

```text
http://localhost:8766/
```

## Validações feitas

- `python -m py_compile app.py build_unit_cache.py`
- `streamlit.testing.v1.AppTest` com 7 abas renderizadas e 0 exceções
- endpoint Streamlit HTTP 200
- endpoint JupyterLite HTTP 200

# JupyterLite Analyst Lab

Documento técnico da Aba 7 do `stramlit/app.py`.

## Objetivo

A Aba 7 cria um laboratório JupyterLite por usina para EDA manual no navegador. O fluxo gera dados, notebook, metadados, build estático e iframe embutido no Streamlit.

## Componentes no código

| Função/constante | Papel |
|---|---|
| `JUPYTERLITE_CONTENT_DIR` | Diretório-fonte com CSV, notebook e metadados. |
| `JUPYTERLITE_OUTPUT_DIR` | Diretório de saída do build estático. |
| `JUPYTERLITE_PORT` | Porta local usada pelo `jupyter lite serve` (`8766`). |
| `_slugify()` | Gera nomes seguros para arquivos. |
| `_jupyter_cmd()` | Localiza o executável `jupyter` do ambiente atual. |
| `_port_open()` | Verifica se a porta do JupyterLite já está aberta. |
| `_ensure_jupyterlite_server()` | Inicia o servidor se ele ainda não estiver rodando. |
| `_make_eda_notebook()` | Cria notebook EDA com `nbformat`. |
| `preparar_jupyterlite_lab()` | Orquestra exportação, notebook, build e servidor. |

## Fluxo operacional

1. Usuário seleciona uma usina na Aba 7.
2. Usuário define quantidade de pontos exportados.
3. Ao clicar em **Gerar / atualizar Lab**, o app chama `preparar_jupyterlite_lab()`.
4. A série temporal é baixada por `carregar_serie()`.
5. O app calcula colunas auxiliares:
   - `gap_mw`;
   - `is_restrito`;
   - `corte_mw`.
6. O CSV é salvo em `jupyterlite_content/data/<slug>_serie.csv`.
7. Os metadados são salvos em `jupyterlite_content/<slug>_metadata.json`.
8. O notebook é gerado em `jupyterlite_content/eda_<slug>.ipynb`.
9. O app executa `jupyter lite init`.
10. O app executa `jupyter lite build`.
11. O app inicia `jupyter lite serve` se a porta não estiver aberta.
12. O Streamlit mostra link, botões de download e iframe.

## Notebook gerado

O notebook usa kernel Python/Pyodide e contém:

1. célula Markdown com título, descrição e metadados;
2. setup de `pandas`, `numpy` e `matplotlib`, com fallback `micropip`;
3. carga do CSV e criação de colunas auxiliares;
4. resumo executivo da série;
5. gráfico geração x referência x corte;
6. perfil horário médio;
7. quebra por razão/origem de restrição;
8. outliers por z-score do gap;
9. ideias de investigação manual.

## Saídas esperadas

| Saída | Exemplo |
|---|---|
| CSV | `stramlit/jupyterlite_content/data/conjunto_eolico_kairos_serie.csv` |
| Notebook | `stramlit/jupyterlite_content/eda_conjunto_eolico_kairos.ipynb` |
| Metadados | `stramlit/jupyterlite_content/conjunto_eolico_kairos_metadata.json` |
| Build | `stramlit/jupyterlite_site/` |
| URL | `http://localhost:8766/lab/index.html?path=eda_<slug>.ipynb` |

## Técnicas usadas

- notebook como artefato gerado programaticamente;
- Pyodide para execução Python no navegador;
- CSV como contrato simples entre Streamlit e JupyterLite;
- metadados JSON para contexto do ativo;
- build estático via CLI;
- servidor local em background;
- iframe para integração UI;
- downloads para reprodução externa.

## Pontos de atenção

- O build pode ser demorado se executado a cada clique.
- O servidor depende da porta `8766` estar livre.
- O notebook roda no navegador e pode ter limitações de pacotes Pyodide.
- O conteúdo gerado deve ser limpo ou versionado conscientemente para evitar acúmulo.

# JupyterLite (Analyst Lab)

Pastas trazidas do protótipo Streamlit para fazer parte do projeto Energython e
servir o **Analyst Lab** (JupyterLite/Pyodide) na tela DEBUG.

## Conteúdo

```text
data/jupyter/
├── jupyterlite_content/   # fonte: notebooks .ipynb, CSVs e metadados das usinas
└── jupyterlite_site/      # build estático do JupyterLite (servir como site)
```

## Como servir localmente (self-host do Lab)

O `jupyterlite_site/` é um site estático. Pode ser servido com qualquer HTTP server:

```bash
cd data/jupyter/jupyterlite_site
python3 -m http.server 8777
# abre em http://localhost:8777/lab/index.html
```

## Integração com a tela DEBUG

A aba **Analyst Lab** do frontend embute o JupyterLite via `<iframe>` ocupando quase
toda a tela. A URL do iframe é configurável por env do front:

```text
VITE_JUPYTERLITE_URL   (default: instância pública de demonstração)
```

Para usar o build local, sirva `jupyterlite_site/` (ex.: porta 8777) e defina:

```bash
# front/.env.local
VITE_JUPYTERLITE_URL=http://localhost:8777/lab/index.html
```

## Geração de novos notebooks

O backend expõe, na camada DEBUG, o template do notebook e o CSV da usina:

```text
GET /api/debug/usinas/{id}/lab-template
GET /api/debug/usinas/{id}/lab-template/notebook   (download .ipynb)
GET /api/debug/usinas/{id}/lab-template/csv        (download .csv)
```

Esses arquivos podem ser carregados dentro do JupyterLite para EDA manual.

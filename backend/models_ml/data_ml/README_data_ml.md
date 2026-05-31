# Pipeline de Dados e Machine Learning (MVP Curtailment)

Esta pasta (`data_ml`) contém os 3 códigos fundamentais para o ecossistema de Inteligência Artificial e Analytics do MVP. Ela foi concebida para ser a versão final de entrega, altamente modularizada e focada.

## 1. `data_extraction.py`
Responsável pela **Coleta e Segregação de Dados**.
- Conecta-se à camada Silver/Gold do PostgreSQL.
- Extrai usinas únicas (Eólicas e Solares).
- Separa o processamento, gerando caches locais individuais: `flat_dados_eolica.csv`, `flat_dados_solar.csv` e `ccee_cache.csv`.
- Esses dados são utilizados tanto pelo Dashboard quanto pelos notebooks/scripts de treino.

## 2. `models.py`
Contém as definições e orquestrações dos modelos preditivos.
- Contempla as classes de inferência, notadamente o `AdvancedCurtailmentPredictor`.
- Carrega de forma inteligente (e cacheada) os arquivos seriais (`.pkl`) especializados (ex: modelo treinado especificamente para Eólica ou Solar).
- Responsável também pela "explicabilidade" local via SHAP values, entregando métricas prontas para UI.

## 3. `dashboard.py`
O **Front-end Analítico** em Streamlit.
- Consome os dados cacheados por `data_extraction.py` (`temp_cache/`).
- Importa o `models.py` de forma dinâmica, aplicando o modelo Eólico para usinas Eólicas, e o modelo Solar para usinas Solares.
- Apresenta os agrupamentos H3, predições de corte de geração e projeções financeiras em tempo real.

## Como Executar

1. **Gere os Caches:**
   ```bash
   python data_extraction.py
   ```
2. **Suba o Dashboard:**
   ```bash
   streamlit run dashboard.py
   ```

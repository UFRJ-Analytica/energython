# 📊 ETL UNIFICADO - ÍNDICE E DOCUMENTAÇÃO


---

## 📑 Documentação Disponível

### 1️⃣ **COMECE AQUI:** Sumário Executivo
📄 `SUMARIO_EXECUTIVO.md`
- O que foi feito em 30 segundos
- Dados processados (82M+ linhas)
- Próximos passos

### 2️⃣ **Para Entender Tudo:** ETL Camada Prata - Documentação Completa
📄 `ETL_CAMADA_PRATA_DOCUMENTACAO_COMPLETA.md`
- Visão geral do pipeline
- Explicação de cada operação (nulos, outliers, normalização)
- Estrutura de saída (Silver e Agg)
- Como rodar
- Exemplos de consumo (backend + frontend)
- Agregações disponíveis
- Troubleshooting

### 3️⃣ **Para Implementar:** Guia Backend e Frontend
📄 `GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md`
- Código pronto para FastAPI (backend Python)
- Código pronto para React + TypeScript (frontend)
- Estrutura de projetos
- APIs prontas
- Componentes React
- Teste de integração

---

## 🚀 Quick Start

### 1. Rodar o ETL (uma vez)
```bash
cd /home/juan/Desktop/ons_data_lake/spark_duck
python etl_unificado.py
```

**Tempo:** ~2-3 horas (completo) ou ~20 segundos (teste com --limit 500000)

### 2. Backend (FastAPI)
```bash
# (copia código do GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md)
pip install fastapi uvicorn pandas pyarrow
python main.py
# Acessa: http://localhost:8000/docs
```

### 3. Frontend (React)
```bash
npm create vite@latest -- --template react-ts
# (copia componentes do GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md)
npm install axios chart.js react-chartjs-2
npm run dev
# Acessa: http://localhost:5173
```

---

## 📂 Arquivos do Projeto

### Scripts
- `etl_unificado.py` — Pipeline completo (execute este)

### Documentação
- `SUMARIO_EXECUTIVO.md` — Overview em 2 minutos
- `ETL_CAMADA_PRATA_DOCUMENTACAO_COMPLETA.md` — Documentação técnica
- `GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md` — Código + exemplos
- `README.md` — Este arquivo

### Data Lake
- `lake/silver/` — Dados tratados e particionados
  - `geracao_usina_2/`
  - `disponibilidade_usina/`
  - `fator_capacidade_2/` (com H3)
  - `restricao_coff_eolica_detail/`

- `lake/agg/` — Agregações para BI/Dashboards
  - `agg_geracao_estado_dia/` — Soma diária
  - `agg_fator_capacidade_estado_mes/` — Média mensal

---

## 🧹 O Que o ETL Faz

```
PostgreSQL (raw, confuso, 82M linhas)
    ↓
[1] Remove nulos em colunas-chave
[2] Remove outliers (IQR estatístico)
[3] Normaliza strings (trim + lowercase)
[4] Particiona por estado/ano/mes
[5] Adiciona H3 (geoespacial)
    ↓
Parquet Silver (limpo, rápido, 82M linhas)
    ↓
[6] Agregações (SUM, AVG)
    ↓
Parquet Agg (dimensões reduzidas, BI-ready)
```

---

## 📊 Dados Processados

| Tabela | Volume | Período | Saída |
|--------|--------|---------|-------|
| **geracao_usina_2** | 15.0M | 2003-2026 | ✓ Silver + Agg dia |
| **disponibilidade_usina** | 3.4M | 2019-2026 | ✓ Silver |
| **fator_capacidade_2** | 13.8M | 2014-2026 | ✓ Silver (H3) + Agg mês |
| **restricao_coff_eolica_detail** | 49.5M | 2021-2026 | ✓ Silver |
| **ccee_pld_horario** | 38K | - | ✓ Silver |
| **TOTAL** | **~82M** | | ✓ Pronto |

---

## 💻 Como Consumir

### Backend (Python)
```python
import pandas as pd

# Agregação (rápido para BI)
df = pd.read_parquet(
    "/home/juan/Desktop/ons_data_lake/lake/agg/agg_geracao_estado_dia/id_estado=SP/"
)

# Silver (completo com todas dimensões)
df = pd.read_parquet(
    "/home/juan/Desktop/ons_data_lake/lake/silver/geracao_usina_2/id_estado=SP/ano=2024/mes=05/"
)
```

### Frontend (JavaScript)
```javascript
const res = await fetch("/api/geracao/estado/BA?data_inicio=2024-01-01");
const dados = await res.json();
// [{data: "2024-01-01", geracao_total_mw: 1234, ...}, ...]
```

---

## 🔧 Dependências Necessárias

```bash
pip install psycopg2-binary pandas pyarrow duckdb h3
```

- `psycopg2-binary` — Conexão PostgreSQL
- `pandas` — Manipulação de dados
- `pyarrow` — Leitura/escrita Parquet
- `duckdb` — Agregações (opcional mas recomendado)
- `h3` — Indexação geoespacial (opcional)

---

## ⚡ Executar Completo vs. Teste

### Teste Rápido (500K linhas, ~20s)
```bash
python etl_unificado.py --limit 500000 --tables geracao_usina_2
```

### Uma Tabela Completa (~2 horas)
```bash
python etl_unificado.py --tables geracao_usina_2
```

### Todas as Tabelas (~3-4 horas, 82M linhas)
```bash
python etl_unificado.py
```

### Sem Agregações (mais rápido)
```bash
python etl_unificado.py --skip-agg
```

---

## 📈 Agregações Disponíveis

### agg_geracao_estado_dia
Soma e média de geração por estado e dia.

```sql
SELECT data, geracao_total_mw, geracao_media_mw 
FROM agg_geracao_estado_dia 
WHERE id_estado='SP'
ORDER BY data DESC
LIMIT 30
```

### agg_fator_capacidade_estado_mes
Média de fator de capacidade por estado e mês.

```sql
SELECT mes, fator_capacidade_media, geracao_verificada_media_mw
FROM agg_fator_capacidade_estado_mes
WHERE id_estado='BA'
ORDER BY mes DESC
LIMIT 12
```

---

## ✅ Validação Pós-ETL

Após rodar, verificar:

```bash
# 1. Camada Silver existe
ls -lh /home/juan/Desktop/ons_data_lake/lake/silver/

# 2. Partições por estado
ls /home/juan/Desktop/ons_data_lake/lake/silver/geracao_usina_2/

# 3. Agregações existem
ls /home/juan/Desktop/ons_data_lake/lake/agg/

# 4. Ler um arquivo Parquet
python -c "import pandas as pd; df = pd.read_parquet('/home/juan/Desktop/ons_data_lake/lake/agg/agg_geracao_estado_dia/id_estado=SP'); print(df.head())"
```

---

## 🎯 Próximos Passos

1. **Backend**: Implementar APIs (FastAPI)
   - `GET /api/geracao/estado/{estado}/dia`
   - `GET /api/capacidade/estado/{estado}/mes`
   - `GET /api/geracao/estados`

2. **Frontend**: Criar Dashboard (React)
   - Seletor de estado
   - Gráfico de linha (Chart.js)
   - Filtro de data
   - Tabela de estatísticas

3. **CI/CD**: Agendar ETL
   - Executar diariamente? Semanalmente?
   - Salvar logs
   - Alertar se falhar

4. **ML/IA**: Modelos de previsão
   - Usar `silver/` para treino
   - Features: lag, sazonalidade, tipo usina
   - Target: geração futura, PLD

---

## 📞 Troubleshooting

### Problema: "pyarrow not found"
```bash
pip install pyarrow
```

### Problema: "Conexão recusada ao PostgreSQL"
```bash
# Testar conectividade
psql -h 177.7.55.100 -p 32775 -U analytica -d hacka-energinn -c "SELECT 1"
```

### Problema: "Sem espaço em disco"
```bash
df -h /home/juan/Desktop/ons_data_lake/lake/
# Se precisar limpar, remova silver/ e regenere
```

### Problema: "Agregações não foram criadas"
```bash
pip install duckdb
python etl_unificado.py --skip-agg  # Só silver
```

---

## 📚 Referências Técnicas

- **IQR (Interquartile Range):** Método robusto para outlier detection
- **H3:** Sistema hexagonal da Uber para indexação geoespacial
- **Parquet:** Formato colunar otimizado para analytics
- **Particionamento:** Estratégia de organização para query performance

---

## 👤 Informações

**Criado:** 30/05/2026  
**Versão:** 1.0  
**Responsável:** Juan (Energy Data Team)  
**Banco:** hacka-energinn (PostgreSQL)  
**Base de dados:** `/home/juan/Desktop/ons_data_lake/lake/`

---

## 📋 Estrutura da Documentação

```
arquitetura/
├── README.md (ESTE ARQUIVO)
│
├── SUMARIO_EXECUTIVO.md
│   └─ O que foi feito? (2 min)
│
├── ETL_CAMADA_PRATA_DOCUMENTACAO_COMPLETA.md
│   ├─ Como o ETL funciona
│   ├─ Operações de limpeza
│   ├─ Consumo no Backend
│   ├─ Consumo no Frontend
│   ├─ Agregações
│   └─ Troubleshooting
│
├── GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md
│   ├─ Código FastAPI completo
│   ├─ Código React+TS completo
│   ├─ Exemplos de uso
│   └─ Teste de integração
│
└── etl_unificado.py
    └─ Script principal (execute este)
```

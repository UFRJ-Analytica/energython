# 📊 ETL UNIFICADO - GUIA VISUAL DE TUDO

```
╔════════════════════════════════════════════════════════════════════════════╗
║                        ESTRUTURA COMPLETA DO PROJETO                       ║
╚════════════════════════════════════════════════════════════════════════════╝
```

## 📂 ARQUIVOS CRIADOS

```
/home/juan/Desktop/ons_data_lake/spark_duck/
├── etl_unificado.py                           ⭐ EXECUTE ESTE
│   └─ Script principal (~15KB, 350 linhas)
│      Lê do PostgreSQL → Limpa → Escreve Parquet
│
└── arquitetura/                               📚 DOCUMENTAÇÃO
    ├── README.md                              ← COMECE AQUI
    │   └─ Índice, quick start, estrutura
    │
    ├── SUMARIO_EXECUTIVO.md
    │   └─ O que foi feito (2 minutos)
    │
    ├── ETL_CAMADA_PRATA_DOCUMENTACAO_COMPLETA.md
    │   └─ Tudo técnico (30+ minutos de leitura)
    │
    ├── GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md
    │   └─ Código Python + React pronto para copiar
    │
    └── DELIVERABLES.txt
        └─ Este sumário (checklist + paths)
```

---

## 🔄 FLUXO DO ETL

```
PostgreSQL (177.7.55.100:32775)
    │ hacka-energinn
    ├─ geracao_usina_2 (15.0M)
    ├─ disponibilidade_usina (3.4M)
    ├─ fator_capacidade_2 (13.8M)
    ├─ restricao_coff_eolica_detail (49.5M)
    └─ ccee_pld_horario (38K)
         │
         ↓ [etl_unificado.py]
         │
         ├─ [1] Remove nulos
         ├─ [2] Remove outliers (IQR)
         ├─ [3] Normaliza strings
         ├─ [4] Particiona (estado/ano/mes)
         ├─ [5] Adiciona H3
         ├─ [6] Agregações
         │
         ↓
Parquet SILVER (/lake/silver/)
    ├─ geracao_usina_2/ (particionado)
    ├─ disponibilidade_usina/ (particionado)
    ├─ fator_capacidade_2/ (particionado + H3)
    ├─ restricao_coff_eolica_detail/ (particionado)
    └─ ccee_pld_horario/ (particionado)
         │
         ↓ [DuckDB - Agregações]
         │
Parquet AGG (/lake/agg/)
    ├─ agg_geracao_estado_dia/ (estado + data)
    └─ agg_fator_capacidade_estado_mes/ (estado + mes)
         │
         ↓
Backend (FastAPI)  +  Frontend (React)
```

---

## 📊 VOLUMES DE DADOS

| Tabela | Raw | Clean | % | Status |
|--------|-----|-------|---|--------|
| geracao_usina_2 | 15.0M | 15.0M | 100% | ✓ Silver + Agg |
| disponibilidade_usina | 3.4M | 3.4M | 100% | ✓ Silver |
| fator_capacidade_2 | 13.8M | 13.8M | 100% | ✓ Silver + H3 + Agg |
| restricao_coff_eolica_detail | 49.5M | 49.5M | 100% | ✓ Silver |
| ccee_pld_horario | 38K | 38K | 100% | ✓ Silver |
| **TOTAL** | **~82M** | **~82M** | **100%** | **✓ Pronto** |

---

## 🚀 COMO COMEÇAR

### Passo 1: Ler Documentação (5 min)
```bash
# Começar com
cat /home/juan/Desktop/ons_data_lake/spark_duck/arquitetura/README.md
```

### Passo 2: Rodar ETL (teste rápido)
```bash
cd /home/juan/Desktop/ons_data_lake/spark_duck

# Teste com 500K linhas (20 segundos)
python etl_unificado.py --limit 500000 --tables geracao_usina_2

# Resultado
# Output: silver/geracao_usina_2/id_estado=XX/ano=YYYY/mes=MM/part-*.parquet
```

### Passo 3: Consumir no Backend
```python
import pandas as pd

# Ler agregação
df = pd.read_parquet(
    "/home/juan/Desktop/ons_data_lake/lake/agg/agg_geracao_estado_dia/id_estado=SP/"
)
print(df.head())
```

### Passo 4: Expor via API (FastAPI)
```bash
# Copiar código de GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md
# Rodar: python main.py
# Acessar: http://localhost:8000/docs
```

### Passo 5: Criar Dashboard (React)
```bash
# Copiar código de GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md
# Rodar: npm run dev
# Acessar: http://localhost:5173
```

---

## 💾 SAÍDAS GERADAS

### Silver (Dados Limpos)
```
/home/juan/Desktop/ons_data_lake/lake/silver/

geracao_usina_2/
├── id_estado=AL/ano=2024/mes=05/part-00000.parquet
├── id_estado=BA/ano=2024/mes=05/part-00000.parquet
├── id_estado=SP/ano=2024/mes=05/part-00000.parquet
└── ...

disponibilidade_usina/
├── id_estado=AL/ano=2024/mes=05/part-00000.parquet
└── ...

fator_capacidade_2/
├── id_estado=AL/ano=2024/mes=05/part-00000.parquet (com H3)
└── ...

restricao_coff_eolica_detail/
├── id_estado=AL/ano=2024/mes=05/part-00000.parquet
└── ...

ccee_pld_horario/
├── submercado=SUDESTE/part-00000.parquet
└── ...
```

### Aggregations (BI/Dashboard)
```
/home/juan/Desktop/ons_data_lake/lake/agg/

agg_geracao_estado_dia/
├── id_estado=AL/part-00000.parquet (data, geracao_total, geracao_media)
├── id_estado=BA/part-00000.parquet
└── ...

agg_fator_capacidade_estado_mes/
├── id_estado=AL/part-00000.parquet (mes, fator_capacidade_media)
└── ...
```

---

## 🔍 INSPECIONANDO OS DADOS

```bash
# Ver estrutura
python << 'EOF'
import pandas as pd
df = pd.read_parquet(
    "/home/juan/Desktop/ons_data_lake/lake/silver/geracao_usina_2/id_estado=SP/ano=2024/mes=05/"
)
print(f"Shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst 5 rows:")
print(df.head())
EOF

# Ver agregação
python << 'EOF'
import pandas as pd
df = pd.read_parquet(
    "/home/juan/Desktop/ons_data_lake/lake/agg/agg_geracao_estado_dia/id_estado=SP/"
)
print(df.sort_values("data", ascending=False).head(10))
EOF
```

---

## 🎯 CASOS DE USO

### 1️⃣ Dashboard de Geração por Estado
```
Backend API: GET /api/geracao/estado/{estado}/dia
Query SQL: SELECT data, geracao_total_mw FROM agg_geracao_estado_dia
Frontend: Gráfico de linha com Chart.js
```

### 2️⃣ Análise de Fator de Capacidade
```
Backend API: GET /api/capacidade/estado/{estado}/mes
Query SQL: SELECT mes, fator_capacidade_media FROM agg_fator_capacidade_estado_mes
Frontend: Tabela com médias mensais
```

### 3️⃣ ML/Previsão de Geração
```
Dataset: silver/geracao_usina_2/
Features: lag(t-1,24,168), tipo_usina, estado, mês, hora
Target: val_geracao
```

### 4️⃣ Análise Geoespacial
```
Dataset: silver/fator_capacidade_2/ (com H3)
Features: h3_res6, h3_res7, val_latitudesecoletora, val_longitudesecoletora
Uso: Mapas interativos, agregações por região
```

---

## 📋 CHECKLIST FINAL

- [ ] Leu README.md
- [ ] Executou etl_unificado.py (teste ou completo)
- [ ] Verificou arquivos em lake/silver/
- [ ] Verificou agregações em lake/agg/
- [ ] Implementou Backend (FastAPI)
- [ ] Implementou Frontend (React)
- [ ] Testou API com curl
- [ ] Testou Dashboard no navegador
- [ ] Agendou ETL (cron, airflow, etc)

---

## 📞 SUPORTE RÁPIDO

**Erro: pyarrow não encontrado**
```bash
pip install pyarrow
```

**Erro: Conexão PostgreSQL**
```bash
psql -h 177.7.55.100 -p 32775 -U analytica -d hacka-energinn
```

**Erro: Sem espaço em disco**
```bash
df -h /home/juan/Desktop/ons_data_lake/lake/
# Se necessário limpar: rm -rf lake/silver/*
```

**Ler arquivo Parquet manualmente**
```python
import pandas as pd
df = pd.read_parquet("/caminho/para/arquivo.parquet")
print(df)
```

---

## 📚 LEITURA RECOMENDADA (Ordem)

1. **Este arquivo** (você está aqui) — 5 min
2. `README.md` — 5 min
3. `SUMARIO_EXECUTIVO.md` — 2 min
4. `ETL_CAMADA_PRATA_DOCUMENTACAO_COMPLETA.md` — 30 min
5. `GUIA_IMPLEMENTACAO_BACKEND_FRONTEND.md` — 60 min (código para copiar)

---

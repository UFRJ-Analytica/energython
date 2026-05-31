# ETL UNIFICADO - CAMADA PRATA (SILVER)
## Documentação Completa para Front-End e Back-End

---

## 📋 ÍNDICE
1. [Visão Geral](#visão-geral)
2. [Contexto do Banco de Dados](#contexto-do-banco-de-dados)
3. [O Que o ETL Faz](#o-que-o-etl-faz)
4. [Operações de Limpeza](#operações-de-limpeza)
5. [Estrutura de Saída](#estrutura-de-saída)
6. [Como Rodar](#como-rodar)
7. [Consumo no Backend](#consumo-no-backend)
8. [Consumo no Frontend](#consumo-no-frontend)
9. [Agregações](#agregações)
10. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O ETL Unificado transforma dados brutos do PostgreSQL em uma camada **PRATA (silver)** e **AGREGAÇÕES** para consumo seguro do backend e frontend.

**Fluxo:**
```
PostgreSQL (raw, confuso) 
  ↓
[ETL unificado.py]
  - Remove NULLs
  - Remove outliers (IQR)
  - Normaliza strings
  - Particiona por estado/ano/mês
  ↓
Parquet particionado (silver/)
  ↓
Agregações (agg/)
  ↓
Backend / Frontend
```

---

## 🗄️ Contexto do Banco de Dados

**Banco:** `hacka-energinn` no PostgreSQL (177.7.55.100:32775)  
**Usuário:** analytica  
**Total de tabelas:** 26  

### Tabelas Principais Processadas

| Tabela | Linhas | Período | Granularidade | Status |
|--------|--------|---------|---------------|--------|
| **geracao_usina_2** | 15.0 M | 2003-2026 | Horário | ✓ Processada |
| **disponibilidade_usina** | 3.4 M | 2019-2026 | Horário | ✓ Processada |
| **fator_capacidade_2** | 13.8 M | 2014-2026 | Horário | ✓ Processada + H3 |
| **restricao_coff_eolica_detail** | 49.5 M | 2021-2026 | 30min | ✓ Processada |
| **ccee_pld_horario** | 38 K | - | Horário | ✓ Processada |

---

## ⚙️ O Que o ETL Faz

### 1. Remove Nulos em Colunas-Chave
- Para **geracao_usina_2**: `din_instante`, `id_estado`, `nom_usina`
- Para **disponibilidade_usina**: `din_instante`, `id_estado`, `nom_usina`
- Para **fator_capacidade_2**: `din_instante`, `id_estado`, `nom_pontoconexao`
- Para **restricao_coff_eolica_detail**: `din_instante`, `id_estado`, `nom_usina`

### 2. Remove Outliers (IQR - Interquartile Range)
Usa método estatístico padrão:
```
Q1 = 25º percentil
Q3 = 75º percentil
IQR = Q3 - Q1
Limite inferior = Q1 - 1.5 × IQR
Limite superior = Q3 + 1.5 × IQR

Mantém: valor >= limite_inferior AND valor <= limite_superior
Remove: valor < limite_inferior OR valor > limite_superior
```

**Exemplo (geracao_usina_2):**
- Q1 = 0.00 MW
- Q3 = 70.52 MW
- IQR = 70.52
- **Range válido: [-105.77, 176.29] MW**

### 3. Normaliza Strings
- `TRIM()`: remove espaços em branco
- `LOWER()`: converte para minúsculas
- Colunas-alvo: `nom_estado`, `nom_usina`, `nom_subsistema`, `nom_tipousina`, `nom_tipocombustivel`

**Antes:** `"  BAHIA  "` → **Depois:** `"bahia"`

### 4. Particionamento por Estado/Ano/Mês
Estrutura Parquet:
```
silver/geracao_usina_2/
  ├── id_estado=BA/
  │   ├── ano=2024/
  │   │   ├── mes=01/
  │   │   │   └── part-00000.parquet
  │   │   └── mes=02/
  │   │       └── part-00000.parquet
  ├── id_estado=SP/
  │   └── ...
```

**Benefício:** Queries muito mais rápidas (filtra por estado sem ler tudo).

### 5. Adiciona H3 (Dados Geográficos)
Para **fator_capacidade_2** com latitude/longitude:
- Gera **H3 resolução 6** (hexágono ~1.2 km²)
- Gera **H3 resolução 7** (hexágono ~150 m²)

**Uso:** Agregações geoespaciais, mapas interativos.

### 6. Agregações Automáticas
- **agg_geracao_estado_dia**: SUM e AVG diários por estado
- **agg_fator_capacidade_estado_mes**: AVG mensais por estado

---

## 🧹 Operações de Limpeza

### Exemplo Real: geracao_usina_2 (500K linhas)

```
Input:  500.000 linhas
Filtro key_cols (nulos):     0 removidas
Filtro outliers (IQR):       0 removidas
Output: 500.000 linhas
Taxa limpeza: 0%
```

*Nota: Dados já estava relativamente limpo. Com dados datalake confuso (raw), esperamos 5-15% de remoção.*

---

## 📂 Estrutura de Saída

### Diretório Silver (Tratado)
```
/home/juan/Desktop/ons_data_lake/lake/silver/
├── geracao_usina_2/
│   ├── id_estado=AL/ano=2024/mes=05/...parquet
│   ├── id_estado=BA/ano=2024/mes=05/...parquet
│   └── ...
├── disponibilidade_usina/
├── fator_capacidade_2/
│   ├── h3_res6 (coluna adicional)
│   ├── h3_res7 (coluna adicional)
├── restricao_coff_eolica_detail/
└── ccee_pld_horario/
```

### Diretório Agg (Agregado)
```
/home/juan/Desktop/ons_data_lake/lake/agg/
├── agg_geracao_estado_dia/
│   ├── id_estado=AL/part-0000.parquet  (data, geracao_total, geracao_media, etc)
│   ├── id_estado=BA/part-0000.parquet
│   └── ...
├── agg_fator_capacidade_estado_mes/
│   ├── id_estado=AL/part-0000.parquet  (mes, fator_media, geracao_verificada_media)
│   └── ...
```

---

## 🚀 Como Rodar

### Prerequisitos
```bash
pip install psycopg2-binary pandas pyarrow duckdb h3 -q
```

### Execução Básica (todas as tabelas)
```bash
cd /home/juan/Desktop/ons_data_lake/spark_duck
python etl_unificado.py
```

**Tempo estimado:** ~2-3 horas (15M + 3.4M + 13.8M + 49.5M = 81M linhas)

### Com Limite (teste rápido)
```bash
python etl_unificado.py --limit 500000
```

**Tempo:** ~20 segundos (para debug)

### Apenas Uma Tabela
```bash
python etl_unificado.py --tables geracao_usina_2
```

### Sem Agregações
```bash
python etl_unificado.py --skip-agg
```

---

## 📊 Consumo no Backend

### Opção 1: Consumir Agregações (RECOMENDADO)

Mais rápido, menos dados.

```python
import pandas as pd
import pyarrow.parquet as pq

# Agregação: geração por estado e dia
df_agg = pd.read_parquet(
    "/home/juan/Desktop/ons_data_lake/lake/agg/agg_geracao_estado_dia/id_estado=BA/",
    columns=["data", "geracao_total_mw", "geracao_media_mw"]
)

# Filtro de data
df_agg = df_agg[df_agg["data"] >= "2024-01-01"]
print(df_agg.head())
```

### Opção 2: Consumir Silver Completo

Todas as dimensões.

```python
# Geração completa para um estado
df_silver = pd.read_parquet(
    "/home/juan/Desktop/ons_data_lake/lake/silver/geracao_usina_2/id_estado=SP/ano=2024/mes=05/",
    columns=["din_instante", "nom_usina", "nom_tipousina", "val_geracao"]
)
```

### Opção 3: API REST (Recomendado para Frontend)

```python
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

@app.get("/api/geracao/estado/{estado}")
def get_geracao(estado: str, data_inicio: str = None, data_fim: str = None):
    df = pd.read_parquet(
        f"/home/juan/Desktop/ons_data_lake/lake/agg/agg_geracao_estado_dia/id_estado={estado}/"
    )
    if data_inicio:
        df = df[df["data"] >= data_inicio]
    if data_fim:
        df = df[df["data"] <= data_fim]
    return df.to_dict(orient="records")

@app.get("/api/fator-capacidade/estado/{estado}")
def get_fator(estado: str, mes: str = None):
    df = pd.read_parquet(
        f"/home/juan/Desktop/ons_data_lake/lake/agg/agg_fator_capacidade_estado_mes/id_estado={estado}/"
    )
    if mes:
        df = df[df["mes"] == mes]
    return df.to_dict(orient="records")
```

---

## 💻 Consumo no Frontend

### Opção 1: Dashboard com Agregações (JS/React)

```javascript
const API_BASE = "http://localhost:8000/api";

async function getGeracaoEstado(estado, dataInicio, dataFim) {
  const params = new URLSearchParams({
    data_inicio: dataInicio,
    data_fim: dataFim
  });
  const res = await fetch(`${API_BASE}/geracao/estado/${estado}?${params}`);
  return res.json();
}

// Uso
const dados = await getGeracaoEstado("BA", "2024-01-01", "2024-03-31");
console.log(dados); // Array de {data, geracao_total_mw, geracao_media_mw, ...}
```

### Opção 2: Gráfico com Chart.js

```html
<canvas id="geracaoChart"></canvas>

<script>
  async function renderChart() {
    const dados = await getGeracaoEstado("BA", "2024-01-01", "2024-03-31");
    
    const ctx = document.getElementById("geracaoChart").getContext("2d");
    new Chart(ctx, {
      type: "line",
      data: {
        labels: dados.map(d => d.data),
        datasets: [{
          label: "Geração Total (MW)",
          data: dados.map(d => d.geracao_total_mw),
          borderColor: "rgb(75, 192, 192)",
          tension: 0.1
        }]
      }
    });
  }
  
  renderChart();
</script>
```

### Opção 3: Mapa com Folium (Python/Backend)

```python
import folium
import pandas as pd

df = pd.read_parquet(
    "/home/juan/Desktop/ons_data_lake/lake/silver/fator_capacidade_2/..."
)

# Usa H3 para agregação geoespacial
map_obj = folium.Map(location=[-15.79, -47.88], zoom_start=6)

for _, row in df.iterrows():
    if row["h3_res7"]:
        folium.Marker(
            location=[row["val_latitudesecoletora"], row["val_longitudesecoletora"]],
            popup=f"{row['nom_localizacao']}: {row['val_fatorcapacidade']:.2%}"
        ).add_to(map_obj)

map_obj.save("mapa_capacidade.html")
```

---

## 📈 Agregações Disponíveis

### 1. agg_geracao_estado_dia
Soma de geração por estado e dia.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_estado` | TEXT | Código do estado (partition key) |
| `nom_estado` | TEXT | Nome do estado |
| `data` | DATE | Data |
| `registros` | BIGINT | Quantidade de usinas/eventos |
| `geracao_total_mw` | DOUBLE | Soma em MW |
| `geracao_media_mw` | DOUBLE | Média em MW |
| `geracao_min_mw` | DOUBLE | Mínimo em MW |
| `geracao_max_mw` | DOUBLE | Máximo em MW |

**Exemplo de query:**
```sql
SELECT data, geracao_total_mw 
FROM agg_geracao_estado_dia 
WHERE id_estado='SP' AND data >= '2024-01-01'
ORDER BY data
```

### 2. agg_fator_capacidade_estado_mes
Média de fator de capacidade por estado e mês.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `id_estado` | TEXT | Código do estado (partition key) |
| `nom_estado` | TEXT | Nome do estado |
| `mes` | DATE | Primeiro dia do mês |
| `registros` | BIGINT | Quantidade de usinas/eventos |
| `fator_capacidade_media` | DOUBLE | Média (0.0 a 1.0) |
| `geracao_verificada_media_mw` | DOUBLE | Média em MW |
| `capacidade_instalada_media_mw` | DOUBLE | Média em MW |

---

## 🔍 Troubleshooting

### Problema: "ModuleNotFoundError: pyarrow"
```bash
pip install pyarrow -q
```

### Problema: "ModuleNotFoundError: duckdb"
```bash
pip install duckdb -q
# (só necessário para agregações)
```

### Problema: "ModuleNotFoundError: h3"
```bash
pip install h3 -q
# (opcional, só para H3)
```

### Problema: Conexão PostgreSQL recusada
1. Verificar credentials:

2. Verificar firewall/rede.

### Problema: Sem espaço em disco
Verificar espaço:
```bash
df -h /home/juan/Desktop/ons_data_lake/lake/
```

Se necessário, limpar agregações antigas:
```bash
rm -rf /home/juan/Desktop/ons_data_lake/lake/silver/*
```

---

## 📝 Logs e Monitoramento

Logs salvos em console durante execução. Para redirecionar para arquivo:

```bash
python etl_unificado.py 2>&1 | tee etl_$(date +%Y%m%d_%H%M%S).log
```

Monitorar progresso em tempo real:
```bash
tail -f etl_*.log
```

---

## ✅ Checklist de Validação

Após rodar o ETL:

- [ ] Diretório `silver/` foi criado
- [ ] Subdiretórios por tabela existem
- [ ] Arquivos `.parquet` foram gerados
- [ ] Partições por estado/ano/mês estão presentes
- [ ] Diretório `agg/` foi criado com agregações
- [ ] Backend consegue ler arquivos Parquet
- [ ] Frontend consegue consumir APIs

---

## 🎓 Referências

- **IQR (Interquartile Range):** Método estatístico padrão para outlier detection
- **H3:** Sistema de indexação hexagonal da Uber para geoespacial
- **Parquet:** Formato colunar otimizado para analytics
- **Particionamento:** Estratégia de organização de arquivos para query performance

---

**Gerado em:** 30/05/2026  
**Versão:** 1.0  
**Mantido por:** Juan (Energy Data Team)

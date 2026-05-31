# GUIA DE IMPLEMENTAÇÃO - BACKEND E FRONTEND

## 🎯 Objetivo
Consumir dados limpos e agregados do ETL para servir dashboards e aplicações.

---

## 📌 BACKEND (Python FastAPI)

### 1. Estrutura de Projeto
```
backend/
├── main.py                 # App principal
├── routes/
│   ├── geracao.py         # Endpoints de geração
│   ├── capacidade.py      # Endpoints de capacidade
│   └── restricao.py       # Endpoints de restrições
├── models/
│   └── schemas.py         # Pydantic models
├── services/
│   └── data_loader.py     # Lógica de leitura Parquet
└── requirements.txt
```

### 2. requirements.txt
```
fastapi==0.104.1
uvicorn==0.24.0
pandas==2.1.3
pyarrow==13.0.0
pydantic==2.5.0
python-dotenv==1.0.0
```

### 3. main.py
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import geracao, capacidade

app = FastAPI(title="Energia API", version="1.0.0")

# CORS (permitir frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rotas
app.include_router(geracao.router, prefix="/api/geracao", tags=["Geração"])
app.include_router(capacidade.router, prefix="/api/capacidade", tags=["Capacidade"])

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 4. services/data_loader.py
```python
import pandas as pd
from pathlib import Path
from typing import Optional
from datetime import datetime

LAKE_PATH = Path("/home/juan/Desktop/ons_data_lake/lake")

class DataLoader:
    
    @staticmethod
    def get_geracao_estado_dia(
        estado: str,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Carrega agregação de geração diária por estado."""
        path = LAKE_PATH / "agg" / "agg_geracao_estado_dia" / f"id_estado={estado}"
        
        if not path.exists():
            raise FileNotFoundError(f"Estado {estado} não encontrado")
        
        df = pd.read_parquet(path)
        
        # Filtros de data
        if data_inicio:
            df = df[df["data"] >= data_inicio]
        if data_fim:
            df = df[df["data"] <= data_fim]
        
        # Limite
        if limit:
            df = df.head(limit)
        
        return df.sort_values("data")
    
    @staticmethod
    def get_fator_capacidade_estado_mes(
        estado: str,
        mes_inicio: Optional[str] = None,
        mes_fim: Optional[str] = None
    ) -> pd.DataFrame:
        """Carrega agregação de fator de capacidade mensal por estado."""
        path = LAKE_PATH / "agg" / "agg_fator_capacidade_estado_mes" / f"id_estado={estado}"
        
        if not path.exists():
            raise FileNotFoundError(f"Estado {estado} não encontrado")
        
        df = pd.read_parquet(path)
        
        if mes_inicio:
            df = df[df["mes"] >= mes_inicio]
        if mes_fim:
            df = df[df["mes"] <= mes_fim]
        
        return df.sort_values("mes")
    
    @staticmethod
    def get_silver_completo(
        tabela: str,
        estado: str,
        ano: Optional[int] = None,
        mes: Optional[int] = None
    ) -> pd.DataFrame:
        """Carrega dados silver completos (todas as dimensões)."""
        path = LAKE_PATH / "silver" / tabela / f"id_estado={estado}"
        
        if ano:
            path = path / f"ano={ano}"
            if mes:
                path = path / f"mes={mes}"
        
        if not path.exists():
            raise FileNotFoundError(f"Caminho não encontrado: {path}")
        
        return pd.read_parquet(path)
```

### 5. routes/geracao.py
```python
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from services.data_loader import DataLoader
from models.schemas import GeracaoDiaResponse

router = APIRouter()
loader = DataLoader()

@router.get("/estado/{estado}/dia", response_model=List[GeracaoDiaResponse])
def get_geracao_dia(
    estado: str,
    data_inicio: Optional[str] = Query(None, description="YYYY-MM-DD"),
    data_fim: Optional[str] = Query(None, description="YYYY-MM-DD"),
    limit: Optional[int] = Query(365, ge=1, le=10000)
):
    """Retorna geração agregada diária por estado."""
    try:
        df = loader.get_geracao_estado_dia(
            estado.upper(),
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )
        return df.to_dict(orient="records")
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/estados")
def list_estados():
    """Lista todos os estados disponíveis."""
    from pathlib import Path
    base = Path("/home/juan/Desktop/ons_data_lake/lake/agg/agg_geracao_estado_dia")
    estados = [d.name.replace("id_estado=", "") for d in base.glob("id_estado=*")]
    return {"estados": sorted(estados)}
```

### 6. models/schemas.py
```python
from pydantic import BaseModel
from datetime import date
from typing import Optional

class GeracaoDiaResponse(BaseModel):
    id_estado: str
    nom_estado: str
    data: date
    registros: int
    geracao_total_mw: float
    geracao_media_mw: float
    geracao_min_mw: float
    geracao_max_mw: float

class CapacidadeMesResponse(BaseModel):
    id_estado: str
    nom_estado: str
    mes: date
    registros: int
    fator_capacidade_media: float
    geracao_verificada_media_mw: float
    capacidade_instalada_media_mw: float
```

### 7. Executar
```bash
# Instalar dependências
pip install -r requirements.txt

# Rodar servidor
python main.py

# Testar
curl http://localhost:8000/api/geracao/estados
curl http://localhost:8000/api/geracao/estado/SP/dia
```

---

## 🎨 FRONTEND (React + TypeScript)

### 1. Estrutura de Projeto
```
frontend/
├── src/
│   ├── api/
│   │   └── energiaApi.ts         # Chamadas HTTP
│   ├── components/
│   │   ├── GeracaoChart.tsx
│   │   ├── CapacidadeTable.tsx
│   │   └── StateFilter.tsx
│   ├── hooks/
│   │   └── useGeracao.ts         # Custom hook
│   ├── types/
│   │   └── energia.ts            # TypeScript types
│   ├── pages/
│   │   └── Dashboard.tsx
│   └── App.tsx
├── package.json
└── vite.config.ts
```

### 2. package.json
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.6.0",
    "chart.js": "^4.4.0",
    "react-chartjs-2": "^5.2.0",
    "date-fns": "^2.30.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/node": "^20.0.0",
    "typescript": "^5.3.0"
  }
}
```

### 3. types/energia.ts
```typescript
export interface GeracaoDia {
  id_estado: string;
  nom_estado: string;
  data: string; // "YYYY-MM-DD"
  registros: number;
  geracao_total_mw: number;
  geracao_media_mw: number;
  geracao_min_mw: number;
  geracao_max_mw: number;
}

export interface CapacidadeMes {
  id_estado: string;
  nom_estado: string;
  mes: string; // "YYYY-MM-01"
  registros: number;
  fator_capacidade_media: number;
  geracao_verificada_media_mw: number;
  capacidade_instalada_media_mw: number;
}
```

### 4. api/energiaApi.ts
```typescript
import axios from "axios";
import { GeracaoDia } from "../types/energia";

const API_BASE = "http://localhost:8000/api";

export const energiaApi = {
  async getEstados(): Promise<string[]> {
    const { data } = await axios.get(`${API_BASE}/geracao/estados`);
    return data.estados;
  },

  async getGeracaoDia(
    estado: string,
    dataInicio?: string,
    dataFim?: string,
    limit?: number
  ): Promise<GeracaoDia[]> {
    const params = new URLSearchParams();
    if (dataInicio) params.append("data_inicio", dataInicio);
    if (dataFim) params.append("data_fim", dataFim);
    if (limit) params.append("limit", String(limit));

    const { data } = await axios.get(
      `${API_BASE}/geracao/estado/${estado}/dia?${params}`
    );
    return data;
  },

  async getCapacidadeMes(estado: string, mesInicio?: string, mesFim?: string) {
    const params = new URLSearchParams();
    if (mesInicio) params.append("mes_inicio", mesInicio);
    if (mesFim) params.append("mes_fim", mesFim);

    const { data } = await axios.get(
      `${API_BASE}/capacidade/estado/${estado}/mes?${params}`
    );
    return data;
  }
};
```

### 5. hooks/useGeracao.ts
```typescript
import { useState, useEffect } from "react";
import { energiaApi } from "../api/energiaApi";
import { GeracaoDia } from "../types/energia";

export function useGeracao(estado: string, dataInicio?: string, dataFim?: string) {
  const [dados, setDados] = useState<GeracaoDia[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        setError(null);
        const result = await energiaApi.getGeracaoDia(
          estado,
          dataInicio,
          dataFim,
          365
        );
        setDados(result);
      } catch (err: any) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [estado, dataInicio, dataFim]);

  return { dados, loading, error };
}
```

### 6. components/GeracaoChart.tsx
```typescript
import React from "react";
import { Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend } from "chart.js";
import { Line } from "react-chartjs-2";
import { GeracaoDia } from "../types/energia";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend);

interface Props {
  dados: GeracaoDia[];
  loading: boolean;
}

export function GeracaoChart({ dados, loading }: Props) {
  if (loading) return <div>Carregando...</div>;
  if (!dados.length) return <div>Sem dados</div>;

  const chartData = {
    labels: dados.map(d => d.data),
    datasets: [
      {
        label: "Geração Total (MW)",
        data: dados.map(d => d.geracao_total_mw),
        borderColor: "rgb(75, 192, 192)",
        backgroundColor: "rgba(75, 192, 192, 0.1)",
        tension: 0.4,
      },
      {
        label: "Média (MW)",
        data: dados.map(d => d.geracao_media_mw),
        borderColor: "rgb(255, 159, 64)",
        backgroundColor: "rgba(255, 159, 64, 0.1)",
        tension: 0.4,
      }
    ]
  };

  return (
    <div style={{ height: "400px" }}>
      <Line data={chartData} options={{ responsive: true, maintainAspectRatio: false }} />
    </div>
  );
}
```

### 7. pages/Dashboard.tsx
```typescript
import React, { useState } from "react";
import { useGeracao } from "../hooks/useGeracao";
import { GeracaoChart } from "../components/GeracaoChart";
import { energiaApi } from "../api/energiaApi";

export function Dashboard() {
  const [estado, setEstado] = useState("SP");
  const [estados, setEstados] = React.useState<string[]>([]);
  const [dataInicio, setDataInicio] = useState("2024-01-01");
  const [dataFim, setDataFim] = useState("2024-03-31");

  const { dados, loading, error } = useGeracao(estado, dataInicio, dataFim);

  React.useEffect(() => {
    energiaApi.getEstados().then(setEstados);
  }, []);

  return (
    <div style={{ padding: "20px" }}>
      <h1>Dashboard de Geração</h1>

      <div style={{ marginBottom: "20px" }}>
        <label>
          Estado:
          <select value={estado} onChange={(e) => setEstado(e.target.value)}>
            {estados.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </label>

        <label style={{ marginLeft: "20px" }}>
          De:
          <input type="date" value={dataInicio} onChange={(e) => setDataInicio(e.target.value)} />
        </label>

        <label style={{ marginLeft: "20px" }}>
          Até:
          <input type="date" value={dataFim} onChange={(e) => setDataFim(e.target.value)} />
        </label>
      </div>

      {error && <div style={{ color: "red" }}>Erro: {error}</div>}

      <GeracaoChart dados={dados} loading={loading} />

      <div style={{ marginTop: "20px" }}>
        <h3>Estatísticas</h3>
        {dados.length > 0 && (
          <p>
            Máximo: {Math.max(...dados.map(d => d.geracao_max_mw)).toFixed(2)} MW | 
            Mínimo: {Math.min(...dados.map(d => d.geracao_min_mw)).toFixed(2)} MW | 
            Média: {(dados.reduce((s, d) => s + d.geracao_media_mw, 0) / dados.length).toFixed(2)} MW
          </p>
        )}
      </div>
    </div>
  );
}
```

### 8. Executar
```bash
# Instalar
npm install

# Rodar dev server
npm run dev

# Acessa http://localhost:5173
```

---

## 🔗 Integração Completa

### 1. Backend rodando na porta 8000
```bash
cd backend && python main.py
# http://localhost:8000
# http://localhost:8000/docs (Swagger UI)
```

### 2. Frontend rodando na porta 5173
```bash
cd frontend && npm run dev
# http://localhost:5173
```

### 3. Teste de Ponta a Ponta
```bash
# 1. Verificar saúde do backend
curl http://localhost:8000/health

# 2. Listar estados
curl http://localhost:8000/api/geracao/estados

# 3. Trazer dados de geração
curl "http://localhost:8000/api/geracao/estado/SP/dia?data_inicio=2024-01-01&data_fim=2024-03-31"

# 4. Abrir dashboard no navegador
# http://localhost:5173
```

---

## ✅ Checklist de Implementação

- [ ] Backend: Criar estrutura FastAPI
- [ ] Backend: Implementar data_loader.py
- [ ] Backend: Criar rotas (/geracao, /capacidade)
- [ ] Backend: Testar com curl
- [ ] Backend: Visualizar Swagger em /docs
- [ ] Frontend: Criar projeto React
- [ ] Frontend: Implementar API client
- [ ] Frontend: Criar componentes (Chart, Table, Filter)
- [ ] Frontend: Conectar ao backend
- [ ] Frontend: Testar dashboard
- [ ] Integração: Testar ponta a ponta

---

**Data:** 30/05/2026  
**Status:** Pronto para implementação

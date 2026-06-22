from __future__ import annotations

from pydantic import BaseModel, Field


class DebugKpiOut(BaseModel):
    label: str
    value: float | int | str
    unit: str | None = None
    description: str | None = None


class DebugUsinaScoreOut(BaseModel):
    usina_id: str
    nome: str
    fonte: str | None = None
    submercado: str | None = None
    potencia_mw: float | None = None
    latitude: float | None = None
    longitude: float | None = None
    total_corte_mwh: float = 0.0
    total_perda_reais: float = 0.0
    percentual_corte: float = 0.0
    percentual_ressarcivel: float = 0.0
    fator_capacidade: float | None = None
    health_score: float = 50.0


class DebugHealthDadosOut(BaseModel):
    status: str
    repository: str
    total_usinas_amostra: int
    observacoes: list[str] = Field(default_factory=list)
    amostra_usinas: list[dict] = Field(default_factory=list)


class DebugControlTowerOut(BaseModel):
    kpis: list[DebugKpiOut]
    ranking: list[DebugUsinaScoreOut]
    metadata: dict = Field(default_factory=dict)


class DebugRankingOut(BaseModel):
    melhores: list[DebugUsinaScoreOut]
    piores: list[DebugUsinaScoreOut]
    metadata: dict = Field(default_factory=dict)


class DebugUnidadesOut(BaseModel):
    kpis: list[DebugKpiOut]
    unidades: list[DebugUsinaScoreOut]
    metadata: dict = Field(default_factory=dict)


class DebugSeriePointOut(BaseModel):
    timestamp: str
    geracao_mwh: float
    referencia_mwh: float | None = None
    corte_mwh: float = 0.0
    cod_razaorestricao: str | None = None
    cod_origemrestricao: str | None = None


class DebugUsinaDetalheOut(BaseModel):
    usina: dict
    kpis: list[DebugKpiOut]
    serie_amostra: list[DebugSeriePointOut]
    score: DebugUsinaScoreOut
    metadata: dict = Field(default_factory=dict)


class DebugAnomaliaOut(BaseModel):
    timestamp: str
    geracao_mwh: float
    referencia_mwh: float | None = None
    corte_mwh: float = 0.0
    score_anomalia: float
    metodo: str


class DebugAnomaliasOut(BaseModel):
    usina_id: str
    total_pontos: int
    total_anomalias: int
    metodo: str
    anomalias: list[DebugAnomaliaOut]


class DebugForecastPointOut(BaseModel):
    timestamp: str
    real_mwh: float | None = None
    baseline_mwh: float | None = None
    forecast_mwh: float
    p10_mwh: float | None = None
    p90_mwh: float | None = None


class DebugForecastOut(BaseModel):
    usina_id: str
    modelo: str
    horizonte: int
    mae_baseline: float | None = None
    mae_hibrido: float | None = None
    ganho_pct: float | None = None
    pontos: list[DebugForecastPointOut]
    feature_importance: list[dict] = Field(default_factory=list)


class DebugNoticiaOut(BaseModel):
    titulo: str
    link: str
    data: str | None = None
    fonte: str | None = None
    relevancia: float = 0.0
    resumo: str | None = None


class DebugNoticiasOut(BaseModel):
    usina_id: str
    consulta: str
    total_bruto: int
    itens: list[DebugNoticiaOut]
    erro: str | None = None
    metadata: dict = Field(default_factory=dict)


class DebugLabOut(BaseModel):
    usina_id: str
    notebook_name: str
    csv_name: str
    metadata: dict = Field(default_factory=dict)
    notebook: dict
    serie_csv_preview: str

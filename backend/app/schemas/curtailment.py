from pydantic import BaseModel


class HistoricoCortesOut(BaseModel):
    usina_id: str
    total_mwh_restringido: float
    numero_eventos: int
    por_razao: dict[str, float]
    serie: list[dict]


class RiscoOut(BaseModel):
    usina_id: str
    horizonte_horas: int
    previsoes: list[dict]
    modelo: str | None = None


class RiscoDetalhadoOut(BaseModel):
    usina_id: str
    horizonte_horas: int
    modelo: str
    tipo_dado: str = "previsao"
    previsoes: list[dict]
    alertas: list[dict]
    resumo: dict
    decomposicao_temporal: dict | None = None
    knn_insights: dict | None = None

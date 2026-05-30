from pydantic import BaseModel


class UsinaOut(BaseModel):
    usina_id: str
    nome: str
    fonte: str
    potencia_mw: float
    submercado: str


class UsinaListOut(BaseModel):
    total_count: int
    limit: int
    offset: int
    items: list[UsinaOut]


class UsinaResumoOut(BaseModel):
    usina: UsinaOut
    total_corte_mwh: float
    total_perda_reais: float
    percentual_ressarcivel: float
    total_eventos_corte: int
    ticket_medio_evento_reais: float
    risco_48h: list[dict]

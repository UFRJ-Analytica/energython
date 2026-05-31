from pydantic import BaseModel

from app.schemas.common import MetaOut


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
    metadata: MetaOut
    items: list[UsinaOut]


class PerdaEsperadaOut(BaseModel):
    valor_reais: float
    horizonte_dias: int
    metodo: str
    observacao: str | None = None


class UsinaResumoOut(BaseModel):
    usina: UsinaOut
    total_corte_mwh: float
    total_perda_reais: float
    percentual_ressarcivel: float
    total_eventos_corte: int
    ticket_medio_evento_reais: float
    metadata: MetaOut
    perda_esperada_30d: PerdaEsperadaOut

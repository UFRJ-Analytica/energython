from pydantic import BaseModel

from app.schemas.common import MetaOut, PaginationOut


class PerdaSerieItem(BaseModel):
    timestamp: str
    energia_restringida_mwh: float
    pld_reais_mwh: float
    perda_reais: float
    razao_restricao: str


class QualidadeDadosPerda(BaseModel):
    status: str
    pld_faltante_eventos: int
    total_eventos: int


class PerdaOut(BaseModel):
    usina_id: str
    total_perda_reais: float
    total_energia_restringida_mwh: float
    por_razao: dict[str, float]
    qualidade_dados: QualidadeDadosPerda
    metadata: MetaOut
    paginacao_serie: PaginationOut
    serie: list[PerdaSerieItem]


class ExposicaoOut(BaseModel):
    usina_id: str
    horizonte_horas: int
    exposicao_estimada_reais: float
    premissas: dict

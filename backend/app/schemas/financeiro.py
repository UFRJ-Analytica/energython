from pydantic import BaseModel

from app.schemas.common import MetaOut, PaginationOut


class PerdaSerieItem(BaseModel):
    timestamp: str
    energia_restringida_mwh: float
    pld_reais_mwh: float
    perda_reais: float
    energia_ressarcivel_mwh: float | None = None
    perda_ressarcivel_reais: float | None = None
    razao_restricao: str
    cod_razaorestricao: str | None = None
    cod_origemrestricao: str | None = None
    referencia_oficial: bool | None = None
    referencia_calculo_curtailment: str | None = None
    nivel_semantico: str | None = None


class PerdaEventoItem(BaseModel):
    event_id: str
    usina_id: str
    inicio: str
    fim: str
    duracao_horas: float
    n_intervalos: int
    energia_restringida_mwh: float
    perda_total_reais: float
    cod_razaorestricao: str | None = None
    cod_origemrestricao: str | None = None
    razao_normalizada: str | None = None
    origem_normalizada: str | None = None
    elegibilidade_status: str
    evidence_score: int
    source_interval_ids: list[str]
    gap_detectado: bool = False


class QualidadeDadosPerda(BaseModel):
    status: str
    pld_faltante_eventos: int
    total_eventos: int
    pld_faltante_intervalos: int = 0
    total_eventos_curtailment: int = 0
    total_intervalos_restricao: int = 0
    eventos_sem_origem: int = 0
    energia_unidade_validada: bool = False
    referencia_oficial_intervalos: int = 0
    referencia_estimativa_intervalos: int = 0
    ressarcivel_oficial_intervalos: int = 0


class PerdaOut(BaseModel):
    usina_id: str
    total_perda_reais: float
    total_energia_restringida_mwh: float
    total_perda_ressarcivel_reais: float | None = None
    total_energia_ressarcivel_mwh: float | None = None
    por_razao: dict[str, float]
    qualidade_dados: QualidadeDadosPerda
    metadata: MetaOut
    paginacao_serie: PaginationOut
    eventos: list[PerdaEventoItem] = []
    serie: list[PerdaSerieItem]


class ExposicaoOut(BaseModel):
    usina_id: str
    horizonte_horas: int
    exposicao_estimada_reais: float
    premissas: dict
    serie_previsao: list[dict] = []


class PrevisaoPerdasOut(BaseModel):
    usina_id: str
    metodo_previsao: str
    horizonte_horas: int
    historico_horas: int
    resumo: dict
    serie_historico: list[dict] = []
    serie_previsao: list[dict] = []

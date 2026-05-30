from pydantic import BaseModel


class ElegibilidadeEventoOut(BaseModel):
    timestamp: str
    razao_restricao: str
    energia_restringida_mwh: float
    elegivel_ressarcimento: bool
    valor_potencial_reais: float


class ElegibilidadeOut(BaseModel):
    usina_id: str
    total_potencial_ressarcivel_reais: float
    eventos: list[ElegibilidadeEventoOut]


class DossieIn(BaseModel):
    inicio: str
    fim: str


class DossieOut(BaseModel):
    usina_id: str
    dossie_markdown: str


class ConsultaRegulatoriaIn(BaseModel):
    pergunta: str


class ConsultaRegulatoriaOut(BaseModel):
    resposta: str
    fontes: list[str]

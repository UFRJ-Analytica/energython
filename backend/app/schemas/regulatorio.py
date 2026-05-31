from pydantic import BaseModel

from app.schemas.common import MetaOut, PaginationOut


class ElegibilidadeEventoOut(BaseModel):
    timestamp: str
    razao_restricao: str
    energia_restringida_mwh: float
    elegivel_ressarcimento: bool
    valor_potencial_reais: float
    valor_ressarcivel_pos_franquia_reais: float
    dentro_franquia: bool
    classificacao_fonte: str
    classificacao_confianca: float
    classificacao_justificativa: str
    auditoria_regra: str
    auditoria_motivo_status: str
    auditoria_detalhe: str


class QualidadeClassificacaoOut(BaseModel):
    eventos_totais: int
    eventos_classificados_por_ia: int
    eventos_com_razao_gold: int


class QualidadeDadosRegulatorioOut(BaseModel):
    status: str
    pld_faltante_eventos: int
    eventos_sem_razao_original: int
    eventos_com_razao_normalizada: int
    total_eventos: int


class ElegibilidadeOut(BaseModel):
    usina_id: str
    total_potencial_ressarcivel_reais: float
    total_ressarcivel_pos_franquia_reais: float
    franquia_horas_ano: float
    horas_elegiveis_no_periodo: float
    horas_excedentes_franquia_no_periodo: float
    qualidade_classificacao: QualidadeClassificacaoOut
    qualidade_dados: QualidadeDadosRegulatorioOut
    metadata: MetaOut
    paginacao_eventos: PaginationOut
    eventos: list[ElegibilidadeEventoOut]


class DossieIn(BaseModel):
    inicio: str
    fim: str


class DossieOut(BaseModel):
    usina_id: str
    dossie_markdown: str


class DossieExportIn(BaseModel):
    inicio: str
    fim: str
    formato: str = "markdown"
    franquia_horas_override: float | None = None


class DossieExportOut(BaseModel):
    usina_id: str
    formato: str
    file_name: str
    content_type: str
    content: str


class FluxoRessarcimentoIn(BaseModel):
    inicio: str
    fim: str
    franquia_horas_override: float | None = None


class FluxoRessarcimentoOut(BaseModel):
    usina_id: str
    periodo: dict
    selecao: dict
    resultado_elegibilidade: ElegibilidadeOut
    dossie_markdown: str
    human_in_the_loop: dict
    metadata: dict


class ConsultaRegulatoriaIn(BaseModel):
    pergunta: str


class ConsultaRegulatoriaOut(BaseModel):
    resposta: str
    fontes: list[str]

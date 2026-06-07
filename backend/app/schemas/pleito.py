from __future__ import annotations

from pydantic import BaseModel, Field


class JanelaPleitoOut(BaseModel):
    data_referencia_hoje: str
    dias_restantes_protocolo_ons: int
    pode_pleitear_protocolo_ons: bool
    elegivel_termo: bool
    janela_adesao_termo: str
    sager_dias_restantes: int
    sager_informativo: bool


class ReconciliacaoOut(BaseModel):
    houve_comparacao: bool
    divergencia_significativa: bool = False
    argumento_tecnico: str
    vento_ons_ms: float | None = None
    vento_proprio_ms: float | None = None
    delta_vento_relativo: float | None = None
    geracao_referencia_recalculada_mwh: float | None = None
    delta_geracao_referencia_mwh: float | None = None
    fonte_dados_proprios: str | None = None


class EventoPleitoOut(BaseModel):
    evento_id: str
    timestamp: str
    data_inicio: str
    data_fim: str
    duracao_horas: float
    razao_classificada_ons: str
    razao_original: str | None = None
    origem: str
    geracao_verificada_mwh: float
    geracao_referencia_ons_mwh: float
    energia_restringida_mwh: float
    pld_reais_mwh: float
    submercado: str
    elegivel: bool
    canal_recomendado: str
    motivo_inelegibilidade: str | None = None
    fonte_normativa: str
    confianca: float
    status_franquia: str
    horas_acumuladas_antes: float
    horas_acumuladas_depois: float
    energia_ressarcivel_mwh: float
    valor_pleitavel_reais: float
    destinatario_do_ressarcimento: str
    reconciliacao: ReconciliacaoOut
    janela_prazo: JanelaPleitoOut
    anexos_recomendados: list[str]


class EventosPleitoOut(BaseModel):
    usina_id: str
    periodo: dict
    franquia: dict
    total_eventos: int
    eventos_elegiveis: int
    valor_total_pleitavel_reais: float
    energia_ressarcivel_total_mwh: float
    eventos: list[EventoPleitoOut]
    metadata: dict


class PleitoCreateIn(BaseModel):
    eventos_ids: list[str] = Field(min_length=1)
    canal: str
    inicio: str | None = None
    fim: str | None = None


class PleitoUpdateIn(BaseModel):
    markdown_gerado: str | None = None
    status: str | None = None


class PleitoOut(BaseModel):
    pleito_id: str
    usina_id: str
    canal: str
    eventos_ids: list[str]
    status: str
    markdown_gerado: str
    metadados_json: dict
    criado_em: str
    atualizado_em: str


class PleitoExportOut(BaseModel):
    pleito_id: str
    formato: str
    file_name: str
    content_type: str
    content: str
    content_encoding: str = "utf-8"


class FranquiaStatusOut(BaseModel):
    usina_id: str
    ano: int
    fonte: str
    franquia_horas: float
    fonte_normativa: str
    horas_rel_acumuladas: float
    horas_restantes: float
    metadata: dict

from pydantic import BaseModel, Field


class BessSimularIn(BaseModel):
    potencia_mw: float = Field(gt=0)
    duracao_horas: float = Field(gt=0)
    eficiencia: float = Field(default=0.85, gt=0, le=1)
    capex: float | None = Field(default=None, ge=0)


class BessSimularOut(BaseModel):
    usina_id: str
    energia_recuperada_mwh: float
    receita_recuperada_reais: float
    percentual_mitigado: float
    capex: float | None = None
    payback_anos: float | None = None
    dimensionamento_com_previsao: dict | None = None

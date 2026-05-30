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

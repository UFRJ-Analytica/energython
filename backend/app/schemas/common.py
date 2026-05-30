from pydantic import BaseModel


class MetaOut(BaseModel):
    mvp_scope_applied: bool = True
    mvp_scope: str = "geradoras_renovaveis_submercado_ne"
    data_quality_status: str | None = None

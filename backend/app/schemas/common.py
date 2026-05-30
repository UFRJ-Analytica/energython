from pydantic import BaseModel


class MetaOut(BaseModel):
    mvp_scope_applied: bool = True
    mvp_scope: str = "geradoras_renovaveis_submercado_ne"
    api_contract_version: str = "v1"
    data_quality_status: str | None = None


class PaginationOut(BaseModel):
    total_count: int
    limit: int
    offset: int

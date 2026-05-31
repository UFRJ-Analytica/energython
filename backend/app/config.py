from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+psycopg://user:pass@localhost:5432/curtailiq"
    data_backend: str = "mock"  # mock | postgres
    cors_origins: str = "http://localhost:5173"
    anthropic_api_key: str | None = None
    anthropic_model_fast: str = "claude-haiku-4-5"
    anthropic_model_smart: str = "claude-sonnet-4-5"
    mvp_only_nordeste: bool = True
    curtailment_model_path: str = "models_ml/curtailment_model.pkl"
    curtailment_threshold_mwh: float = 1.0

    # Regras de elegibilidade regulatória (parametrizáveis por ambiente)
    elegivel_confiabilidade: bool = True
    elegivel_indisponibilidade_externa: bool = True
    elegivel_energetico: bool = False
    elegivel_indefinido: bool = False
    regulatorio_policy_version: str = "lei_15269_2025"

    @field_validator("data_backend")
    @classmethod
    def validate_backend(cls, v: str) -> str:
        if v not in {"mock", "postgres"}:
            raise ValueError("DATA_BACKEND must be 'mock' or 'postgres'")
        return v

    @field_validator("regulatorio_policy_version")
    @classmethod
    def validate_regulatorio_policy_version(cls, v: str) -> str:
        allowed = {"lei_15269_2025", "pos_lei_15269_2025", "vigente", "pre_lei_15269_2025", "historica_pre_2025"}
        if v not in allowed:
            raise ValueError("REGULATORIO_POLICY_VERSION invalida")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()

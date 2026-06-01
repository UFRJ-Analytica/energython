from pathlib import Path

from fastapi import Depends

from app.agents.anthropic_client import AnthropicClient
from app.agents.classifier_agent import ClassifierAgent
from app.agents.dossier_agent import DossierAgent
from app.agents.rag_agent import RagAgent
from app.config import Settings, get_settings
from app.domain.policies import RegulatorioPolicy
from app.database import get_db_session
from app.repositories.base import BaseRepository
from app.repositories.mock_repo import MockRepository
from app.services.bess_service import BessService
from app.services.financeiro_service import FinanceiroService
from app.services.regulatorio_service import RegulatorioService
from app.utils.simple_cache import TTLCache

regulatorio_cache = TTLCache(ttl_seconds=1800)


def get_repo(settings: Settings = Depends(get_settings), db=Depends(get_db_session)) -> BaseRepository:
    if settings.data_backend == "postgres":
        from app.repositories.postgres_repo import PostgresRepository

        return PostgresRepository(db=db, mvp_only_nordeste=settings.mvp_only_nordeste)
    return MockRepository(mvp_only_nordeste=settings.mvp_only_nordeste)


def get_financeiro_service(repo: BaseRepository = Depends(get_repo)) -> FinanceiroService:
    return FinanceiroService(repo)


def get_bess_service(repo: BaseRepository = Depends(get_repo)) -> BessService:
    return BessService(repo)


def get_curtailment_service(
    repo: BaseRepository = Depends(get_repo), settings: Settings = Depends(get_settings)
) -> "CurtailmentService":
    from app.services.curtailment_service import CurtailmentService

    return CurtailmentService(
        repo,
        model_path=settings.curtailment_model_path,
        model_mode=settings.curtailment_model_mode,
        advanced_model_path=settings.curtailment_model_advanced_path,
        advanced_module_path=settings.curtailment_advanced_module_path,
    )


def get_regulatorio_service(
    repo: BaseRepository = Depends(get_repo), settings: Settings = Depends(get_settings)
) -> RegulatorioService:
    llm = AnthropicClient(api_key=settings.anthropic_api_key)
    classifier = ClassifierAgent(llm, model=settings.anthropic_model_fast)
    dossier = DossierAgent(llm, model=settings.anthropic_model_smart)
    rag = RagAgent(llm, model=settings.anthropic_model_smart, knowledge_dir=Path(__file__).resolve().parent / "knowledge")
    try:
        policy = RegulatorioPolicy.by_version(settings.regulatorio_policy_version)
    except ValueError:
        policy = RegulatorioPolicy.default()
    regras = {
        "confiabilidade": settings.elegivel_confiabilidade,
        "indisponibilidade_externa": settings.elegivel_indisponibilidade_externa,
        "energetico": settings.elegivel_energetico,
        "indefinido": settings.elegivel_indefinido,
    }
    regras_merged = {**policy.elegibilidade_por_razao, **regras}
    policy = RegulatorioPolicy(
        elegibilidade_por_razao=regras_merged,
        versao_regulatoria=policy.versao_regulatoria,
    )
    return RegulatorioService(
        repo=repo,
        classifier_agent=classifier,
        dossier_agent=dossier,
        rag_agent=rag,
        policy=policy,
        cache=regulatorio_cache,
    )

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import get_repo
from app.repositories.base import BaseRepository
from app.schemas.debug import (
    DebugAnomaliasOut,
    DebugControlTowerOut,
    DebugForecastOut,
    DebugHealthDadosOut,
    DebugLabOut,
    DebugNoticiasOut,
    DebugRankingOut,
    DebugUnidadesOut,
    DebugUsinaDetalheOut,
)
from app.services.debug_service import DebugService
from app.utils.http_errors import api_error

router = APIRouter(prefix="/api/debug", tags=["debug"])


def get_debug_service(repo: BaseRepository = Depends(get_repo)) -> DebugService:
    return DebugService(repo)


@router.get("/health-dados", response_model=DebugHealthDadosOut)
def health_dados(
    limit: int = Query(default=5, ge=1, le=20),
    service: DebugService = Depends(get_debug_service),
):
    return service.health_dados(limit=limit)


@router.get("/control-tower", response_model=DebugControlTowerOut)
def control_tower(
    limit: int = Query(default=20, ge=1, le=100),
    dias: int = Query(default=90, ge=1, le=366),
    service: DebugService = Depends(get_debug_service),
):
    return service.control_tower(limit=limit, dias=dias)


@router.get("/ranking", response_model=DebugRankingOut)
def ranking_debug(
    limit: int = Query(default=30, ge=1, le=100),
    dias: int = Query(default=90, ge=1, le=366),
    service: DebugService = Depends(get_debug_service),
):
    return service.ranking(limit=limit, dias=dias)


@router.get("/unidades", response_model=DebugUnidadesOut)
def unidades_debug(
    limit: int = Query(default=30, ge=1, le=100),
    dias: int = Query(default=90, ge=1, le=366),
    service: DebugService = Depends(get_debug_service),
):
    return service.unidades(limit=limit, dias=dias)


@router.get("/usinas/{usina_id}", response_model=DebugUsinaDetalheOut)
def detalhe_usina_debug(
    usina_id: str,
    dias: int = Query(default=90, ge=1, le=366),
    limit_serie: int = Query(default=200, ge=10, le=2000),
    service: DebugService = Depends(get_debug_service),
):
    try:
        return service.detalhe_usina(usina_id, dias=dias, limit_serie=limit_serie)
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.get("/usinas/{usina_id}/anomalias", response_model=DebugAnomaliasOut)
def anomalias_debug(
    usina_id: str,
    dias: int = Query(default=90, ge=1, le=366),
    limit: int = Query(default=30, ge=1, le=200),
    service: DebugService = Depends(get_debug_service),
):
    try:
        return service.anomalias(usina_id, dias=dias, limit=limit)
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.get("/usinas/{usina_id}/forecast", response_model=DebugForecastOut)
def forecast_debug(
    usina_id: str,
    horizonte: int = Query(default=48, ge=4, le=168),
    dias: int = Query(default=120, ge=10, le=366),
    service: DebugService = Depends(get_debug_service),
):
    try:
        return service.forecast(usina_id, horizonte=horizonte, dias=dias)
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.get("/usinas/{usina_id}/noticias", response_model=DebugNoticiasOut)
def noticias_debug(
    usina_id: str,
    termos_extra: str = Query(default=""),
    max_itens: int = Query(default=12, ge=1, le=30),
    service: DebugService = Depends(get_debug_service),
):
    try:
        return service.noticias(usina_id, termos_extra=termos_extra, max_itens=max_itens)
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.get("/usinas/{usina_id}/lab-template", response_model=DebugLabOut)
def lab_template_debug(
    usina_id: str,
    dias: int = Query(default=30, ge=1, le=366),
    limit_serie: int = Query(default=200, ge=10, le=1000),
    service: DebugService = Depends(get_debug_service),
):
    try:
        return service.lab_template(usina_id, dias=dias, limit_serie=limit_serie)
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")

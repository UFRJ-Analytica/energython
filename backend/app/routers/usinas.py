from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.deps import get_financeiro_service, get_regulatorio_service, get_repo
from app.repositories.base import BaseRepository
from app.schemas.usinas import UsinaListOut, UsinaOut, UsinaResumoOut
from app.utils.datetime_utils import DateRangeError, parse_iso_datetime, parse_range
from app.utils.http_errors import api_error

router = APIRouter(prefix="/api", tags=["usinas"])


@router.get("/usinas", response_model=UsinaListOut)
def listar_usinas(
    fonte: str | None = None,
    submercado: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    repo: BaseRepository = Depends(get_repo),
):
    data = repo.list_usinas(fonte=fonte, submercado=submercado)
    return {
        "total_count": len(data),
        "limit": limit,
        "offset": offset,
        "metadata": {
            "mvp_scope_applied": True,
            "mvp_scope": "geradoras_renovaveis_submercado_ne",
            "api_contract_version": "v1",
            "data_quality_status": None,
        },
        "items": data[offset : offset + limit],
    }


@router.get("/usinas/{usina_id}", response_model=UsinaOut)
def detalhar_usina(usina_id: str, repo: BaseRepository = Depends(get_repo)):
    usina = repo.get_usina(usina_id)
    if not usina:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")
    return usina


@router.get("/usinas/{usina_id}/resumo", response_model=UsinaResumoOut)
def resumo_usina(
    usina_id: str,
    inicio: str | None = Query(default=None),
    fim: str | None = Query(default=None),
    repo: BaseRepository = Depends(get_repo),
    financeiro=Depends(get_financeiro_service),
    regulatorio=Depends(get_regulatorio_service),
):
    usina = repo.get_usina(usina_id)
    if not usina:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")

    if inicio is None or fim is None:
        fim_dt = datetime.utcnow()
        inicio_dt = fim_dt - timedelta(days=30)
    else:
        try:
            inicio_dt, fim_dt = parse_range(inicio, fim)
        except DateRangeError as exc:
            raise api_error(422, "parametro_data_invalido", str(exc))

    perda = financeiro.calcular_perda(usina_id, inicio_dt, fim_dt)
    eleg = regulatorio.classificar_eventos(usina_id, inicio_dt, fim_dt, usar_ia_classificacao=False)

    total_perda = perda["total_perda_reais"]
    total_eventos = len(perda["serie"])
    ticket_medio = (total_perda / total_eventos) if total_eventos else 0.0
    perc_ress = (eleg["total_potencial_ressarcivel_reais"] / total_perda * 100.0) if total_perda > 0 else 0.0

    dias_janela = max((fim_dt - inicio_dt).total_seconds() / 86400.0, 1.0)
    perda_media_diaria = total_perda / dias_janela if total_perda > 0 else 0.0
    perda_esperada_30d = {
        "valor_reais": round(perda_media_diaria * 30.0, 2),
        "horizonte_dias": 30,
        "metodo": "media_diaria_historica",
        "observacao": "Estimativa baseada na média diária observada no período selecionado.",
    }

    return {
        "usina": usina,
        "total_corte_mwh": perda["total_energia_restringida_mwh"],
        "total_perda_reais": total_perda,
        "percentual_ressarcivel": round(perc_ress, 2),
        "total_eventos_corte": total_eventos,
        "ticket_medio_evento_reais": round(ticket_medio, 2),
        "metadata": {
            "mvp_scope_applied": True,
            "mvp_scope": "geradoras_renovaveis_submercado_ne",
            "api_contract_version": "v1",
            "data_quality_status": perda["qualidade_dados"]["status"],
        },
        "perda_esperada_30d": perda_esperada_30d,
    }

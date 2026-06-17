from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.config import get_settings
from app.deps import get_curtailment_service, get_financeiro_service, get_repo
from app.domain.policies import RegulatorioPolicy
from app.repositories.base import BaseRepository
from app.schemas.curtailment import RiscoDetalhadoOut, RiscoOut
from app.schemas.usinas import UsinaListOut, UsinaOut, UsinaResumoOut
from app.utils.simple_cache import TTLCache
from app.utils.datetime_utils import DateRangeError, parse_range
from app.utils.http_errors import api_error


router = APIRouter(prefix="/api", tags=["usinas"])
_cache_settings = get_settings()
usinas_list_cache = TTLCache(
    name="usinas_list",
    ttl_seconds=_cache_settings.cache_usinas_ttl_seconds,
    max_entries=_cache_settings.cache_max_entries,
    enabled=_cache_settings.cache_enabled,
)
usina_detail_cache = TTLCache(
    name="usina_detail",
    ttl_seconds=_cache_settings.cache_usinas_ttl_seconds,
    max_entries=_cache_settings.cache_max_entries,
    enabled=_cache_settings.cache_enabled,
)


@router.get("/usinas", response_model=UsinaListOut)
def listar_usinas(
    fonte: str | None = None,
    submercado: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    repo: BaseRepository = Depends(get_repo),
):
    cache_key = f"usinas:list:{fonte or ''}:{submercado or ''}:{limit}:{offset}"
    cached = usinas_list_cache.get(cache_key)
    if cached is not None:
        return cached

    data = repo.list_usinas(fonte=fonte, submercado=submercado)
    out = {
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
    usinas_list_cache.set(cache_key, out)
    return out


@router.get("/usinas/{usina_id}", response_model=UsinaOut)
def detalhar_usina(usina_id: str, repo: BaseRepository = Depends(get_repo)):
    cache_key = f"usinas:detail:{usina_id}"
    cached = usina_detail_cache.get(cache_key)
    if cached is not None:
        return cached

    usina = repo.get_usina(usina_id)
    if not usina:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")
    usina_detail_cache.set(cache_key, usina)
    return usina


@router.get("/usinas/{usina_id}/resumo", response_model=UsinaResumoOut)
def resumo_usina(
    usina_id: str,
    inicio: str | None = Query(default=None),
    fim: str | None = Query(default=None),
    repo: BaseRepository = Depends(get_repo),
    financeiro=Depends(get_financeiro_service),
):
    usina = detalhar_usina(usina_id, repo)

    if inicio is None or fim is None:
        fim_dt = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        inicio_dt = fim_dt - timedelta(days=90)
    else:
        try:
            inicio_dt, fim_dt = parse_range(inicio, fim, max_dias=366)
        except DateRangeError as exc:
            raise api_error(422, "parametro_data_invalido", str(exc))

    # Keep the executive summary numerically aligned with the Financeiro tab.
    # The previous aggregate shortcut can diverge from the detailed endpoint when
    # source tables normalize timestamps/reasons differently. Cache keeps this
    # acceptable for the MVP.
    perda = financeiro.calcular_perda(usina_id, inicio_dt, fim_dt)
    policy = RegulatorioPolicy.default()

    total_perda = perda["total_perda_reais"]
    total_eventos = int(
        perda.get("total_eventos")
        or perda.get("qualidade_dados", {}).get("total_eventos_curtailment")
        or perda.get("qualidade_dados", {}).get("total_eventos")
        or len(perda.get("eventos") or [])
        or 0
    )
    total_intervalos = int(
        perda.get("qualidade_dados", {}).get("total_intervalos_restricao")
        or len(perda.get("serie") or [])
        or 0
    )
    ticket_medio = (total_perda / total_eventos) if total_eventos else 0.0
    perda_ressarcivel = sum(
        float(v or 0.0)
        for razao, v in (perda.get("por_razao") or {}).items()
        if policy.is_elegivel(str(razao))
    )
    perc_ress = (perda_ressarcivel / total_perda * 100.0) if total_perda > 0 else 0.0

    exposicao_prevista_30d = financeiro.projetar_exposicao(usina_id, horizonte_horas=24 * 30)
    perda_esperada_30d = {
        "valor_reais": round(exposicao_prevista_30d["exposicao_estimada_reais"], 2),
        "horizonte_dias": 30,
        "metodo": exposicao_prevista_30d.get("premissas", {}).get("previsao_futura", {}).get("metodo", "fallback_sazonal"),
        "observacao": (
            "Previsão futura baseada em modelo ML quando disponível; "
            "fallback sazonal por hora/weekday quando necessário."
        ),
    }

    return {
        "usina": usina,
        "total_corte_mwh": perda["total_energia_restringida_mwh"],
        "total_perda_reais": total_perda,
        "percentual_ressarcivel": round(perc_ress, 2),
        "perda_ressarcivel_reais": round(perda_ressarcivel, 2),
        "perda_por_razao": {str(k): round(float(v or 0.0), 2) for k, v in (perda.get("por_razao") or {}).items()},
        "total_eventos_corte": total_eventos,
        "total_intervalos_restricao": total_intervalos,
        "ticket_medio_evento_reais": round(ticket_medio, 2),
        "metadata": {
            "mvp_scope_applied": True,
            "mvp_scope": "geradoras_renovaveis_submercado_ne",
            "api_contract_version": "v1",
            "data_quality_status": perda["qualidade_dados"]["status"],
        },
        "perda_esperada_30d": perda_esperada_30d,
    }


@router.get("/usinas/{usina_id}/risco-corte", response_model=RiscoOut)
def risco_corte(
    usina_id: str,
    horizonte: int = Query(default=48, ge=1, le=720),
    service=Depends(get_curtailment_service),
):
    return service.prever_risco(usina_id, horizonte_horas=horizonte)


@router.get("/usinas/{usina_id}/curtailment/previsao-detalhada", response_model=RiscoDetalhadoOut)
def previsao_detalhada_curtailment(
    usina_id: str,
    horizonte: int = Query(default=48, ge=1, le=720),
    service=Depends(get_curtailment_service),
):
    return service.prever_risco_detalhado(usina_id, horizonte_horas=horizonte)

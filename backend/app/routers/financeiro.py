from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query

from app.deps import get_bess_service, get_financeiro_service
from app.schemas.bess import BessSimularIn, BessSimularOut
from app.schemas.financeiro import ExposicaoOut, PerdaOut, PrevisaoPerdasOut
from app.utils.datetime_utils import DateRangeError, parse_range
from app.utils.http_errors import api_error

router = APIRouter(prefix="/api", tags=["financeiro"])


@router.get("/usinas/{usina_id}/perda", response_model=PerdaOut)
def perda_financeira(
    usina_id: str,
    inicio: str,
    fim: str,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    service=Depends(get_financeiro_service),
):
    try:
        i, f = parse_range(inicio, fim, max_dias=90)
        out = service.calcular_perda(usina_id, i, f)
        total = len(out["serie"])
        out["paginacao_serie"] = {"total_count": total, "limit": limit, "offset": offset}
        out["serie"] = out["serie"][offset : offset + limit]
        return out
    except DateRangeError as exc:
        raise api_error(422, "parametro_data_invalido", str(exc))
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.get("/usinas/{usina_id}/exposicao", response_model=ExposicaoOut)
def exposicao(
    usina_id: str,
    horizonte: int = Query(default=48, ge=1, le=168),
    service=Depends(get_financeiro_service),
):
    try:
        return service.projetar_exposicao(usina_id, horizonte_horas=horizonte)
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.get("/usinas/{usina_id}/previsao-perdas", response_model=PrevisaoPerdasOut)
def previsao_perdas(
    usina_id: str,
    horizonte: int = Query(default=48, ge=1, le=720),
    historico_horas: int = Query(default=168, ge=24, le=2160),
    service=Depends(get_financeiro_service),
):
    try:
        return service.previsao_perdas_detalhada(
            usina_id=usina_id,
            horizonte_horas=horizonte,
            historico_horas=historico_horas,
        )
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.post("/usinas/{usina_id}/bess/simular", response_model=BessSimularOut)
def simular_bess(
    usina_id: str,
    body: BessSimularIn,
    inicio: str | None = None,
    fim: str | None = None,
    service=Depends(get_bess_service),
):
    if inicio is None or fim is None:
        fim_dt = datetime.utcnow()
        inicio_dt = fim_dt - timedelta(days=30)
    else:
        try:
            inicio_dt, fim_dt = parse_range(inicio, fim, max_dias=90)
        except DateRangeError as exc:
            raise api_error(422, "parametro_data_invalido", str(exc))

    try:
        return service.simular_bess(
            usina_id=usina_id,
            inicio=inicio_dt,
            fim=fim_dt,
            potencia_bateria_mw=body.potencia_mw,
            duracao_horas=body.duracao_horas,
            eficiencia=body.eficiencia,
            capex=body.capex,
        )
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")

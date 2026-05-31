from fastapi import APIRouter, Depends, Query

from app.deps import get_regulatorio_service
from app.schemas.regulatorio import (
    ConsultaRegulatoriaIn,
    ConsultaRegulatoriaOut,
    DossieExportIn,
    DossieExportOut,
    DossieIn,
    DossieOut,
    ElegibilidadeOut,
    FluxoRessarcimentoIn,
    FluxoRessarcimentoOut,
)
from app.utils.datetime_utils import DateRangeError, parse_range
from app.utils.http_errors import api_error

router = APIRouter(prefix="/api", tags=["regulatorio"])


@router.get("/usinas/{usina_id}/elegibilidade", response_model=ElegibilidadeOut)
def elegibilidade(
    usina_id: str,
    inicio: str,
    fim: str,
    limit: int = Query(default=200, ge=1, le=2000),
    offset: int = Query(default=0, ge=0),
    service=Depends(get_regulatorio_service),
):
    try:
        i, f = parse_range(inicio, fim)
        out = service.classificar_eventos(usina_id, i, f, usar_ia_classificacao=False)
        total = len(out["eventos"])
        out["paginacao_eventos"] = {"total_count": total, "limit": limit, "offset": offset}
        out["eventos"] = out["eventos"][offset : offset + limit]
        return out
    except DateRangeError as exc:
        raise api_error(422, "parametro_data_invalido", str(exc))
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.post("/usinas/{usina_id}/dossie", response_model=DossieOut)
def dossie(usina_id: str, body: DossieIn, service=Depends(get_regulatorio_service)):
    try:
        i, f = parse_range(body.inicio, body.fim)
        return service.gerar_dossie(usina_id, i, f)
    except DateRangeError as exc:
        raise api_error(422, "parametro_data_invalido", str(exc))
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.post("/usinas/{usina_id}/dossie/export", response_model=DossieExportOut)
def exportar_dossie(usina_id: str, body: DossieExportIn, service=Depends(get_regulatorio_service)):
    try:
        i, f = parse_range(body.inicio, body.fim)
        return service.exportar_dossie(
            usina_id=usina_id,
            inicio=i,
            fim=f,
            formato=body.formato,
            franquia_horas_override=body.franquia_horas_override,
        )
    except DateRangeError as exc:
        raise api_error(422, "parametro_data_invalido", str(exc))
    except ValueError as exc:
        if str(exc) == "formato_exportacao_invalido":
            raise api_error(422, "formato_exportacao_invalido", "Formato deve ser 'markdown' ou 'json'")
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.post("/usinas/{usina_id}/ressarcimento", response_model=FluxoRessarcimentoOut)
def fluxo_ressarcimento(usina_id: str, body: FluxoRessarcimentoIn, service=Depends(get_regulatorio_service)):
    try:
        i, f = parse_range(body.inicio, body.fim)
        return service.executar_fluxo_ressarcimento(
            usina_id=usina_id,
            inicio=i,
            fim=f,
            franquia_horas_override=body.franquia_horas_override,
        )
    except DateRangeError as exc:
        raise api_error(422, "parametro_data_invalido", str(exc))
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.post("/regulatorio/consulta", response_model=ConsultaRegulatoriaOut)
def consulta(body: ConsultaRegulatoriaIn, service=Depends(get_regulatorio_service)):
    return service.consultar_regra(body.pergunta)

from fastapi import APIRouter, Depends

from app.deps import get_regulatorio_service
from app.schemas.regulatorio import (
    ConsultaRegulatoriaIn,
    ConsultaRegulatoriaOut,
    DossieIn,
    DossieOut,
    ElegibilidadeOut,
)
from app.utils.datetime_utils import DateRangeError, parse_range
from app.utils.http_errors import api_error

router = APIRouter(prefix="/api", tags=["regulatorio"])


@router.get("/usinas/{usina_id}/elegibilidade", response_model=ElegibilidadeOut)
def elegibilidade(usina_id: str, inicio: str, fim: str, service=Depends(get_regulatorio_service)):
    try:
        i, f = parse_range(inicio, fim)
        return service.classificar_eventos(usina_id, i, f)
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


@router.post("/regulatorio/consulta", response_model=ConsultaRegulatoriaOut)
def consulta(body: ConsultaRegulatoriaIn, service=Depends(get_regulatorio_service)):
    return service.consultar_regra(body.pergunta)

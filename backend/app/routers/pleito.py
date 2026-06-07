from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.deps import get_pleito_service
from app.schemas.pleito import (
    EventosPleitoOut,
    FranquiaStatusOut,
    PleitoCreateIn,
    PleitoExportOut,
    PleitoOut,
    PleitoUpdateIn,
)
from app.utils.datetime_utils import DateRangeError, parse_range
from app.utils.http_errors import api_error

router = APIRouter(prefix="/api", tags=["pleito"])


@router.get("/usinas/{usina_id}/eventos-pleito", response_model=EventosPleitoOut)
def listar_eventos_pleito(
    usina_id: str,
    inicio: str,
    fim: str,
    apenas_elegivel: bool = False,
    motivo: str | None = None,
    service=Depends(get_pleito_service),
):
    try:
        i, f = parse_range(inicio, fim)
        out = service.listar_eventos_para_pleito(usina_id, i, f)
        eventos = out["eventos"]
        if apenas_elegivel:
            eventos = [e for e in eventos if e.get("elegivel")]
        if motivo:
            eventos = [e for e in eventos if str(e.get("razao_classificada_ons", "")).upper() == motivo.upper()]
        out = {**out, "eventos": eventos, "total_eventos": len(eventos), "eventos_elegiveis": sum(1 for e in eventos if e.get("elegivel"))}
        out["valor_total_pleitavel_reais"] = round(sum(float(e.get("valor_pleitavel_reais") or 0) for e in eventos), 2)
        out["energia_ressarcivel_total_mwh"] = round(sum(float(e.get("energia_ressarcivel_mwh") or 0) for e in eventos), 4)
        return out
    except DateRangeError as exc:
        raise api_error(422, "parametro_data_invalido", str(exc))
    except ValueError as exc:
        if str(exc) == "usina_nao_encontrada":
            raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")
        raise api_error(422, "pleito_eventos_invalido", str(exc))


@router.get("/usinas/{usina_id}/franquia-status", response_model=FranquiaStatusOut)
def franquia_status(usina_id: str, ano: int = Query(..., ge=2020, le=2100), service=Depends(get_pleito_service)):
    try:
        return service.franquia_status(usina_id, ano)
    except ValueError:
        raise api_error(404, "usina_nao_encontrada", "Usina não encontrada")


@router.post("/usinas/{usina_id}/pleitos", response_model=PleitoOut)
def criar_pleito(usina_id: str, body: PleitoCreateIn, service=Depends(get_pleito_service)):
    try:
        inicio = fim = None
        if body.inicio and body.fim:
            inicio, fim = parse_range(body.inicio, body.fim)
        return service.gerar_pleito(usina_id, body.eventos_ids, body.canal, inicio=inicio, fim=fim)
    except DateRangeError as exc:
        raise api_error(422, "parametro_data_invalido", str(exc))
    except ValueError as exc:
        code = str(exc)
        if code in {"usina_nao_encontrada", "pleito_nao_encontrado"}:
            raise api_error(404, code, "Registro não encontrado")
        raise api_error(422, code or "pleito_invalido", "Não foi possível gerar o pleito")


@router.get("/pleitos/{pleito_id}", response_model=PleitoOut)
def obter_pleito(pleito_id: str, service=Depends(get_pleito_service)):
    try:
        return service.obter_pleito(pleito_id)
    except ValueError:
        raise api_error(404, "pleito_nao_encontrado", "Pleito não encontrado")


@router.patch("/pleitos/{pleito_id}", response_model=PleitoOut)
def atualizar_pleito(pleito_id: str, body: PleitoUpdateIn, service=Depends(get_pleito_service)):
    try:
        return service.atualizar_pleito(pleito_id, markdown_gerado=body.markdown_gerado, status=body.status)
    except ValueError:
        raise api_error(404, "pleito_nao_encontrado", "Pleito não encontrado")


@router.get("/pleitos/{pleito_id}/export", response_model=PleitoExportOut)
def exportar_pleito(pleito_id: str, formato: str = "docx", service=Depends(get_pleito_service)):
    try:
        return service.exportar_pleito(pleito_id, formato=formato)
    except ValueError as exc:
        if str(exc) == "formato_exportacao_invalido":
            raise api_error(422, "formato_exportacao_invalido", "Formato deve ser docx, pdf, md/markdown ou json")
        raise api_error(404, "pleito_nao_encontrado", "Pleito não encontrado")

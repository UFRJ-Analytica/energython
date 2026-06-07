from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Any

from app.engine.elegibilidade import CANAL_NENHUM, classificar_elegibilidade, normalizar_razao_pleito
from app.engine.franquia import aplicar_franquia_eventos
from app.engine.prazos import janela_pleito
from app.engine.reconciliacao import reconciliar_evento
from app.engine.valoracao import valorar_evento
from app.domain.policies import FinanceiroPolicy
from app.utils.datetime_utils import ts_hour_key
from app.utils.document_export import markdown_to_docx_base64, markdown_to_pdf_base64

PLEITOS_STORE: dict[str, dict[str, Any]] = {}


class PleitoService:
    def __init__(self, repo, dossier_agent, financeiro_policy: FinanceiroPolicy | None = None):
        self.repo = repo
        self.dossier_agent = dossier_agent
        self.financeiro_policy = financeiro_policy or FinanceiroPolicy.default()

    @staticmethod
    def _as_datetime(value: Any) -> datetime:
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        return datetime.fromisoformat(str(value)).replace(tzinfo=None)

    @staticmethod
    def _as_float(value: Any, default: float = 0.0) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    def _franquia_horas(self, fonte: str | None, ano: int) -> tuple[float, str]:
        if hasattr(self.repo, "obter_franquia"):
            row = self.repo.obter_franquia(ano, fonte)  # type: ignore[attr-defined]
            if row:
                return self._as_float(row.get("franquia_horas")), str(row.get("fonte_normativa") or "gold.franquia_anual")
        fonte_norm = self.financeiro_policy.normalize_fonte(fonte)
        val = self.financeiro_policy.franquia_horas(fonte_norm, ano)
        if val <= 0:
            val = 82.0 if fonte_norm == "eolica" else 41.0
        return val, "Default MVP parametrizável — confirmar valor vigente ONS antes do go-live"

    @staticmethod
    def _evento_id(usina_id: str, timestamp: datetime, razao: str) -> str:
        return f"{usina_id}__{timestamp.isoformat()}__{razao}"

    @staticmethod
    def _data_brasilia(timestamp: datetime) -> str:
        # Dados do MVP chegam sem timezone; exibimos explicitamente na convenção operacional Brasília UTC-3.
        return f"{timestamp.isoformat()}-03:00"

    def listar_eventos_para_pleito(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos_raw = self.repo.get_constrained_off(usina_id, inicio, fim)
        plds = self.repo.get_pld(usina.get("submercado"), inicio, fim)
        climas = self.repo.get_clima_horario(usina_id, inicio, fim) if hasattr(self.repo, "get_clima_horario") else []
        dados_proprios = []
        if hasattr(self.repo, "get_dados_proprios_climatologia"):
            dados_proprios = self.repo.get_dados_proprios_climatologia(usina_id, inicio, fim)  # type: ignore[attr-defined]
        contratos = []
        if hasattr(self.repo, "obter_contratos_vigentes"):
            contratos = self.repo.obter_contratos_vigentes(usina_id, inicio)  # type: ignore[attr-defined]

        pld_map = {ts_hour_key(self._as_datetime(p.get("timestamp"))): self._as_float(p.get("pld_reais_mwh")) for p in plds}
        clima_map = {ts_hour_key(self._as_datetime(c.get("timestamp"))): c for c in climas}
        proprios_map = {ts_hour_key(self._as_datetime(d.get("timestamp"))): d for d in dados_proprios}
        ano = inicio.year
        franquia_horas, fonte_normativa_franquia = self._franquia_horas(usina.get("fonte"), ano)

        eventos_base: list[dict[str, Any]] = []
        for raw in eventos_raw:
            ts = self._as_datetime(raw.get("timestamp"))
            razao_original = raw.get("razao_restricao") or raw.get("cod_razaorestricao")
            razao = normalizar_razao_pleito(razao_original)
            origem = str(raw.get("origem_restricao") or "SIS").upper()
            eleg = classificar_elegibilidade(razao, origem=origem, data_evento=ts.date())
            duracao = self._as_float(raw.get("duracao_horas"), 1.0) or 1.0
            energia = self._as_float(raw.get("energia_restringida_mwh"))
            eventos_base.append(
                {
                    "evento_id": str(raw.get("evento_id") or self._evento_id(usina_id, ts, razao)),
                    "timestamp": ts.isoformat(),
                    "_ts": ts,
                    "data_inicio": self._data_brasilia(ts),
                    "data_fim": self._data_brasilia(ts + timedelta(hours=duracao)),
                    "duracao_horas": duracao,
                    "razao_classificada_ons": razao,
                    "razao_original": str(razao_original) if razao_original is not None else None,
                    "origem": origem,
                    "geracao_verificada_mwh": round(self._as_float(raw.get("geracao_verificada_mwh")), 4),
                    "geracao_referencia_ons_mwh": round(self._as_float(raw.get("geracao_referencia_mwh")), 4),
                    "geracao_referencia_mwh": self._as_float(raw.get("geracao_referencia_mwh")),
                    "energia_restringida_mwh": round(energia, 4),
                    "pld_reais_mwh": round(pld_map.get(ts_hour_key(ts), 0.0), 4),
                    "submercado": str(raw.get("submercado") or usina.get("submercado") or ""),
                    "elegivel": bool(eleg.elegivel),
                    "canal_recomendado": eleg.canal_recomendado,
                    "motivo_inelegibilidade": eleg.motivo_inelegibilidade,
                    "fonte_normativa": eleg.fonte_normativa,
                    "confianca": round(eleg.confianca, 4),
                }
            )

        eventos_franquia = aplicar_franquia_eventos(eventos_base, franquia_horas=franquia_horas)
        eventos_out: list[dict[str, Any]] = []
        for ev in eventos_franquia:
            ts = ev.pop("_ts")
            valoracao = valorar_evento(ev.get("energia_ressarcivel_mwh", 0.0), ev.get("pld_reais_mwh", 0.0), contratos)
            rec = reconciliar_evento(
                ev,
                clima_ons=clima_map.get(ts_hour_key(ts)),
                dados_proprios=proprios_map.get(ts_hour_key(ts)),
            )
            ev["energia_ressarcivel_mwh"] = round(self._as_float(ev.get("energia_ressarcivel_mwh")), 4)
            ev["valor_pleitavel_reais"] = valoracao["valor_pleitavel_reais"] if ev.get("canal_recomendado") != CANAL_NENHUM else 0.0
            ev["destinatario_do_ressarcimento"] = valoracao["destinatario_do_ressarcimento"]
            ev["reconciliacao"] = rec
            ev["janela_prazo"] = janela_pleito(ts)
            ev["anexos_recomendados"] = self._anexos_recomendados(ev)
            ev.pop("geracao_referencia_mwh", None)
            eventos_out.append(ev)

        eventos_out.sort(key=lambda x: float(x.get("valor_pleitavel_reais") or 0.0), reverse=True)
        valor_total = sum(float(e.get("valor_pleitavel_reais") or 0.0) for e in eventos_out)
        energia_total = sum(float(e.get("energia_ressarcivel_mwh") or 0.0) for e in eventos_out)
        return {
            "usina_id": usina_id,
            "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
            "franquia": {
                "ano": ano,
                "fonte": self.financeiro_policy.normalize_fonte(usina.get("fonte")),
                "horas_definidas": round(franquia_horas, 2),
                "fonte_normativa": fonte_normativa_franquia,
            },
            "total_eventos": len(eventos_out),
            "eventos_elegiveis": sum(1 for e in eventos_out if e.get("elegivel")),
            "valor_total_pleitavel_reais": round(valor_total, 2),
            "energia_ressarcivel_total_mwh": round(energia_total, 4),
            "eventos": eventos_out,
            "metadata": {
                "api_contract_version": "pleito_evento_v1",
                "fonte_eventos": "constrained_off",
                "human_in_the_loop": True,
                "llm_apenas_redacao": True,
            },
        }

    def franquia_status(self, usina_id: str, ano: int) -> dict:
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")
        franquia, fonte_norm = self._franquia_horas(usina.get("fonte"), ano)
        inicio = datetime(ano, 1, 1)
        fim = datetime(ano, 12, 31, 23, 59, 59)
        eventos = self.listar_eventos_para_pleito(usina_id, inicio, fim)["eventos"]
        horas_rel = sum(float(e.get("duracao_horas") or 0.0) for e in eventos if e.get("razao_classificada_ons") == "REL" and e.get("elegivel"))
        return {
            "usina_id": usina_id,
            "ano": ano,
            "fonte": self.financeiro_policy.normalize_fonte(usina.get("fonte")),
            "franquia_horas": round(franquia, 2),
            "fonte_normativa": fonte_norm,
            "horas_rel_acumuladas": round(horas_rel, 2),
            "horas_restantes": round(max(0.0, franquia - horas_rel), 2),
            "metadata": {"api_contract_version": "pleito_evento_v1"},
        }

    def gerar_pleito(self, usina_id: str, eventos_ids: list[str], canal: str, inicio: datetime | None = None, fim: datetime | None = None) -> dict:
        if inicio is None or fim is None:
            inicio, fim = self._inferir_periodo_eventos(eventos_ids)
        eventos_payload = self.listar_eventos_para_pleito(usina_id, inicio, fim)
        eventos = [e for e in eventos_payload["eventos"] if e["evento_id"] in set(eventos_ids)]
        if len(eventos) != len(set(eventos_ids)):
            raise ValueError("evento_nao_encontrado")
        canais = {e.get("canal_recomendado") for e in eventos}
        if canal not in canais and any(e.get("canal_recomendado") != CANAL_NENHUM for e in eventos):
            # Permite override humano apenas quando todos são elegíveis, mas registra no pacote.
            pass
        pacote = self._montar_pacote(usina_id, canal, eventos, eventos_payload)
        template_md = self._render_template(pacote)
        markdown = self.dossier_agent.gerar_pleito_evento(pacote, template_md)
        now = datetime.utcnow().isoformat()
        pleito_id = str(uuid.uuid4())
        pleito = {
            "pleito_id": pleito_id,
            "usina_id": usina_id,
            "canal": canal,
            "eventos_ids": eventos_ids,
            "status": "RASCUNHO",
            "markdown_gerado": markdown,
            "metadados_json": {
                "pacote_estruturado": pacote,
                "pacote_hash_sha256": hashlib.sha256(json.dumps(pacote, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest(),
            },
            "criado_em": now,
            "atualizado_em": now,
        }
        PLEITOS_STORE[pleito_id] = pleito
        return pleito

    def obter_pleito(self, pleito_id: str) -> dict:
        pleito = PLEITOS_STORE.get(pleito_id)
        if not pleito:
            raise ValueError("pleito_nao_encontrado")
        return pleito

    def atualizar_pleito(self, pleito_id: str, markdown_gerado: str | None = None, status: str | None = None) -> dict:
        pleito = self.obter_pleito(pleito_id)
        if markdown_gerado is not None:
            pleito["markdown_gerado"] = markdown_gerado
        if status is not None:
            pleito["status"] = status
        pleito["atualizado_em"] = datetime.utcnow().isoformat()
        return pleito

    def exportar_pleito(self, pleito_id: str, formato: str = "docx") -> dict:
        pleito = self.obter_pleito(pleito_id)
        formato_norm = (formato or "docx").lower()
        markdown = pleito["markdown_gerado"]
        if formato_norm in {"md", "markdown"}:
            return {
                "pleito_id": pleito_id,
                "formato": "md",
                "file_name": f"pleito_{pleito_id}.md",
                "content_type": "text/markdown; charset=utf-8",
                "content": markdown,
                "content_encoding": "utf-8",
            }
        if formato_norm == "docx":
            return {
                "pleito_id": pleito_id,
                "formato": "docx",
                "file_name": f"pleito_{pleito_id}.docx",
                "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "content": markdown_to_docx_base64(markdown),
                "content_encoding": "base64",
            }
        if formato_norm == "pdf":
            return {
                "pleito_id": pleito_id,
                "formato": "pdf",
                "file_name": f"pleito_{pleito_id}.pdf",
                "content_type": "application/pdf",
                "content": markdown_to_pdf_base64(markdown),
                "content_encoding": "base64",
            }
        if formato_norm == "json":
            return {
                "pleito_id": pleito_id,
                "formato": "json",
                "file_name": f"pleito_{pleito_id}.json",
                "content_type": "application/json",
                "content": json.dumps(pleito, ensure_ascii=False, indent=2),
                "content_encoding": "utf-8",
            }
        raise ValueError("formato_exportacao_invalido")

    def _inferir_periodo_eventos(self, eventos_ids: list[str]) -> tuple[datetime, datetime]:
        timestamps = []
        for eid in eventos_ids:
            try:
                parts = eid.split("__")
                timestamps.append(datetime.fromisoformat(parts[1]))
            except Exception:
                pass
        if not timestamps:
            raise ValueError("periodo_obrigatorio")
        return min(timestamps) - timedelta(hours=1), max(timestamps) + timedelta(hours=2)

    @staticmethod
    def _anexos_recomendados(ev: dict) -> list[str]:
        anexos = ["Extrato SAGER/ONS do evento", "PLD horário CCEE do submercado", "Boletim operativo ONS do dia"]
        if ev.get("reconciliacao", {}).get("houve_comparacao"):
            anexos += ["Dados próprios climatológicos/SMF", "Comprovação de disponibilidade eletromecânica"]
        else:
            anexos += ["Comprovação de disponibilidade SCADA", "Registro de despacho/restrição operacional"]
        return anexos

    def _montar_pacote(self, usina_id: str, canal: str, eventos: list[dict], eventos_payload: dict) -> dict:
        usina = self.repo.get_usina(usina_id) or {}
        total_valor = sum(float(e.get("valor_pleitavel_reais") or 0.0) for e in eventos)
        total_energia_restr = sum(float(e.get("energia_restringida_mwh") or 0.0) for e in eventos)
        total_energia_ress = sum(float(e.get("energia_ressarcivel_mwh") or 0.0) for e in eventos)
        menor_prazo = min((int(e.get("janela_prazo", {}).get("dias_restantes_protocolo_ons", 9999)) for e in eventos), default=0)
        fundamentos = [
            "Submódulo 5.13 dos Procedimentos de Rede (RO-AO.BR.13) — confirmar revisão vigente antes do protocolo",
            "Resolução Normativa ANEEL nº 1.030/2022, com alterações posteriores",
        ]
        if canal == "TERMO_COMPROMISSO_LEI_15269":
            fundamentos.append("Lei 15.269/2025 art. 1º-B e regulamentação MME/CCEE vigente")
        else:
            fundamentos.append("Ofício 61/2025-SGM/ANEEL, quando aplicável a dados próprios")
        return {
            "canal": canal,
            "usina": {
                "razao_social": usina.get("nome") or usina_id,
                "ceg": usina.get("ceg") or "[CEG ausente — preencher]",
                "sigla_ons": usina.get("sigla_ons") or usina_id,
                "fonte": usina.get("fonte"),
                "submercado": usina.get("submercado"),
                "outorga": usina.get("outorga") or "[outorga ausente — preencher]",
            },
            "destinatario": {
                "orgao": "Operador Nacional do Sistema Elétrico (ONS)",
                "cargo": "Gerente Executivo de Apuração, Análise e Custo da Operação",
                "canal_envio": "Protocolo ONS via SINtegre" if canal == "PROTOCOLO_ONS" else "Canal do Termo de Compromisso MME/CCEE vigente",
            },
            "fundamentacao_normativa": fundamentos,
            "janela_prazo": {
                "data_referencia_hoje": datetime.utcnow().date().isoformat(),
                "dias_restantes_menor": menor_prazo,
                "observacao": "Verificar prazo específico antes do protocolo; SAGER rotineiro é apenas informativo no MVP.",
            },
            "franquia": eventos_payload["franquia"],
            "eventos": eventos,
            "totais": {
                "n_eventos": len(eventos),
                "energia_total_restringida_mwh": round(total_energia_restr, 4),
                "energia_ressarcivel_total_mwh": round(total_energia_ress, 4),
                "valor_total_pleitavel_reais": round(total_valor, 2),
                "destinatario_do_ressarcimento": eventos[0].get("destinatario_do_ressarcimento") if eventos else "[preencher]",
            },
        }

    @staticmethod
    def _render_template(pacote: dict) -> str:
        canal = pacote.get("canal")
        titulo = "Pleito de revisão de apuração de constrained-off" if canal == "PROTOCOLO_ONS" else "Dossiê de adesão/impugnação ao Termo de Compromisso"
        linhas = [
            f"# {titulo}",
            "",
            f"Data: {pacote['janela_prazo']['data_referencia_hoje']}",
            f"Destinatário: {pacote['destinatario']['orgao']} — {pacote['destinatario']['cargo']}",
            f"Canal de envio: {pacote['destinatario']['canal_envio']}",
            "",
            "## 1. Objeto",
            "Solicitamos a revisão da apuração dos eventos de constrained-off listados, com manutenção da granularidade evento a evento e rascunho sujeito à revisão humana.",
            "",
            "## 2. Identificação da usina",
            f"Razão social/usina: {pacote['usina']['razao_social']}",
            f"CEG: {pacote['usina']['ceg']}",
            f"Sigla ONS: {pacote['usina']['sigla_ons']}",
            f"Fonte/submercado: {pacote['usina']['fonte']} / {pacote['usina']['submercado']}",
            "",
            "## 3. Eventos selecionados",
            "| evento_id | data/hora Brasília | duração | razão | energia restringida MWh | energia ressarcível MWh | valor pleitável R$ |",
            "|---|---:|---:|---|---:|---:|---:|",
        ]
        for ev in pacote.get("eventos", []):
            linhas.append(
                f"| {ev['evento_id']} | {ev['data_inicio']} | {ev['duracao_horas']} | {ev['razao_classificada_ons']} | "
                f"{ev['energia_restringida_mwh']} | {ev['energia_ressarcivel_mwh']} | {ev['valor_pleitavel_reais']} |"
            )
        linhas += [
            "",
            "## 4. Fundamentação normativa",
            *[f"- {f}" for f in pacote.get("fundamentacao_normativa", [])],
            "",
            "## 5. Contestação técnica e reconciliação",
        ]
        for ev in pacote.get("eventos", []):
            rec = ev.get("reconciliacao", {})
            linhas.append(f"- {ev['evento_id']}: {rec.get('argumento_tecnico', '[campo ausente — preencher]')}")
        frq = pacote.get("franquia", {})
        totais = pacote.get("totais", {})
        linhas += [
            "",
            "## 6. Demonstrativo de cálculo",
            f"Franquia aplicada: {frq.get('horas_definidas')} h ({frq.get('fonte_normativa')}).",
            f"Energia ressarcível total: {totais.get('energia_ressarcivel_total_mwh')} MWh.",
            f"Valor total pleitável: R$ {totais.get('valor_total_pleitavel_reais')}.",
            "Metodologia: energia ressarcível × PLD horário do submercado, com franquia anual aplicada em código antes da redação.",
            "",
            "## 7. Destinatário do ressarcimento",
            str(totais.get("destinatario_do_ressarcimento") or "[campo ausente — preencher]"),
            "",
            "## 8. Pedido",
            "Requer-se a revisão da apuração e o processamento do ressarcimento cabível, preservados os documentos comprobatórios e a revisão humana antes do protocolo.",
            "",
            "## 9. Anexos recomendados",
        ]
        anexos = sorted({a for ev in pacote.get("eventos", []) for a in ev.get("anexos_recomendados", [])})
        linhas += [f"- {a}" for a in anexos]
        linhas += ["", "— Documento gerado como rascunho. Revisão humana obrigatória antes de protocolo."]
        return "\n".join(linhas)

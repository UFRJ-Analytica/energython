from __future__ import annotations

import json
from datetime import datetime

from app.domain.contracts import parse_constrained_off, parse_pld
from app.domain.policies import RegulatorioPolicy
from app.services.financeiro_service import FinanceiroService


def _ts_hour_key(value) -> str:
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    dt = dt.replace(tzinfo=None)
    return str(dt.replace(minute=0, second=0, microsecond=0))


class RegulatorioService:
    def __init__(
        self,
        repo,
        classifier_agent,
        dossier_agent,
        rag_agent,
        regras_elegibilidade=None,
        cache=None,
        policy: RegulatorioPolicy | None = None,
    ):
        self.repo = repo
        self.classifier_agent = classifier_agent
        self.dossier_agent = dossier_agent
        self.rag_agent = rag_agent
        if policy is not None:
            self.policy = policy
        elif regras_elegibilidade is not None:
            self.policy = RegulatorioPolicy(elegibilidade_por_razao=regras_elegibilidade)
        else:
            self.policy = RegulatorioPolicy.default()
        self.regras_elegibilidade = self.policy.elegibilidade_por_razao
        self.financeiro_service = FinanceiroService(repo)
        self.cache = cache

    def classificar_eventos(
        self,
        usina_id: str,
        inicio: datetime,
        fim: datetime,
        franquia_horas_override: float | None = None,
    ) -> dict:
        cache_key = (
            f"classificar:{usina_id}:{inicio.isoformat()}:{fim.isoformat()}:"
            f"{hash(frozenset(self.regras_elegibilidade.items()))}:frq={franquia_horas_override}"
        )
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos = parse_constrained_off(self.repo.get_constrained_off(usina_id, inicio, fim))
        pld = parse_pld(self.repo.get_pld(usina["submercado"], inicio, fim))
        pld_map = {str(p.timestamp): p.pld_reais_mwh for p in pld}
        pld_map_hora = {_ts_hour_key(p.timestamp): p.pld_reais_mwh for p in pld}

        itens = []
        total_potencial = 0.0
        classificados_por_ia = 0
        classificados_por_gold = 0
        pld_faltante_eventos = 0
        eventos_sem_razao_original = 0
        eventos_com_razao_normalizada = 0

        fonte_usina = usina.get("fonte")
        ano_base = inicio.year
        franquia_horas_ano = self.financeiro_service.policy.franquia_horas(fonte_usina, ano_base)
        if franquia_horas_override is not None:
            franquia_horas_ano = max(0.0, float(franquia_horas_override))
        horas_elegiveis_no_periodo = 0.0

        for e in eventos:
            razao_original = e.razao_restricao or e.cod_razaorestricao
            razao = self.policy.normalize_razao(razao_original)
            if not razao_original:
                eventos_sem_razao_original += 1
            elif razao_original != razao:
                eventos_com_razao_normalizada += 1
            confianca = 1.0
            justificativa = "classificacao_gold"
            fonte_classificacao = "gold"

            if not razao or razao not in self.regras_elegibilidade:
                pred = self.classifier_agent.classificar_evento(e)
                razao = pred.get("razao", "indefinido")
                confianca = float(pred.get("confianca", 0.0) or 0.0)
                justificativa = str(pred.get("justificativa", "classificacao_por_ia"))
                fonte_classificacao = "ia"
                classificados_por_ia += 1
            else:
                classificados_por_gold += 1

            elegivel = self.policy.is_elegivel(razao)
            energia = e.energia_restringida_mwh
            regra_aplicada = f"razao={razao};elegivel={str(elegivel).lower()}"
            preco = pld_map.get(str(e.timestamp))
            if preco is None:
                preco = pld_map_hora.get(_ts_hour_key(e.timestamp))
            if preco is None:
                pld_faltante_eventos += 1
                preco = 0.0
            valor = energia * preco if elegivel else 0.0
            total_potencial += valor
            if elegivel and energia > 0:
                horas_elegiveis_no_periodo += 1.0

            itens.append(
                {
                    "timestamp": str(e.timestamp),
                    "razao_restricao": razao,
                    "energia_restringida_mwh": round(energia, 4),
                    "elegivel_ressarcimento": elegivel,
                    "valor_potencial_reais": round(valor, 2),
                    "valor_ressarcivel_pos_franquia_reais": 0.0,
                    "dentro_franquia": bool(elegivel),
                    "classificacao_fonte": fonte_classificacao,
                    "classificacao_confianca": round(confianca, 4),
                    "classificacao_justificativa": justificativa,
                    "auditoria_regra": regra_aplicada,
                    "auditoria_motivo_status": (
                        "nao_elegivel_razao"
                        if not elegivel
                        else ("sem_pld" if preco == 0 else "pendente_aplicar_franquia")
                    ),
                    "auditoria_detalhe": (
                        "evento inelegível pelas regras vigentes"
                        if not elegivel
                        else (
                            "evento elegível sem PLD horário disponível (valorado em 0)"
                            if preco == 0
                            else "evento elegível aguardando aplicação de franquia"
                        )
                    ),
                }
            )

        qualidade_status = (
            "completo"
            if pld_faltante_eventos == 0 and eventos_sem_razao_original == 0
            else "parcial"
        )

        # Aplica franquia anual por fonte (MVP: contabiliza horas elegíveis no período)
        horas_excedentes_franquia_no_periodo = max(0.0, horas_elegiveis_no_periodo - franquia_horas_ano)
        horas_restantes_dentro_franquia = min(horas_elegiveis_no_periodo, franquia_horas_ano)

        total_ressarcivel_pos_franquia = 0.0
        for item in sorted(itens, key=lambda x: x["timestamp"]):
            if not item["elegivel_ressarcimento"] or item["energia_restringida_mwh"] <= 0:
                item["dentro_franquia"] = False
                item["valor_ressarcivel_pos_franquia_reais"] = 0.0
                if item["elegivel_ressarcimento"] and item["energia_restringida_mwh"] <= 0:
                    item["auditoria_motivo_status"] = "energia_zerada"
                    item["auditoria_detalhe"] = "evento elegível com energia restringida <= 0"
                continue

            if horas_restantes_dentro_franquia > 0:
                item["dentro_franquia"] = True
                item["valor_ressarcivel_pos_franquia_reais"] = 0.0
                item["auditoria_motivo_status"] = "dentro_franquia"
                item["auditoria_detalhe"] = "evento elegível absorvido pela franquia anual"
                horas_restantes_dentro_franquia -= 1.0
            else:
                item["dentro_franquia"] = False
                val = float(item["valor_potencial_reais"])
                item["valor_ressarcivel_pos_franquia_reais"] = round(val, 2)
                item["auditoria_motivo_status"] = "ressarcivel_excedente_franquia"
                item["auditoria_detalhe"] = "evento elegível excedeu franquia anual e foi valorado"
                total_ressarcivel_pos_franquia += val

        out = {
            "usina_id": usina_id,
            "total_potencial_ressarcivel_reais": round(total_potencial, 2),
            "total_ressarcivel_pos_franquia_reais": round(total_ressarcivel_pos_franquia, 2),
            "franquia_horas_ano": round(franquia_horas_ano, 2),
            "horas_elegiveis_no_periodo": round(horas_elegiveis_no_periodo, 2),
            "horas_excedentes_franquia_no_periodo": round(horas_excedentes_franquia_no_periodo, 2),
            "qualidade_classificacao": {
                "eventos_totais": len(eventos),
                "eventos_classificados_por_ia": classificados_por_ia,
                "eventos_com_razao_gold": classificados_por_gold,
            },
            "qualidade_dados": {
                "status": qualidade_status,
                "pld_faltante_eventos": pld_faltante_eventos,
                "eventos_sem_razao_original": eventos_sem_razao_original,
                "eventos_com_razao_normalizada": eventos_com_razao_normalizada,
                "total_eventos": len(eventos),
            },
            "metadata": {
                "mvp_scope_applied": True,
                "mvp_scope": "geradoras_renovaveis_submercado_ne",
                "api_contract_version": "v1",
                "data_quality_status": qualidade_status,
                "regulatorio_policy_version": self.policy.versao_regulatoria,
            },
            "eventos": itens,
        }
        if self.cache:
            self.cache.set(cache_key, out)
        return out

    def gerar_dossie(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
        cache_key = f"dossie:{usina_id}:{inicio.isoformat()}:{fim.isoformat()}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        eleg = self.classificar_eventos(usina_id, inicio, fim)
        dossie = self.dossier_agent.gerar_dossie(eleg)
        out = {"usina_id": usina_id, "dossie_markdown": dossie}
        if self.cache:
            self.cache.set(cache_key, out)
        return out

    def executar_fluxo_ressarcimento(
        self,
        usina_id: str,
        inicio: datetime,
        fim: datetime,
        franquia_horas_override: float | None = None,
    ) -> dict:
        eleg = self.classificar_eventos(
            usina_id=usina_id,
            inicio=inicio,
            fim=fim,
            franquia_horas_override=franquia_horas_override,
        )
        dossie_md = self.dossier_agent.gerar_dossie(eleg)
        eleg = {
            **eleg,
            "paginacao_eventos": {
                "total_count": len(eleg.get("eventos", [])),
                "limit": len(eleg.get("eventos", [])),
                "offset": 0,
            },
        }
        return {
            "usina_id": usina_id,
            "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
            "selecao": {
                "fonte_eventos": "constrained_off",
                "eventos_totais": len(eleg.get("eventos", [])),
            },
            "resultado_elegibilidade": eleg,
            "dossie_markdown": dossie_md,
            "human_in_the_loop": {
                "submissao_automatica_habilitada": False,
                "acao_recomendada": "revisar_e_exportar_dossie",
            },
            "metadata": {
                "api_contract_version": "v1",
                "fluxo": "agente_ressarcimento",
                "regulatorio_policy_version": self.policy.versao_regulatoria,
            },
        }

    def exportar_dossie(
        self,
        usina_id: str,
        inicio: datetime,
        fim: datetime,
        formato: str = "markdown",
        franquia_horas_override: float | None = None,
    ) -> dict:
        fluxo = self.executar_fluxo_ressarcimento(
            usina_id=usina_id,
            inicio=inicio,
            fim=fim,
            franquia_horas_override=franquia_horas_override,
        )
        formato_norm = (formato or "markdown").strip().lower()
        inicio_tag = inicio.strftime("%Y%m%dT%H%M%S")
        fim_tag = fim.strftime("%Y%m%dT%H%M%S")

        if formato_norm in {"md", "markdown"}:
            return {
                "usina_id": usina_id,
                "formato": "markdown",
                "file_name": f"dossie_{usina_id}_{inicio_tag}_{fim_tag}.md",
                "content_type": "text/markdown; charset=utf-8",
                "content": fluxo["dossie_markdown"],
            }

        if formato_norm == "json":
            payload = {
                "usina_id": fluxo["usina_id"],
                "periodo": fluxo["periodo"],
                "selecao": fluxo["selecao"],
                "resultado_elegibilidade": fluxo["resultado_elegibilidade"],
                "human_in_the_loop": fluxo["human_in_the_loop"],
                "metadata": fluxo["metadata"],
                "dossie_markdown": fluxo["dossie_markdown"],
            }
            return {
                "usina_id": usina_id,
                "formato": "json",
                "file_name": f"dossie_{usina_id}_{inicio_tag}_{fim_tag}.json",
                "content_type": "application/json",
                "content": json.dumps(payload, ensure_ascii=False, indent=2),
            }

        raise ValueError("formato_exportacao_invalido")

    def consultar_regra(self, pergunta: str) -> dict:
        return self.rag_agent.consultar(pergunta)

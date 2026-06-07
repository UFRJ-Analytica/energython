from __future__ import annotations

import json
from datetime import datetime, timedelta

from app.domain.contracts import parse_constrained_off, parse_pld
from app.domain.policies import RegulatorioPolicy
from app.services.financeiro_service import FinanceiroService
from app.utils.datetime_utils import ts_hour_key
from app.utils.logging_utils import log_json


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
        usar_ia_classificacao: bool = False,
    ) -> dict:
        cache_key = (
            f"classificar:{usina_id}:{inicio.isoformat()}:{fim.isoformat()}:"
            f"{hash(frozenset(self.regras_elegibilidade.items()))}:frq={franquia_horas_override}:ia={int(usar_ia_classificacao)}"
        )
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                log_json("regulatorio.classificar_eventos.cache_hit", usina_id=usina_id)
                return cached

        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos = parse_constrained_off(self.repo.get_constrained_off(usina_id, inicio, fim))
        pld = parse_pld(self.repo.get_pld(usina["submercado"], inicio, fim))
        pld_map = {str(p.timestamp): p.pld_reais_mwh for p in pld}
        pld_map_hora = {ts_hour_key(p.timestamp): p.pld_reais_mwh for p in pld}

        itens = []
        total_potencial = 0.0
        classificados_por_ia = 0
        classificados_por_gold = 0
        pld_faltante_eventos = 0
        eventos_sem_razao_original = 0
        eventos_com_razao_normalizada = 0
        classificacao_ia_por_razao: dict[str, dict] = {}
        max_classificacoes_ia = 12

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

            if (not razao or razao not in self.regras_elegibilidade) and usar_ia_classificacao:
                chave_razao = str(razao_original or "").strip().lower()
                if not chave_razao:
                    razao = "indefinido"
                    confianca = 0.0
                    justificativa = "sem_razao_original_para_classificar"
                    fonte_classificacao = "regra_default"
                elif chave_razao in classificacao_ia_por_razao:
                    pred = classificacao_ia_por_razao[chave_razao]
                    razao = pred.get("razao", "indefinido")
                    confianca = float(pred.get("confianca", 0.0) or 0.0)
                    justificativa = str(pred.get("justificativa", "classificacao_por_ia_cache_razao"))
                    fonte_classificacao = "ia"
                elif len(classificacao_ia_por_razao) < max_classificacoes_ia:
                    pred = self.classifier_agent.classificar_evento(e)
                    classificacao_ia_por_razao[chave_razao] = pred
                    razao = pred.get("razao", "indefinido")
                    confianca = float(pred.get("confianca", 0.0) or 0.0)
                    justificativa = str(pred.get("justificativa", "classificacao_por_ia"))
                    fonte_classificacao = "ia"
                    classificados_por_ia += 1
                else:
                    razao = "indefinido"
                    confianca = 0.0
                    justificativa = "limite_classificacao_ia_atingido"
                    fonte_classificacao = "regra_default"
            else:
                if not razao or razao not in self.regras_elegibilidade:
                    razao = "indefinido"
                    confianca = 0.0
                    justificativa = "classificacao_ia_desabilitada"
                    fonte_classificacao = "regra_default"
                classificados_por_gold += 1

            elegivel = self.policy.is_elegivel(razao)
            energia = e.energia_restringida_mwh
            regra_aplicada = f"razao={razao};elegivel={str(elegivel).lower()}"
            preco = pld_map.get(str(e.timestamp))
            if preco is None:
                preco = pld_map_hora.get(ts_hour_key(e.timestamp))
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
        log_json(
            "regulatorio.classificar_eventos",
            usina_id=usina_id,
            total_eventos=len(eventos),
            classificados_por_ia=classificados_por_ia,
            classificados_por_gold=classificados_por_gold,
            horas_elegiveis=round(horas_elegiveis_no_periodo, 2),
            total_potencial_reais=round(total_potencial, 2),
            total_ressarcivel_pos_franquia=round(total_ressarcivel_pos_franquia, 2),
            qualidade_status=qualidade_status,
        )

        if self.cache:
            self.cache.set(cache_key, out)
        return out

    def gerar_dossie(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
        cache_key = f"dossie:{usina_id}:{inicio.isoformat()}:{fim.isoformat()}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eleg = self.classificar_eventos(usina_id, inicio, fim, usar_ia_classificacao=True)
        perda_resumo = self.financeiro_service.calcular_perda_resumida(usina_id, inicio, fim)
        exposicao_30d = self.financeiro_service.projetar_exposicao(usina_id, horizonte_horas=24 * 30)

        payload_dossie = {
            "usina": {
                "usina_id": usina.get("usina_id"),
                "nome": usina.get("nome"),
                "fonte": usina.get("fonte"),
                "submercado": usina.get("submercado"),
            },
            "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
            "resumo_financeiro": {
                "total_perda_reais": perda_resumo.get("total_perda_reais"),
                "total_energia_restringida_mwh": perda_resumo.get("total_energia_restringida_mwh"),
                "por_razao": perda_resumo.get("por_razao"),
                "total_eventos": perda_resumo.get("total_eventos"),
                "perda_esperada_30d_reais": round(float(exposicao_30d.get("exposicao_estimada_reais") or 0.0), 2),
                "perda_esperada_30d_energia_mwh": round(float(exposicao_30d.get("energia_perdida_prevista_mwh") or 0.0), 4),
                "horizonte_dias": 30,
            },
            "elegibilidade": eleg,
            "instrucao_contextual": (
                "Para MVP/pitch rápido, usar os números fornecidos no payload como fonte primária. "
                "Não declarar 'informação indisponível' quando o campo numérico estiver presente."
            ),
        }

        dossie = self.dossier_agent.gerar_dossie(payload_dossie)
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
        cache_key = (
            f"fluxo_ressarcimento:{usina_id}:{inicio.isoformat()}:{fim.isoformat()}:"
            f"frq={franquia_horas_override}"
        )
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        perda = self.financeiro_service.calcular_perda(usina_id, inicio, fim)
        eleg = self.classificar_eventos(
            usina_id=usina_id,
            inicio=inicio,
            fim=fim,
            franquia_horas_override=franquia_horas_override,
            usar_ia_classificacao=True,
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

        reconciliacao = {
            "energia_total_mwh": round(float(perda.get("total_energia_restringida_mwh", 0.0) or 0.0), 4),
            "perda_total_reais": round(float(perda.get("total_perda_reais", 0.0) or 0.0), 2),
            "potencial_ressarcivel_reais": eleg.get("total_potencial_ressarcivel_reais", 0.0),
            "ressarcivel_pos_franquia_reais": eleg.get("total_ressarcivel_pos_franquia_reais", 0.0),
            "pld_faltante_eventos": int(eleg.get("qualidade_dados", {}).get("pld_faltante_eventos", 0) or 0),
            "eventos_sem_razao_original": int(eleg.get("qualidade_dados", {}).get("eventos_sem_razao_original", 0) or 0),
        }

        out = {
            "usina_id": usina_id,
            "periodo": {"inicio": inicio.isoformat(), "fim": fim.isoformat()},
            "selecao": {
                "fonte_eventos": "constrained_off",
                "eventos_totais": len(eleg.get("eventos", [])),
                "eventos_elegiveis": int(eleg.get("horas_elegiveis_no_periodo", 0) or 0),
            },
            "reconciliacao": reconciliacao,
            "etapas": [
                "ingestao_eventos_constrained_off",
                "reconciliacao_eventos_pld",
                "classificacao_razao_elegibilidade",
                "aplicacao_franquia_anual",
                "geracao_pleito_dossie",
            ],
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
        if self.cache:
            self.cache.set(cache_key, out)
        return out

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

    def consultar_regra(
        self,
        pergunta: str,
        usina_id: str | None = None,
        inicio: datetime | None = None,
        fim: datetime | None = None,
    ) -> dict:
        contexto_operacional = ""
        if usina_id:
            usina = self.repo.get_usina(usina_id)
            if usina:
                fim_ctx = fim or datetime.utcnow()
                inicio_ctx = inicio or (fim_ctx.replace(tzinfo=None) - timedelta(days=30))
                try:
                    perda = self.financeiro_service.calcular_perda(usina_id, inicio_ctx, fim_ctx)
                    perda_resumo = self.financeiro_service.calcular_perda_resumida(usina_id, inicio_ctx, fim_ctx)
                    exposicao_30d = self.financeiro_service.projetar_exposicao(usina_id, horizonte_horas=24 * 30)
                    eleg = self.classificar_eventos(usina_id, inicio_ctx, fim_ctx, usar_ia_classificacao=False)
                    contexto_operacional = (
                        f"Usina: {usina.get('usina_id')} - {usina.get('nome')} | fonte={usina.get('fonte')} | submercado={usina.get('submercado')}\n"
                        f"Período histórico analisado: {inicio_ctx.isoformat()} até {fim_ctx.isoformat()}\n"
                        f"Histórico: corte_total_mwh={perda.get('total_energia_restringida_mwh')} | perda_total_reais={perda.get('total_perda_reais')} | eventos={len(perda.get('serie', []))}\n"
                        f"Histórico resumido: total_perda_reais={perda_resumo.get('total_perda_reais')} | total_energia_mwh={perda_resumo.get('total_energia_restringida_mwh')} | por_razao={perda_resumo.get('por_razao')}\n"
                        f"Previsão 30d: perda_esperada_reais={round(float(exposicao_30d.get('exposicao_estimada_reais') or 0.0), 2)} | energia_prevista_mwh={round(float(exposicao_30d.get('energia_perdida_prevista_mwh') or 0.0), 4)}\n"
                        f"Regulatório: potencial_ressarcivel_reais={eleg.get('total_potencial_ressarcivel_reais')} | pos_franquia_reais={eleg.get('total_ressarcivel_pos_franquia_reais')}\n"
                        "Observação: use os números acima e diferencie histórico vs previsão no texto final; não alegar ausência de dados quando os campos estiverem presentes."
                    )
                except Exception:
                    contexto_operacional = (
                        f"Usina: {usina.get('usina_id')} - {usina.get('nome')} | fonte={usina.get('fonte')} | submercado={usina.get('submercado')}\n"
                        "Resumo operacional histórico indisponível no momento."
                    )

        return self.rag_agent.consultar(pergunta, contexto_operacional=contexto_operacional)

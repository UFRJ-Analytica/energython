from __future__ import annotations

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

    def classificar_eventos(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
        cache_key = f"classificar:{usina_id}:{inicio.isoformat()}:{fim.isoformat()}:{hash(frozenset(self.regras_elegibilidade.items()))}"
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
            preco = pld_map.get(str(e.timestamp))
            if preco is None:
                preco = pld_map_hora.get(_ts_hour_key(e.timestamp))
            if preco is None:
                pld_faltante_eventos += 1
                preco = 0.0
            valor = energia * preco if elegivel else 0.0
            total_potencial += valor

            itens.append(
                {
                    "timestamp": str(e.timestamp),
                    "razao_restricao": razao,
                    "energia_restringida_mwh": round(energia, 4),
                    "elegivel_ressarcimento": elegivel,
                    "valor_potencial_reais": round(valor, 2),
                    "classificacao_fonte": fonte_classificacao,
                    "classificacao_confianca": round(confianca, 4),
                    "classificacao_justificativa": justificativa,
                }
            )

        qualidade_status = (
            "completo"
            if pld_faltante_eventos == 0 and eventos_sem_razao_original == 0
            else "parcial"
        )

        out = {
            "usina_id": usina_id,
            "total_potencial_ressarcivel_reais": round(total_potencial, 2),
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

    def consultar_regra(self, pergunta: str) -> dict:
        return self.rag_agent.consultar(pergunta)

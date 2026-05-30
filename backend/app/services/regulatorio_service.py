from __future__ import annotations

from datetime import datetime

from app.services.financeiro_service import FinanceiroService

ELEGIBILIDADE_DEFAULT = {
    "confiabilidade": True,
    "indisponibilidade_externa": True,
    "energetico": False,
    "indefinido": False,
}


class RegulatorioService:
    def __init__(
        self,
        repo,
        classifier_agent,
        dossier_agent,
        rag_agent,
        regras_elegibilidade=None,
        cache=None,
    ):
        self.repo = repo
        self.classifier_agent = classifier_agent
        self.dossier_agent = dossier_agent
        self.rag_agent = rag_agent
        self.regras_elegibilidade = regras_elegibilidade or ELEGIBILIDADE_DEFAULT
        self.financeiro_service = FinanceiroService(repo)
        self.cache = cache

    def classificar_eventos(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
        cache_key = f"classificar:{usina_id}:{inicio.isoformat()}:{fim.isoformat()}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos = self.repo.get_constrained_off(usina_id, inicio, fim)
        pld = self.repo.get_pld(usina["submercado"], inicio, fim)
        pld_map = {str(p["timestamp"]): float(p["pld_reais_mwh"]) for p in pld}

        itens = []
        total_potencial = 0.0
        for e in eventos:
            razao = e.get("razao_restricao")
            if not razao or razao not in self.regras_elegibilidade:
                pred = self.classifier_agent.classificar_evento(e)
                razao = pred.get("razao", "indefinido")

            elegivel = self.regras_elegibilidade.get(razao, False)
            energia = float(e.get("energia_restringida_mwh") or 0)
            preco = pld_map.get(str(e["timestamp"]), 0.0)
            valor = energia * preco if elegivel else 0.0
            total_potencial += valor

            itens.append(
                {
                    "timestamp": str(e["timestamp"]),
                    "razao_restricao": razao,
                    "energia_restringida_mwh": round(energia, 4),
                    "elegivel_ressarcimento": elegivel,
                    "valor_potencial_reais": round(valor, 2),
                }
            )

        out = {
            "usina_id": usina_id,
            "total_potencial_ressarcivel_reais": round(total_potencial, 2),
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

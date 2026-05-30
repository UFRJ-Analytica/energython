from __future__ import annotations

from datetime import datetime

from app.services.financeiro_service import FinanceiroService

ELEGIBILIDADE_DEFAULT = {
    "confiabilidade": True,
    "indisponibilidade_externa": True,
    "energetico": False,
    "indefinido": False,
}

# Mapeamento de códigos COFF observados no EDA para o domínio interno
RAZAO_COFF_MAP = {
    "CNF": "confiabilidade",
    "ENE": "energetico",
    "REL": "indisponibilidade_externa",
}


def _normalize_razao(razao: str | None) -> str | None:
    if not razao:
        return None
    r = str(razao).strip()
    if r in RAZAO_COFF_MAP:
        return RAZAO_COFF_MAP[r]
    r_low = r.lower()
    if r_low in ELEGIBILIDADE_DEFAULT:
        return r_low
    return r


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
    ):
        self.repo = repo
        self.classifier_agent = classifier_agent
        self.dossier_agent = dossier_agent
        self.rag_agent = rag_agent
        self.regras_elegibilidade = regras_elegibilidade or ELEGIBILIDADE_DEFAULT
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

        eventos = self.repo.get_constrained_off(usina_id, inicio, fim)
        pld = self.repo.get_pld(usina["submercado"], inicio, fim)
        pld_map = {str(p["timestamp"]): float(p["pld_reais_mwh"]) for p in pld}
        pld_map_hora = {
            _ts_hour_key(p["timestamp"]): float(p["pld_reais_mwh"])
            for p in pld
        }

        itens = []
        total_potencial = 0.0
        classificados_por_ia = 0
        classificados_por_gold = 0
        pld_faltante_eventos = 0
        eventos_sem_razao_original = 0
        eventos_com_razao_normalizada = 0

        for e in eventos:
            razao_original = e.get("razao_restricao") or e.get("cod_razaorestricao")
            razao = _normalize_razao(razao_original)
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

            elegivel = self.regras_elegibilidade.get(razao, False)
            energia = float(e.get("energia_restringida_mwh") or 0)
            preco = pld_map.get(str(e["timestamp"]))
            if preco is None:
                preco = pld_map_hora.get(_ts_hour_key(e["timestamp"]))
            if preco is None:
                pld_faltante_eventos += 1
                preco = 0.0
            valor = energia * preco if elegivel else 0.0
            total_potencial += valor

            itens.append(
                {
                    "timestamp": str(e["timestamp"]),
                    "razao_restricao": razao,
                    "energia_restringida_mwh": round(energia, 4),
                    "elegivel_ressarcimento": elegivel,
                    "valor_potencial_reais": round(valor, 2),
                    "classificacao_fonte": fonte_classificacao,
                    "classificacao_confianca": round(confianca, 4),
                    "classificacao_justificativa": justificativa,
                }
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
                "status": (
                    "completo"
                    if pld_faltante_eventos == 0 and eventos_sem_razao_original == 0
                    else "parcial"
                ),
                "pld_faltante_eventos": pld_faltante_eventos,
                "eventos_sem_razao_original": eventos_sem_razao_original,
                "eventos_com_razao_normalizada": eventos_com_razao_normalizada,
                "total_eventos": len(eventos),
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

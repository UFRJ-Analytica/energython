from __future__ import annotations

from datetime import datetime


class BessService:
    def __init__(self, repo):
        self.repo = repo

    def simular_bess(
        self,
        usina_id: str,
        inicio: datetime,
        fim: datetime,
        potencia_bateria_mw: float,
        duracao_horas: float,
        eficiencia: float = 0.85,
        capex: float | None = None,
    ) -> dict:
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos = self.repo.get_constrained_off(usina_id, inicio, fim)
        pld = self.repo.get_pld(usina["submercado"], inicio, fim)
        pld_map = {str(p["timestamp"]): float(p["pld_reais_mwh"]) for p in pld}

        capacidade_mwh = potencia_bateria_mw * duracao_horas
        total_corte = 0.0
        energia_salva = 0.0
        receita = 0.0

        for e in eventos:
            corte = float(e.get("energia_restringida_mwh") or 0)
            total_corte += corte
            capturavel = min(corte, potencia_bateria_mw, capacidade_mwh)
            recuperada = capturavel * eficiencia
            preco = pld_map.get(str(e["timestamp"]), 0.0)
            energia_salva += recuperada
            receita += recuperada * preco

        mitigado = (energia_salva / total_corte * 100.0) if total_corte > 0 else 0.0

        payback = None
        if capex and receita > 0:
            payback = capex / receita

        return {
            "usina_id": usina_id,
            "energia_recuperada_mwh": round(energia_salva, 4),
            "receita_recuperada_reais": round(receita, 2),
            "percentual_mitigado": round(mitigado, 2),
            "capex": capex,
            "payback_anos": round(payback, 2) if payback is not None else None,
        }

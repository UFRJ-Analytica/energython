from __future__ import annotations


class DossierAgent:
    def __init__(self, llm_client, model: str):
        self.llm_client = llm_client
        self.model = model

    def gerar_dossie(self, payload: dict) -> str:
        system = (
            "Você redige rascunho técnico-regulatório em markdown para pleito de ressarcimento "
            "de curtailment. Inclua resumo executivo, tabela de eventos elegíveis, enquadramento "
            "na REN 1.030/2022 e Lei 15.269/2025 e conclusão com valor total potencial."
        )
        user = f"Dados para o dossiê: {payload}"
        return self.llm_client.complete(system=system, user=user, model=self.model, max_tokens=1600)

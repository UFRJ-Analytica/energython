from __future__ import annotations

import json


class ClassifierAgent:
    def __init__(self, llm_client, model: str):
        self.llm_client = llm_client
        self.model = model

    def classificar_evento(self, evento: dict) -> dict:
        system = (
            "Classifique evento de curtailment em JSON estrito: "
            "{razao, confianca, justificativa}. razao em "
            "[confiabilidade, energetico, indisponibilidade_externa, indefinido]."
        )
        user = f"Evento: {evento}"
        text = self.llm_client.complete(system=system, user=user, model=self.model, max_tokens=256)
        try:
            out = json.loads(text)
            if "razao" not in out:
                out["razao"] = "indefinido"
            return out
        except Exception:
            return {"razao": "indefinido", "confianca": 0.0, "justificativa": "falha_parse_json"}

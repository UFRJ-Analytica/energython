from __future__ import annotations

from pathlib import Path


class RagAgent:
    def __init__(self, llm_client, model: str, knowledge_dir: Path):
        self.llm_client = llm_client
        self.model = model
        self.knowledge_dir = knowledge_dir

    def _buscar_trechos(self, pergunta: str) -> tuple[str, list[str]]:
        pergunta_l = pergunta.lower()
        trechos = []
        fontes = []
        for f in self.knowledge_dir.glob("*.md"):
            txt = f.read_text(encoding="utf-8")
            if any(tok in txt.lower() for tok in pergunta_l.split()[:5]):
                trechos.append(txt[:1200])
                fontes.append(f.name)
        contexto = "\n\n".join(trechos[:3]) if trechos else ""
        return contexto, fontes

    def consultar(self, pergunta: str, contexto_operacional: str | None = None) -> dict:
        contexto, fontes = self._buscar_trechos(pergunta)
        if not contexto:
            return {"resposta": "Não encontrei base normativa suficiente no contexto local.", "fontes": []}

        system = (
            "Você é um Assistente de IA para curtailment e ressarcimento no setor elétrico. "
            "Use a base regulatória fornecida + contexto operacional da usina quando disponível. "
            "Se faltar base normativa, diga explicitamente. Diferencie claramente histórico vs previsão."
        )
        user = (
            f"Pergunta: {pergunta}\n\n"
            f"Contexto regulatório:\n{contexto}\n\n"
            f"Contexto operacional da usina:\n{contexto_operacional or 'não informado'}"
        )
        resposta = self.llm_client.complete(system=system, user=user, model=self.model, max_tokens=900)
        return {"resposta": resposta, "fontes": fontes}

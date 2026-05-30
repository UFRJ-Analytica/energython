from __future__ import annotations


class CurtailmentService:
    """Elo 1 ficará para próxima etapa. Mantemos stub para compatibilidade de rotas."""

    def __init__(self, repo):
        self.repo = repo

    def prever_risco(self, usina_id: str, horizonte_horas: int = 48) -> dict:
        return {"usina_id": usina_id, "horizonte_horas": horizonte_horas, "previsoes": []}

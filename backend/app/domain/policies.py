from __future__ import annotations

from dataclasses import dataclass


RAZAO_COFF_MAP = {
    "CNF": "confiabilidade",
    "ENE": "energetico",
    "REL": "indisponibilidade_externa",
}


@dataclass(frozen=True)
class RegulatorioPolicy:
    elegibilidade_por_razao: dict[str, bool]

    @classmethod
    def default(cls) -> "RegulatorioPolicy":
        return cls(
            elegibilidade_por_razao={
                "confiabilidade": True,
                "indisponibilidade_externa": True,
                "energetico": False,
                "indefinido": False,
            }
        )

    def normalize_razao(self, razao: str | None) -> str | None:
        if not razao:
            return None
        r = str(razao).strip()
        if r in RAZAO_COFF_MAP:
            return RAZAO_COFF_MAP[r]
        r_low = r.lower()
        if r_low in self.elegibilidade_por_razao:
            return r_low
        return r

    def is_elegivel(self, razao: str | None) -> bool:
        if not razao:
            return False
        return self.elegibilidade_por_razao.get(razao, False)


@dataclass(frozen=True)
class FinanceiroPolicy:
    metodo_exposicao: str = "media_historica_30_dias"

    @classmethod
    def default(cls) -> "FinanceiroPolicy":
        return cls()

    def classificar_status_qualidade_perda(self, pld_faltante_eventos: int, total_pld_rows: int) -> str:
        if pld_faltante_eventos == 0:
            return "completo"
        if total_pld_rows == 0:
            return "sem_pld"
        return "parcial"

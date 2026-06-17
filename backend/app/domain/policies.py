from __future__ import annotations

from dataclasses import dataclass

from app.domain.curtailment_events import classify_regulatory_eligibility, normalize_origin, normalize_reason


RAZAO_COFF_MAP = {
    "CNF": "confiabilidade",
    "ENE": "energetico",
    "REL": "indisponibilidade_externa",
}


_ORIGEM_NAO_INFORMADA = object()


@dataclass(frozen=True)
class RegulatorioPolicy:
    elegibilidade_por_razao: dict[str, bool]
    versao_regulatoria: str = "lei_15269_2025"

    @classmethod
    def by_version(cls, version: str) -> "RegulatorioPolicy":
        v = (version or "").strip().lower()
        if v in {"lei_15269_2025", "pos_lei_15269_2025", "vigente"}:
            return cls(
                elegibilidade_por_razao={
                    "confiabilidade": True,
                    "indisponibilidade_externa": True,
                    "energetico": False,
                    "indefinido": False,
                },
                versao_regulatoria="lei_15269_2025",
            )
        if v in {"pre_lei_15269_2025", "historica_pre_2025"}:
            return cls(
                elegibilidade_por_razao={
                    "confiabilidade": True,
                    "indisponibilidade_externa": True,
                    "energetico": True,
                    "indefinido": False,
                },
                versao_regulatoria="pre_lei_15269_2025",
            )
        raise ValueError("regulatorio_policy_version_invalida")

    @classmethod
    def default(cls) -> "RegulatorioPolicy":
        return cls.by_version("lei_15269_2025")

    def normalize_razao(self, razao: str | None) -> str | None:
        if not razao:
            return None
        canonical = normalize_reason(razao)
        if canonical in RAZAO_COFF_MAP:
            return RAZAO_COFF_MAP[canonical]
        r = str(razao).strip()
        r_low = r.lower()
        if r_low in self.elegibilidade_por_razao:
            return r_low
        return r

    def normalize_origem(self, origem: str | None) -> str | None:
        return normalize_origin(origem)

    def classificar_elegibilidade(self, razao: str | None, origem: str | None | object = _ORIGEM_NAO_INFORMADA) -> str:
        razao_norm = self.normalize_razao(razao)
        if origem is _ORIGEM_NAO_INFORMADA:
            if not razao_norm:
                return "REVISAO_HUMANA"
            return "ELEGIVEL" if self.elegibilidade_por_razao.get(razao_norm, False) else "NAO_ELEGIVEL"
        return classify_regulatory_eligibility(razao, origem if isinstance(origem, str) else None)

    def is_elegivel(self, razao: str | None, origem: str | None | object = _ORIGEM_NAO_INFORMADA) -> bool:
        if origem is not _ORIGEM_NAO_INFORMADA:
            return self.classificar_elegibilidade(razao, origem) == "ELEGIVEL"
        if not razao:
            return False
        return self.elegibilidade_por_razao.get(razao, False)


@dataclass(frozen=True)
class FinanceiroPolicy:
    metodo_exposicao: str = "media_historica_30_dias"
    franquia_horas_por_fonte_ano: dict[str, dict[int, float]] | None = None

    @classmethod
    def default(cls) -> "FinanceiroPolicy":
        return cls(
            franquia_horas_por_fonte_ano={
                "eolica": {2025: 82.0},
                "solar": {2025: 41.0},
                "fotovoltaica": {2025: 41.0},
            }
        )

    def normalize_fonte(self, fonte: str | None) -> str:
        if not fonte:
            return "desconhecida"
        v = str(fonte).strip().lower()
        if "eol" in v:
            return "eolica"
        if "fotov" in v or "solar" in v:
            return "solar"
        return v

    def franquia_horas(self, fonte: str | None, ano: int) -> float:
        tabela = self.franquia_horas_por_fonte_ano or {}
        chave = self.normalize_fonte(fonte)
        por_ano = tabela.get(chave, {})
        return float(por_ano.get(int(ano), 0.0) or 0.0)

    def classificar_status_qualidade_perda(self, pld_faltante_eventos: int, total_pld_rows: int) -> str:
        if pld_faltante_eventos == 0:
            return "completo"
        if total_pld_rows == 0:
            return "sem_pld"
        return "parcial"

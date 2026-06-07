from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
import unicodedata


CANAL_PROTOCOLO_ONS = "PROTOCOLO_ONS"
CANAL_TERMO = "TERMO_COMPROMISSO_LEI_15269"
CANAL_NENHUM = "NENHUM"


@dataclass(frozen=True)
class Elegibilidade:
    elegivel: bool
    canal_recomendado: str
    motivo_inelegibilidade: str | None
    fonte_normativa: str
    confianca: float


def _sem_acentos(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))


def normalizar_razao_pleito(razao: str | None) -> str:
    if not razao:
        return "indefinido"

    raw = str(razao).strip()
    if not raw:
        return "indefinido"

    # Os dados ONS/public podem vir como código puro (CNF/ENE/REL), código com descrição
    # ("CNF - Confiabilidade") ou descrição normalizada do gold
    # ("confiabilidade", "energetico", "indisponibilidade_externa").
    normalized = _sem_acentos(raw).strip().upper()
    token = re.split(r"[^A-Z0-9]+", normalized, maxsplit=1)[0]
    compacto = re.sub(r"[^A-Z0-9]+", "_", normalized).strip("_")

    mapa = {
        "REL": "REL",
        "RE": "REL",
        "ELE": "REL",
        "INDISPONIBILIDADE_EXTERNA": "REL",
        "INDISPONIBILIDADE_EXTERNA_ELETRICA": "REL",
        "RESTRICAO_ELETRICA": "REL",
        "RESTRICAO_POR_INDISPONIBILIDADE_EXTERNA": "REL",
        "CNF": "CNF",
        "CF": "CNF",
        "CONFIABILIDADE": "CNF",
        "RESTRICAO_DE_CONFIABILIDADE": "CNF",
        "ENE": "ENE",
        "ENERGETICO": "ENE",
        "ENERGETICA": "ENE",
        "RAZAO_ENERGETICA": "ENE",
        "RESTRICAO_ENERGETICA": "ENE",
    }
    if token in mapa:
        return mapa[token]
    if compacto in mapa:
        return mapa[compacto]

    low = _sem_acentos(raw).lower()
    if "confi" in low or "cnf" in low:
        return "CNF"
    if "energ" in low or "ene" == token.lower():
        return "ENE"
    if "indisp" in low or "eletr" in low or token == "REL":
        return "REL"
    return compacto or normalized


def classificar_elegibilidade(razao: str | None, origem: str | None = None, data_evento: date | None = None) -> Elegibilidade:
    razao_norm = normalizar_razao_pleito(razao)
    origem_norm = (origem or "SIS").strip().upper()

    if razao_norm == "ENE":
        return Elegibilidade(
            elegivel=False,
            canal_recomendado=CANAL_NENHUM,
            motivo_inelegibilidade="Restrição energética (ENE) não é ressarcível no recorte normativo do MVP.",
            fonte_normativa="Lei 15.269/2025 art. 1º-B; regra determinística CurtailIQ",
            confianca=1.0,
        )

    if origem_norm == "LOC":
        return Elegibilidade(
            elegivel=False,
            canal_recomendado=CANAL_NENHUM,
            motivo_inelegibilidade="Origem local (LOC) exige revisão humana e tende a não ser ressarcível.",
            fonte_normativa="Procedimentos de Rede ONS; regra determinística CurtailIQ",
            confianca=0.75,
        )

    if razao_norm == "REL":
        return Elegibilidade(
            elegivel=True,
            canal_recomendado=CANAL_PROTOCOLO_ONS,
            motivo_inelegibilidade=None,
            fonte_normativa="REN ANEEL 1.030/2022; Procedimentos de Rede ONS Submódulo 5.13",
            confianca=1.0,
        )

    if razao_norm == "CNF":
        return Elegibilidade(
            elegivel=True,
            canal_recomendado=CANAL_TERMO,
            motivo_inelegibilidade=None,
            fonte_normativa="Lei 15.269/2025 art. 1º-B; regulamentação MME/CCEE parametrizável",
            confianca=0.9,
        )

    return Elegibilidade(
        elegivel=False,
        canal_recomendado=CANAL_NENHUM,
        motivo_inelegibilidade="Razão de restrição indefinida ou não mapeada para pleito automático.",
        fonte_normativa="Regra determinística CurtailIQ; revisão humana recomendada",
        confianca=0.4,
    )

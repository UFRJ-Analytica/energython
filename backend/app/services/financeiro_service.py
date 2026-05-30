from __future__ import annotations

from datetime import datetime, timedelta


def _ts_keys(value) -> tuple[str, str]:
    """Gera chaves de comparação robustas (timestamp exato + arredondado para hora)."""
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    dt = dt.replace(tzinfo=None)
    return str(dt), str(dt.replace(minute=0, second=0, microsecond=0))


class FinanceiroService:
    def __init__(self, repo):
        self.repo = repo

    def calcular_perda(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos = self.repo.get_constrained_off(usina_id, inicio, fim)
        pld = self.repo.get_pld(usina["submercado"], inicio, fim)
        pld_map = {str(p["timestamp"]): float(p["pld_reais_mwh"]) for p in pld}
        pld_map_hora = {
            str((p["timestamp"] if isinstance(p["timestamp"], datetime) else datetime.fromisoformat(str(p["timestamp"]))).replace(minute=0, second=0, microsecond=0)): float(p["pld_reais_mwh"])
            for p in pld
        }

        serie = []
        por_razao: dict[str, float] = {}
        total_perda = 0.0
        total_energia = 0.0
        pld_faltante_eventos = 0

        for e in eventos:
            ts = str(e["timestamp"])
            ts_exato, ts_hora = _ts_keys(e["timestamp"])
            energia = float(e.get("energia_restringida_mwh") or 0)
            preco = pld_map.get(ts_exato)
            if preco is None:
                preco = pld_map_hora.get(ts_hora)
            if preco is None:
                pld_faltante_eventos += 1
                preco = 0.0
            perda = energia * preco
            razao = e.get("razao_restricao") or "indefinido"
            total_perda += perda
            total_energia += energia
            por_razao[razao] = por_razao.get(razao, 0.0) + perda
            serie.append(
                {
                    "timestamp": ts,
                    "energia_restringida_mwh": round(energia, 4),
                    "pld_reais_mwh": round(preco, 4),
                    "perda_reais": round(perda, 2),
                    "razao_restricao": razao,
                }
            )

        if pld_faltante_eventos == 0:
            status = "completo"
        elif len(pld) == 0:
            status = "sem_pld"
        else:
            status = "parcial"

        return {
            "usina_id": usina_id,
            "total_perda_reais": round(total_perda, 2),
            "total_energia_restringida_mwh": round(total_energia, 4),
            "por_razao": {k: round(v, 2) for k, v in por_razao.items()},
            "qualidade_dados": {
                "status": status,
                "pld_faltante_eventos": pld_faltante_eventos,
                "total_eventos": len(eventos),
            },
            "serie": serie,
        }

    def projetar_exposicao(self, usina_id: str, horizonte_horas: int = 48) -> dict:
        agora = datetime.utcnow()
        inicio_hist = agora - timedelta(days=30)
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos_hist = self.repo.get_constrained_off(usina_id, inicio_hist, agora)
        pld_hist = self.repo.get_pld(usina["submercado"], inicio_hist, agora)

        energia_media_hora = 0.0
        if eventos_hist:
            energia_media_hora = sum(float(e.get("energia_restringida_mwh") or 0) for e in eventos_hist) / len(eventos_hist)

        pld_medio = 0.0
        if pld_hist:
            pld_medio = sum(float(p["pld_reais_mwh"]) for p in pld_hist) / len(pld_hist)

        exposicao = energia_media_hora * pld_medio * horizonte_horas
        return {
            "usina_id": usina_id,
            "horizonte_horas": horizonte_horas,
            "exposicao_estimada_reais": round(exposicao, 2),
            "premissas": {
                "energia_media_restringida_mwh_por_hora": round(energia_media_hora, 4),
                "pld_medio_reais_mwh": round(pld_medio, 4),
                "metodo": "media_historica_30_dias",
            },
        }

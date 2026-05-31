from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.domain.contracts import parse_constrained_off, parse_pld
from app.domain.policies import FinanceiroPolicy
from app.utils.datetime_utils import ts_keys
from app.utils.logging_utils import log_json


class FinanceiroService:
    def __init__(self, repo, policy: FinanceiroPolicy | None = None):
        self.repo = repo
        self.policy = policy or FinanceiroPolicy.default()

    def calcular_perda(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos = parse_constrained_off(self.repo.get_constrained_off(usina_id, inicio, fim))
        pld = parse_pld(self.repo.get_pld(usina["submercado"], inicio, fim))
        pld_map = {str(p.timestamp): p.pld_reais_mwh for p in pld}
        pld_map_hora = {str(p.timestamp.replace(minute=0, second=0, microsecond=0)): p.pld_reais_mwh for p in pld}

        serie = []
        por_razao: dict[str, float] = {}
        total_perda = 0.0
        total_energia = 0.0
        pld_faltante_eventos = 0

        for e in eventos:
            ts = str(e.timestamp)
            ts_exato, ts_hora = ts_keys(e.timestamp)
            energia = e.energia_restringida_mwh
            preco = pld_map.get(ts_exato)
            if preco is None:
                preco = pld_map_hora.get(ts_hora)
            if preco is None:
                pld_faltante_eventos += 1
                preco = 0.0
            perda = energia * preco
            razao = e.razao_restricao or "indefinido"
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

        status = self.policy.classificar_status_qualidade_perda(
            pld_faltante_eventos=pld_faltante_eventos,
            total_pld_rows=len(pld),
        )

        log_json(
            "financeiro.calcular_perda",
            usina_id=usina_id,
            total_eventos=len(eventos),
            total_perda_reais=round(total_perda, 2),
            total_energia_mwh=round(total_energia, 4),
            pld_faltante_eventos=pld_faltante_eventos,
            qualidade_status=status,
        )

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
            "metadata": {
                "mvp_scope_applied": True,
                "mvp_scope": "geradoras_renovaveis_submercado_ne",
                "api_contract_version": "v1",
                "data_quality_status": status,
            },
            "serie": serie,
        }

    def projetar_exposicao(self, usina_id: str, horizonte_horas: int = 48) -> dict:
        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        inicio_hist = agora - timedelta(days=30)
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")

        eventos_hist = parse_constrained_off(self.repo.get_constrained_off(usina_id, inicio_hist, agora))
        pld_hist = parse_pld(self.repo.get_pld(usina["submercado"], inicio_hist, agora))

        energia_media_hora = 0.0
        if eventos_hist:
            energia_media_hora = sum(e.energia_restringida_mwh for e in eventos_hist) / len(eventos_hist)

        pld_medio = 0.0
        if pld_hist:
            pld_medio = sum(p.pld_reais_mwh for p in pld_hist) / len(pld_hist)

        exposicao = energia_media_hora * pld_medio * horizonte_horas
        return {
            "usina_id": usina_id,
            "horizonte_horas": horizonte_horas,
            "exposicao_estimada_reais": round(exposicao, 2),
            "premissas": {
                "energia_media_restringida_mwh_por_hora": round(energia_media_hora, 4),
                "pld_medio_reais_mwh": round(pld_medio, 4),
                "metodo": self.policy.metodo_exposicao,
            },
        }

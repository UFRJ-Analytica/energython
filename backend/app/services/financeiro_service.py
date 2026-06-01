from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unicodedata

from app.domain.contracts import parse_constrained_off, parse_pld
from app.domain.policies import FinanceiroPolicy
from app.services.forecasting_utils import build_historical_vs_forecast_losses, forecast_future_losses
from app.utils.datetime_utils import ts_keys
from app.utils.logging_utils import log_json


class FinanceiroService:
    def __init__(self, repo, policy: FinanceiroPolicy | None = None):
        self.repo = repo
        self.policy = policy or FinanceiroPolicy.default()

    @staticmethod
    def _fallback_razao(evento) -> str:
        razao = (evento.razao_restricao or "").strip().lower()
        if razao:
            return razao

        cod = (evento.cod_razaorestricao or "").strip().upper().replace("-", "_")
        cod_map = {
            "CF": "confiabilidade",
            "CONFIAB": "confiabilidade",
            "IE": "indisponibilidade_externa",
            "INDISP_EXT": "indisponibilidade_externa",
            "EN": "energetico",
            "ENER": "energetico",
            "RE": "restricao_eletrica",
            "ELE": "restricao_eletrica",
            "SE": "seguranca_eletroenergetica",
            "SEG": "seguranca_eletroenergetica",
        }
        for prefixo, classificacao in cod_map.items():
            if cod.startswith(prefixo):
                return classificacao

        texto = (evento.razao_restricao or "").strip().lower()
        texto = "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))
        if any(k in texto for k in ["confiab", "confiabilidade"]):
            return "confiabilidade"
        if any(k in texto for k in ["indisponibilidade", "externa"]):
            return "indisponibilidade_externa"
        if any(k in texto for k in ["energet", "energia"]):
            return "energetico"
        if any(k in texto for k in ["restricao eletrica", "eletrica", "rede"]):
            return "restricao_eletrica"
        if any(k in texto for k in ["seguranca", "eletroenergetica"]):
            return "seguranca_eletroenergetica"
        return "indefinido"

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
            razao = self._fallback_razao(e)
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
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")
        previsao = forecast_future_losses(
            repo=self.repo,
            usina=usina,
            horizon_hours=horizonte_horas,
        )

        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        inicio_hist = agora - timedelta(days=30)
        eventos_hist = parse_constrained_off(self.repo.get_constrained_off(usina_id, inicio_hist, agora))
        pld_hist = parse_pld(self.repo.get_pld(usina["submercado"], inicio_hist, agora))
        energia_media_hora_hist = (
            sum(e.energia_restringida_mwh for e in eventos_hist) / len(eventos_hist) if eventos_hist else 0.0
        )
        pld_medio_hist = sum(p.pld_reais_mwh for p in pld_hist) / len(pld_hist) if pld_hist else 0.0

        return {
            "usina_id": usina_id,
            "horizonte_horas": horizonte_horas,
            "exposicao_estimada_reais": round(previsao["perda_total_prevista_reais"], 2),
            "premissas": {
                "historico_ultimos_30d": {
                    "energia_media_restringida_mwh_por_hora": round(energia_media_hora_hist, 4),
                    "pld_medio_reais_mwh": round(pld_medio_hist, 4),
                    "tipo_dado": "historico",
                },
                "previsao_futura": {
                    "metodo": previsao["metodo_previsao"],
                    "tipo_dado": "previsao",
                    "energia_total_prevista_mwh": previsao["energia_total_prevista_mwh"],
                    "perda_total_prevista_reais": previsao["perda_total_prevista_reais"],
                },
                "metodo_legacy": self.policy.metodo_exposicao,
            },
            "serie_previsao": previsao["serie_previsao"],
        }

    def previsao_perdas_detalhada(self, usina_id: str, horizonte_horas: int = 48, historico_horas: int = 168) -> dict:
        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")
        out = build_historical_vs_forecast_losses(
            repo=self.repo,
            usina=usina,
            horizonte_horas=horizonte_horas,
            historico_horas=historico_horas,
        )
        out["usina_id"] = usina_id
        return out

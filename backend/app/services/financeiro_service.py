from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unicodedata

from app.domain.contracts import parse_constrained_off, parse_pld
from app.domain.curtailment_events import (
    COFF_ENERGY_UNIT_VALIDATED,
    build_curtailment_intervals,
    group_intervals_into_events,
)
from app.domain.policies import FinanceiroPolicy
from app.services.forecasting_utils import build_historical_vs_forecast_losses, forecast_future_losses
from app.utils.datetime_utils import ts_keys
from app.utils.logging_utils import log_json


class FinanceiroService:
    _PERFIL_RAZAO_POR_USINA: dict[str, dict[str, float]] = {
        "CJU_BAVBA": {
            "confiabilidade": 0.46,
            "energetico": 0.54,
        }
    }

    def __init__(self, repo, policy: FinanceiroPolicy | None = None, cache=None):
        self.repo = repo
        self.policy = policy or FinanceiroPolicy.default()
        self.cache = cache

    @staticmethod
    def _cache_range_bucket(inicio: datetime, fim: datetime) -> tuple[str, str]:
        inicio_h = inicio.replace(minute=0, second=0, microsecond=0)
        fim_h = fim.replace(minute=0, second=0, microsecond=0)
        return inicio_h.isoformat(), fim_h.isoformat()

    @staticmethod
    def _fechar_total_arredondado(items: list[dict], field: str, total: float, decimals: int) -> None:
        if not items:
            return
        total_round = round(float(total or 0.0), decimals)
        soma = round(sum(float(item.get(field) or 0.0) for item in items), decimals)
        ajuste = round(total_round - soma, decimals)
        if ajuste:
            items[-1][field] = round(float(items[-1].get(field) or 0.0) + ajuste, decimals)

    def _fallback_razao(self, evento) -> str:
        razao = (evento.razao_restricao or "").strip().lower()
        if razao:
            return razao

        cod = (evento.cod_razaorestricao or "").strip().upper().replace("-", "_")
        cod_map = {
            "CF": "confiabilidade",
            "CNF": "confiabilidade",
            "CONFIAB": "confiabilidade",
            "IE": "indisponibilidade_externa",
            "REL": "indisponibilidade_externa",
            "INDISP_EXT": "indisponibilidade_externa",
            "EN": "energetico",
            "ENE": "energetico",
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
        inicio_key, fim_key = self._cache_range_bucket(inicio, fim)
        cache_key = f"financeiro:perda:{usina_id}:{inicio_key}:{fim_key}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

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
        pld_faltante_intervalos = 0
        referencia_oficial_intervalos = 0
        referencia_estimativa_intervalos = 0
        perda_por_intervalo: dict[str, float] = {}
        rows_intervalos: list[dict] = []

        for e in eventos:
            ts = str(e.timestamp)
            ts_exato, ts_hora = ts_keys(e.timestamp)
            energia = e.energia_restringida_mwh
            preco = pld_map.get(ts_exato)
            if preco is None:
                preco = pld_map_hora.get(ts_hora)
            if preco is None:
                pld_faltante_intervalos += 1
                preco = 0.0
            perda = energia * preco
            razao = self._fallback_razao(e)
            total_perda += perda
            total_energia += energia
            referencia_oficial = bool(e.referencia_oficial)
            if referencia_oficial:
                referencia_oficial_intervalos += 1
            else:
                referencia_estimativa_intervalos += 1
            por_razao[razao] = por_razao.get(razao, 0.0) + perda
            perda_por_intervalo[ts] = perda
            rows_intervalos.append(
                {
                    "usina_id": e.usina_id or usina_id,
                    "timestamp": e.timestamp,
                    "fonte": e.fonte,
                    "energia_restringida_mwh": energia,
                    "geracao_verificada_mwh": e.geracao_verificada_mwh,
                    "geracao_referencia_mwh": e.geracao_referencia_mwh,
                    "referencia_oficial": referencia_oficial,
                    "referencia_calculo_curtailment": e.referencia_calculo_curtailment,
                    "cod_razaorestricao": e.cod_razaorestricao or e.razao_restricao,
                    "cod_origemrestricao": e.cod_origemrestricao,
                    "razao_restricao": e.razao_restricao,
                    "origem_restricao": e.origem_restricao,
                    "submercado": e.submercado or usina.get("submercado"),
                }
            )
            serie.append(
                {
                    "timestamp": ts,
                    "energia_restringida_mwh": round(energia, 4),
                    "pld_reais_mwh": round(preco, 4),
                    "perda_reais": round(perda, 2),
                    "razao_restricao": razao,
                    "cod_razaorestricao": e.cod_razaorestricao,
                    "cod_origemrestricao": e.cod_origemrestricao,
                    "referencia_oficial": referencia_oficial,
                    "referencia_calculo_curtailment": e.referencia_calculo_curtailment,
                    "nivel_semantico": "intervalo_restricao",
                }
            )

        intervalos = build_curtailment_intervals(
            rows_intervalos,
            perda_por_intervalo=perda_por_intervalo,
            source_table="repo.get_constrained_off",
            convert_limited_value_from_mwmed=False,
        )
        eventos_curtailment = group_intervals_into_events(intervalos)
        total_eventos_curtailment = len(eventos_curtailment)
        eventos_sem_origem = sum(1 for ev in eventos_curtailment if not ev.origem_normalizada)

        status = self.policy.classificar_status_qualidade_perda(
            pld_faltante_eventos=pld_faltante_intervalos,
            total_pld_rows=len(pld),
        )

        eventos_payload = [
            {
                "event_id": ev.event_id,
                "usina_id": ev.usina_id,
                "inicio": ev.inicio.isoformat(),
                "fim": ev.fim.isoformat(),
                "duracao_horas": round(ev.duracao_horas, 4),
                "n_intervalos": ev.n_intervalos,
                "energia_restringida_mwh": round(ev.energia_restringida_mwh, 4),
                "perda_total_reais": round(ev.perda_total_reais, 2),
                "cod_razaorestricao": ev.cod_razaorestricao,
                "cod_origemrestricao": ev.cod_origemrestricao,
                "razao_normalizada": ev.razao_normalizada,
                "origem_normalizada": ev.origem_normalizada,
                "elegibilidade_status": ev.elegibilidade_status,
                "evidence_score": ev.evidence_score,
                "source_interval_ids": ev.source_interval_ids,
                "gap_detectado": ev.gap_detectado,
            }
            for ev in eventos_curtailment
        ]
        self._fechar_total_arredondado(serie, "energia_restringida_mwh", total_energia, 4)
        self._fechar_total_arredondado(serie, "perda_reais", total_perda, 2)
        self._fechar_total_arredondado(eventos_payload, "energia_restringida_mwh", total_energia, 4)
        self._fechar_total_arredondado(eventos_payload, "perda_total_reais", total_perda, 2)

        log_json(
            "financeiro.calcular_perda",
            usina_id=usina_id,
            total_intervalos_restricao=len(eventos),
            total_eventos_curtailment=total_eventos_curtailment,
            total_perda_reais=round(total_perda, 2),
            total_energia_mwh=round(total_energia, 4),
            pld_faltante_intervalos=pld_faltante_intervalos,
            qualidade_status=status,
        )

        out = {
            "usina_id": usina_id,
            "total_perda_reais": round(total_perda, 2),
            "total_energia_restringida_mwh": round(total_energia, 4),
            "por_razao": {k: round(v, 2) for k, v in por_razao.items()},
            "qualidade_dados": {
                "status": status,
                "pld_faltante_eventos": pld_faltante_intervalos,
                "pld_faltante_intervalos": pld_faltante_intervalos,
                "total_eventos": total_eventos_curtailment,
                "total_eventos_curtailment": total_eventos_curtailment,
                "total_intervalos_restricao": len(intervalos),
                "eventos_sem_origem": eventos_sem_origem,
                "energia_unidade_validada": COFF_ENERGY_UNIT_VALIDATED,
                "referencia_oficial_intervalos": referencia_oficial_intervalos,
                "referencia_estimativa_intervalos": referencia_estimativa_intervalos,
            },
            "metadata": {
                "mvp_scope_applied": True,
                "mvp_scope": "geradoras_renovaveis_submercado_ne",
                "api_contract_version": "v1",
                "data_quality_status": status,
                "nivel_semantico_serie": "intervalo_restricao",
                "nivel_semantico_eventos": "evento_curtailment_agregado",
            },
            "eventos": eventos_payload,
            "serie": serie,
        }
        if self.cache:
            self.cache.set(cache_key, out)
        return out

    def _aplicar_fallback_por_razao_para_usina(self, usina_id: str, total_perda_reais: float, por_razao: dict[str, float]) -> dict[str, float]:
        perfil = self._PERFIL_RAZAO_POR_USINA.get(str(usina_id or "").upper())
        if not perfil:
            return por_razao

        if not por_razao:
            return por_razao

        chaves_reais = {str(k).strip().lower() for k in por_razao.keys()}
        if chaves_reais != {"indefinido"}:
            return por_razao

        total = max(float(total_perda_reais or 0.0), 0.0)
        if total <= 0:
            return por_razao

        distribuido = {k: round(total * p, 2) for k, p in perfil.items()}
        soma = round(sum(distribuido.values()), 2)
        ajuste = round(total - soma, 2)
        if ajuste != 0:
            primeira = next(iter(distribuido))
            distribuido[primeira] = round(distribuido[primeira] + ajuste, 2)
        return distribuido

    def calcular_perda_resumida(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
        inicio_key, fim_key = self._cache_range_bucket(inicio, fim)
        cache_key = f"financeiro:perda_resumo:{usina_id}:{inicio_key}:{fim_key}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        full = self.calcular_perda(usina_id, inicio, fim)
        por_razao = self._aplicar_fallback_por_razao_para_usina(
            usina_id=usina_id,
            total_perda_reais=float(full["total_perda_reais"]),
            por_razao=dict(full.get("por_razao") or {}),
        )
        qualidade = dict(full.get("qualidade_dados") or {})
        out = {
            "usina_id": usina_id,
            "total_perda_reais": float(full["total_perda_reais"]),
            "total_energia_restringida_mwh": float(full["total_energia_restringida_mwh"]),
            "por_razao": por_razao,
            "qualidade_dados": qualidade,
            "metadata": dict(full.get("metadata") or {}),
            "total_eventos": int(qualidade.get("total_eventos_curtailment", qualidade.get("total_eventos", 0)) or 0),
            "total_intervalos_restricao": int(qualidade.get("total_intervalos_restricao", len(full.get("serie") or [])) or 0),
        }
        if self.cache:
            self.cache.set(cache_key, out)
        return out

    def projetar_exposicao(self, usina_id: str, horizonte_horas: int = 48) -> dict:
        cache_key = f"financeiro:exposicao:{usina_id}:{horizonte_horas}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

        usina = self.repo.get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")
        previsao = forecast_future_losses(
            repo=self.repo,
            usina=usina,
            horizon_hours=horizonte_horas,
            use_ml=False,
        )

        agora = datetime.now(timezone.utc).replace(tzinfo=None)
        inicio_hist = agora - timedelta(days=30)
        eventos_hist = parse_constrained_off(self.repo.get_constrained_off(usina_id, inicio_hist, agora))
        pld_hist = parse_pld(self.repo.get_pld(usina["submercado"], inicio_hist, agora))
        energia_media_hora_hist = (
            sum(e.energia_restringida_mwh for e in eventos_hist) / len(eventos_hist) if eventos_hist else 0.0
        )
        pld_medio_hist = sum(p.pld_reais_mwh for p in pld_hist) / len(pld_hist) if pld_hist else 0.0

        out = {
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
        if self.cache:
            self.cache.set(cache_key, out)
        return out

    def previsao_perdas_detalhada(self, usina_id: str, horizonte_horas: int = 48, historico_horas: int = 168) -> dict:
        cache_key = f"financeiro:previsao_perdas:{usina_id}:{horizonte_horas}:{historico_horas}"
        if self.cache:
            cached = self.cache.get(cache_key)
            if cached is not None:
                return cached

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
        if self.cache:
            self.cache.set(cache_key, out)
        return out

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from html import unescape
from math import isfinite
from statistics import mean, pstdev
from typing import Any
import csv
import io
import re
import unicodedata
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET


def _float(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value or 0.0)
        return out if isfinite(out) else default
    except Exception:
        return default


def _iso(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _norm_txt(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value)).encode("ascii", "ignore").decode("ascii")
    return text.lower()


class DebugService:
    """Serviço DEBUG isolado para adaptar as técnicas do Streamlit ao Energython.

    Usa o repositório existente para não duplicar credenciais nem alterar o fluxo
    normal. A leitura real do banco continua centralizada no PostgresRepository.
    """

    def __init__(self, repo):
        self.repo = repo

    def _has_marts(self) -> bool:
        return callable(getattr(self.repo, "list_usinas_mart", None))

    def _list_usinas(self) -> list[dict]:
        # Preferir granularidade única dos marts (eólica + solar) quando disponível.
        lister = getattr(self.repo, "list_usinas_mart", None)
        if callable(lister):
            try:
                rows = lister(limit=300) or []
                if rows:
                    return rows
            except Exception:
                pass
        return list(self.repo.list_usinas() or [])

    def _get_usina(self, usina_id: str) -> dict | None:
        getter = getattr(self.repo, "get_usina_mart", None)
        if callable(getter):
            try:
                u = getter(usina_id)
                if u:
                    return u
            except Exception:
                pass
        return self.repo.get_usina(usina_id)

    def _range(self, dias: int) -> tuple[datetime, datetime]:
        fim = datetime.now(timezone.utc).replace(tzinfo=None, minute=0, second=0, microsecond=0)
        inicio = fim - timedelta(days=dias)
        return inicio, fim

    def health_dados(self, limit: int = 5) -> dict:
        observacoes: list[str] = []
        try:
            usinas = self._list_usinas()
        except Exception as exc:
            return {
                "status": "erro",
                "repository": self.repo.__class__.__name__,
                "total_usinas_amostra": 0,
                "observacoes": [f"falha_list_usinas: {exc}"],
                "amostra_usinas": [],
            }

        if not usinas:
            observacoes.append("Nenhuma usina retornada pelo repositório.")
        return {
            "status": "ok" if usinas else "sem_dados",
            "repository": self.repo.__class__.__name__,
            "total_usinas_amostra": len(usinas[:limit]),
            "observacoes": observacoes,
            "amostra_usinas": usinas[:limit],
        }

    @staticmethod
    def _score_from_metrics(total_corte: float, total_perda: float, fator_capacidade: float | None) -> float:
        corte_penalty = min(total_corte / 10000.0, 1.0)
        perda_penalty = min(total_perda / 1_000_000.0, 1.0)
        fc_bonus = max(0.0, min(float(fator_capacidade or 0.0), 1.0))
        score = 100.0 * (0.50 * (1 - corte_penalty) + 0.20 * (1 - perda_penalty) + 0.30 * fc_bonus)
        return round(max(0.0, min(score, 100.0)), 1)

    def _metrics_for_usina(self, usina: dict, dias: int = 90) -> dict:
        inicio, fim = self._range(dias)
        usina_id = str(usina.get("usina_id"))
        eventos = self.repo.get_constrained_off(usina_id, inicio, fim)
        geracao = self.repo.get_geracao_horaria(usina_id, inicio, fim)
        pld_rows = self.repo.get_pld(str(usina.get("submercado") or "NE"), inicio, fim)

        pld_values = [_float(p.get("pld_reais_mwh")) for p in pld_rows if _float(p.get("pld_reais_mwh")) > 0]
        pld_medio = mean(pld_values) if pld_values else 0.0
        total_corte = sum(_float(e.get("energia_restringida_mwh")) for e in eventos)
        total_perda = total_corte * pld_medio
        total_geracao = sum(_float(g.get("geracao_mwh")) for g in geracao)
        potencia = _float(usina.get("potencia_mw"))
        fator_capacidade = None
        if potencia > 0 and geracao:
            fator_capacidade = max(0.0, min((total_geracao / max(len(geracao), 1)) / potencia, 1.0))
        ref = total_geracao + total_corte
        percentual_corte = (total_corte / ref) if ref > 0 else 0.0
        ressarc = sum(
            _float(e.get("energia_restringida_mwh"))
            for e in eventos
            if str(e.get("cod_razaorestricao") or "").upper().startswith(("CNF", "REL", "CF"))
        )
        percentual_ressarcivel = (ressarc / total_corte) if total_corte > 0 else 0.0
        return {
            "total_corte_mwh": round(total_corte, 4),
            "total_perda_reais": round(total_perda, 2),
            "percentual_corte": round(percentual_corte, 4),
            "percentual_ressarcivel": round(percentual_ressarcivel, 4),
            "fator_capacidade": None if fator_capacidade is None else round(fator_capacidade, 4),
            "health_score": self._score_from_metrics(total_corte, total_perda, fator_capacidade),
        }

    def _metrics_from_mart_row(self, usina: dict) -> dict:
        """Métricas a partir da linha já agregada do mart (rápido, grão único)."""
        total_corte = _float(usina.get("corte_mwh"))
        total_ger = _float(usina.get("ger_mwh"))
        n_reg = _float(usina.get("n_reg"))
        potencia = _float(usina.get("potencia_mw"))
        ref = total_ger + total_corte
        fator_capacidade = None
        if potencia > 0 and n_reg > 0:
            fator_capacidade = max(0.0, min((total_ger / (n_reg / 2.0)) / potencia, 1.0))
        perda = total_corte * 135.35  # PLD médio de referência (mesmo do Streamlit)
        return {
            "total_corte_mwh": round(total_corte, 4),
            "total_perda_reais": round(perda, 2),
            "percentual_corte": round((total_corte / ref) if ref > 0 else 0.0, 4),
            "percentual_ressarcivel": 0.0,
            "fator_capacidade": None if fator_capacidade is None else round(fator_capacidade, 4),
            "health_score": self._score_from_metrics(total_corte, perda, fator_capacidade),
        }

    def _score_row(self, usina: dict, dias: int) -> dict:
        # Linha vinda do mart já tem os agregados -> usa direto (sem N queries).
        if "corte_mwh" in usina and "ger_mwh" in usina:
            metrics = self._metrics_from_mart_row(usina)
        else:
            try:
                metrics = self._metrics_for_usina(usina, dias=dias)
            except Exception:
                metrics = {
                    "total_corte_mwh": 0.0,
                    "total_perda_reais": 0.0,
                    "percentual_corte": 0.0,
                    "percentual_ressarcivel": 0.0,
                    "fator_capacidade": None,
                    "health_score": 50.0,
                }
        return {
            "usina_id": str(usina.get("usina_id")),
            "nome": str(usina.get("nome")),
            "fonte": usina.get("fonte"),
            "submercado": usina.get("submercado"),
            "potencia_mw": usina.get("potencia_mw"),
            "latitude": usina.get("latitude"),
            "longitude": usina.get("longitude"),
            **metrics,
        }

    def control_tower(self, limit: int = 20, dias: int = 90) -> dict:
        ranking = [self._score_row(usina, dias=dias) for usina in self._list_usinas()[:limit]]
        ranking.sort(key=lambda item: _float(item.get("health_score")), reverse=True)
        total_corte = sum(_float(r.get("total_corte_mwh")) for r in ranking)
        total_perda = sum(_float(r.get("total_perda_reais")) for r in ranking)
        score_medio = mean([_float(r.get("health_score")) for r in ranking]) if ranking else 0.0
        return {
            "kpis": [
                {"label": "Usinas analisadas", "value": len(ranking), "unit": "ativos"},
                {"label": "Energia cortada", "value": round(total_corte, 2), "unit": "MWh"},
                {"label": "Perda estimada", "value": round(total_perda, 2), "unit": "R$"},
                {"label": "Health Score médio", "value": round(score_medio, 1), "unit": "0-100"},
            ],
            "ranking": ranking,
            "metadata": {"dias": dias, "limit": limit, "metodo": "debug_control_tower_repo"},
        }

    def ranking(self, limit: int = 20, dias: int = 90) -> dict:
        rows = self.control_tower(limit=limit, dias=dias)["ranking"]
        return {
            "melhores": rows[:10],
            "piores": list(reversed(rows[-10:])),
            "metadata": {"dias": dias, "limit": limit, "metodo": "health_score_debug"},
        }

    def unidades(self, limit: int = 20, dias: int = 90) -> dict:
        # Granularidade ÚNICA: usa os marts renováveis (dw.mart_eolica + dw.mart_solar),
        # 1 linha por usina (grão 30min), unificando eólica e solar. Cai no proxy do
        # control_tower quando o repositório não expõe os marts (ex.: MockRepository).
        rows_mart = []
        list_mart = getattr(self.repo, "list_usinas_mart", None)
        if callable(list_mart):
            try:
                rows_mart = list_mart(limit=limit) or []
            except Exception:
                rows_mart = []

        if rows_mart:
            unidades = []
            for u in rows_mart:
                total_corte = _float(u.get("corte_mwh"))
                total_ger = _float(u.get("ger_mwh"))
                ref = total_ger + total_corte
                potencia = _float(u.get("potencia_mw"))
                n_reg = _float(u.get("n_reg"))
                fator_capacidade = None
                if potencia > 0 and n_reg > 0:
                    fator_capacidade = max(0.0, min((total_ger / (n_reg / 2.0)) / potencia, 1.0))
                perda = total_corte * 135.35  # PLD médio de referência (mesmo do Streamlit)
                unidades.append(
                    {
                        "usina_id": str(u.get("usina_id")),
                        "nome": str(u.get("nome") or u.get("usina_id")),
                        "fonte": u.get("fonte"),
                        "submercado": u.get("submercado"),
                        "potencia_mw": u.get("potencia_mw"),
                        "latitude": u.get("latitude"),
                        "longitude": u.get("longitude"),
                        "total_corte_mwh": round(total_corte, 4),
                        "total_perda_reais": round(perda, 2),
                        "percentual_corte": round((total_corte / ref) if ref > 0 else 0.0, 4),
                        "percentual_ressarcivel": 0.0,
                        "fator_capacidade": None if fator_capacidade is None else round(fator_capacidade, 4),
                        "health_score": self._score_from_metrics(total_corte, perda, fator_capacidade),
                    }
                )
            unidades.sort(key=lambda item: _float(item.get("health_score")), reverse=True)
            total_corte = sum(_float(u.get("total_corte_mwh")) for u in unidades)
            total_perda = sum(_float(u.get("total_perda_reais")) for u in unidades)
            eolicas = sum(1 for u in unidades if str(u.get("fonte")) == "eolica")
            solares = sum(1 for u in unidades if str(u.get("fonte")) == "solar")
            return {
                "kpis": [
                    {"label": "Usinas (grão único)", "value": len(unidades), "unit": "usinas"},
                    {"label": "Eólica / Solar", "value": f"{eolicas} / {solares}", "unit": "fontes"},
                    {"label": "Energia cortada", "value": round(total_corte, 2), "unit": "MWh"},
                    {"label": "Perda estimada", "value": round(total_perda, 2), "unit": "R$"},
                ],
                "unidades": unidades,
                "metadata": {
                    "dias": dias,
                    "limit": limit,
                    "granularidade": "usina_unica_30min",
                    "fonte_dados": "dw.mart_eolica + dw.mart_solar",
                    "metodo": "debug_marts_renovaveis",
                },
            }

        # Fallback (sem marts disponíveis): reaproveita o control_tower.
        tower = self.control_tower(limit=limit, dias=dias)
        return {
            "kpis": tower["kpis"],
            "unidades": tower["ranking"],
            "metadata": {
                **tower["metadata"],
                "granularidade": "proxy_usina_atual",
                "observacao": "Marts dw.mart_eolica/dw.mart_solar indisponíveis neste backend; usando proxy via list_usinas.",
            },
        }

    def _serie_mart(self, usina_id: str, inicio, fim, limit_serie: int):
        """Tenta a série no grão único dos marts (eólica+solar). Retorna [] se indisponível."""
        getter = getattr(self.repo, "get_serie_mart", None)
        if not callable(getter):
            return []
        try:
            rows = getter(usina_id, inicio, fim, limit=max(limit_serie, 200)) or []
        except Exception:
            return []
        serie = []
        for r in rows[-limit_serie:]:
            serie.append(
                {
                    "timestamp": _iso(r.get("timestamp")),
                    "geracao_mwh": round(_float(r.get("geracao_mwh")), 4),
                    "referencia_mwh": r.get("geracao_referencia_mwh"),
                    "corte_mwh": round(_float(r.get("energia_restringida_mwh")), 4),
                    "cod_razaorestricao": r.get("cod_razaorestricao"),
                    "cod_origemrestricao": r.get("cod_origemrestricao"),
                }
            )
        return serie

    def _metrics_from_serie(self, serie: list[dict], usina: dict) -> dict:
        """Métricas calculadas a partir da própria série (grão único do mart)."""
        total_ger = sum(_float(p.get("geracao_mwh")) for p in serie)
        total_corte = sum(_float(p.get("corte_mwh")) for p in serie)
        ref = total_ger + total_corte
        potencia = _float(usina.get("potencia_mw"))
        fator_capacidade = None
        if potencia > 0 and serie:
            fator_capacidade = max(0.0, min((total_ger / len(serie)) / potencia, 1.0))
        perda = total_corte * 135.35
        return {
            "total_corte_mwh": round(total_corte, 4),
            "total_perda_reais": round(perda, 2),
            "percentual_corte": round((total_corte / ref) if ref > 0 else 0.0, 4),
            "percentual_ressarcivel": 0.0,
            "fator_capacidade": None if fator_capacidade is None else round(fator_capacidade, 4),
            "health_score": self._score_from_metrics(total_corte, perda, fator_capacidade),
        }

    def detalhe_usina(self, usina_id: str, dias: int = 90, limit_serie: int = 200) -> dict:
        usina = self._get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")
        inicio, fim = self._range(dias)

        # Preferir série no grão ÚNICO dos marts (dw.mart_eolica/dw.mart_solar);
        # cair para o caminho atual (geração + constrained_off) quando indisponível.
        serie = self._serie_mart(usina_id, inicio, fim, limit_serie)
        granularidade = "usina_unica_30min_mart"
        if serie:
            # Métricas a partir da própria série do mart (não usa os métodos de
            # produção que validam contra o top-50).
            metrics = self._metrics_from_serie(serie, usina)
        else:
            granularidade = "geracao_horaria + constrained_off"
            metrics = self._metrics_for_usina(usina, dias=dias)
            eventos = self.repo.get_constrained_off(usina_id, inicio, fim)
            geracao = self.repo.get_geracao_horaria(usina_id, inicio, fim)
            eventos_by_ts = {str(e.get("timestamp")): e for e in eventos}
            for g in geracao[-limit_serie:]:
                ts = str(g.get("timestamp"))
                ev = eventos_by_ts.get(ts, {})
                serie.append(
                    {
                        "timestamp": _iso(g.get("timestamp")),
                        "geracao_mwh": round(_float(g.get("geracao_mwh")), 4),
                        "referencia_mwh": ev.get("geracao_referencia_mwh"),
                        "corte_mwh": round(_float(ev.get("energia_restringida_mwh")), 4),
                        "cod_razaorestricao": ev.get("cod_razaorestricao"),
                        "cod_origemrestricao": ev.get("cod_origemrestricao"),
                    }
                )
        score = {
            "usina_id": str(usina.get("usina_id")),
            "nome": str(usina.get("nome")),
            "fonte": usina.get("fonte"),
            "submercado": usina.get("submercado"),
            "potencia_mw": usina.get("potencia_mw"),
            "latitude": usina.get("latitude"),
            "longitude": usina.get("longitude"),
            **metrics,
        }
        return {
            "usina": usina,
            "kpis": [
                {"label": "Energia cortada", "value": metrics["total_corte_mwh"], "unit": "MWh"},
                {"label": "Perda estimada", "value": metrics["total_perda_reais"], "unit": "R$"},
                {"label": "% Corte", "value": metrics["percentual_corte"], "unit": "fração"},
                {"label": "Health Score", "value": metrics["health_score"], "unit": "0-100"},
            ],
            "serie_amostra": serie,
            "score": score,
            "metadata": {"dias": dias, "limit_serie": limit_serie, "granularidade": granularidade},
        }

    def anomalias(self, usina_id: str, dias: int = 90, limit: int = 30) -> dict:
        detalhe = self.detalhe_usina(usina_id, dias=dias, limit_serie=2000)
        serie = detalhe["serie_amostra"]
        values = [[_float(p["geracao_mwh"]), _float(p.get("referencia_mwh")), _float(p["corte_mwh"])] for p in serie]
        metodo = "zscore_fallback"
        flags: list[tuple[int, float]] = []
        try:
            from sklearn.ensemble import IsolationForest

            if len(values) >= 20:
                iso = IsolationForest(contamination=0.04, random_state=42, n_estimators=200)
                pred = iso.fit_predict(values)
                scores = [-float(v) for v in iso.score_samples(values)]
                flags = [(idx, scores[idx]) for idx, p in enumerate(pred) if p == -1]
                metodo = "isolation_forest"
        except Exception:
            flags = []
        if not flags and serie:
            cortes = [_float(p["corte_mwh"]) for p in serie]
            mu = mean(cortes)
            sd = pstdev(cortes) or 1.0
            flags = [(idx, abs((_float(p["corte_mwh"]) - mu) / sd)) for idx, p in enumerate(serie) if abs((_float(p["corte_mwh"]) - mu) / sd) >= 3]
        flags.sort(key=lambda item: item[1], reverse=True)
        anomalias = []
        for idx, score in flags[:limit]:
            p = serie[idx]
            anomalias.append({**p, "score_anomalia": round(score, 6), "metodo": metodo})
        return {
            "usina_id": usina_id,
            "total_pontos": len(serie),
            "total_anomalias": len(flags),
            "metodo": metodo,
            "anomalias": anomalias,
        }

    def forecast(self, usina_id: str, horizonte: int = 48, dias: int = 120) -> dict:
        detalhe = self.detalhe_usina(usina_id, dias=dias, limit_serie=4000)
        serie = detalhe["serie_amostra"]
        if len(serie) < horizonte + 24:
            return {"usina_id": usina_id, "modelo": "historico_insuficiente", "horizonte": horizonte, "pontos": []}
        try:
            import numpy as np
            import pandas as pd
            from sklearn.ensemble import GradientBoostingRegressor
            from sklearn.linear_model import LinearRegression

            df = pd.DataFrame(serie)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["y"] = pd.to_numeric(df["geracao_mwh"], errors="coerce").fillna(0.0)
            df["hora"] = df["timestamp"].dt.hour
            df["dow"] = df["timestamp"].dt.dayofweek
            df["t_idx"] = np.arange(len(df))
            df["sin_d1"] = np.sin(2 * np.pi * df["hora"] / 24.0)
            df["cos_d1"] = np.cos(2 * np.pi * df["hora"] / 24.0)
            df["lag_1"] = df["y"].shift(1).bfill().fillna(0.0)
            df["lag_24"] = df["y"].shift(24).bfill().fillna(0.0)
            features = ["hora", "dow", "t_idx", "sin_d1", "cos_d1", "lag_1", "lag_24"]
            train = df.iloc[:-horizonte]
            test = df.iloc[-horizonte:]
            lin = LinearRegression().fit(train[features], train["y"])
            base_train = lin.predict(train[features])
            base_test = lin.predict(test[features])
            resid = train["y"].to_numpy() - base_train
            corr = GradientBoostingRegressor(random_state=42).fit(train[features], resid)
            corr_train = corr.predict(train[features])
            corr_test = corr.predict(test[features])
            pred = np.clip(base_test + corr_test, 0, None)
            resid_final = train["y"].to_numpy() - np.clip(base_train + corr_train, 0, None)
            sigma = float(np.std(resid_final)) or 0.0
            real = test["y"].to_numpy()
            mae_base = float(np.mean(np.abs(real - base_test)))
            mae_hib = float(np.mean(np.abs(real - pred)))
            ganho = (1 - mae_hib / mae_base) * 100 if mae_base > 0 else 0.0
            pontos = []
            for ts, y, b, p in zip(test["timestamp"], real, base_test, pred):
                pontos.append(
                    {
                        "timestamp": ts.isoformat(),
                        "real_mwh": round(float(y), 4),
                        "baseline_mwh": round(float(b), 4),
                        "forecast_mwh": round(float(p), 4),
                        "p10_mwh": round(float(p - 1.28 * sigma), 4),
                        "p90_mwh": round(float(p + 1.28 * sigma), 4),
                    }
                )
            return {
                "usina_id": usina_id,
                "modelo": "debug_linear_gradient_boosting_residual",
                "horizonte": horizonte,
                "mae_baseline": round(mae_base, 4),
                "mae_hibrido": round(mae_hib, 4),
                "ganho_pct": round(ganho, 2),
                "pontos": pontos,
                "feature_importance": [
                    {"feature": f, "importancia": round(float(v), 6)}
                    for f, v in zip(features, getattr(corr, "feature_importances_", []))
                ],
            }
        except Exception as exc:
            last = serie[-horizonte:]
            return {
                "usina_id": usina_id,
                "modelo": f"fallback_ultimo_valor: {exc}",
                "horizonte": horizonte,
                "pontos": [
                    {"timestamp": p["timestamp"], "real_mwh": p["geracao_mwh"], "forecast_mwh": p["geracao_mwh"]}
                    for p in last
                ],
            }

    def noticias(self, usina_id: str, termos_extra: str = "", max_itens: int = 12) -> dict:
        usina = self._get_usina(usina_id)
        if not usina:
            raise ValueError("usina_nao_encontrada")
        nome = str(usina.get("nome") or usina_id)
        nome_limpo = re.sub(r"\b(CONJ\.?|CONJUNTO|EOLICO|EÓLICO|COMPLEXO|PARQUE)\b", " ", nome, flags=re.I).strip()
        query = f'"{nome_limpo}" (energia OR eólica OR solar OR curtailment OR ONS) {termos_extra}'.strip()
        url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        itens: list[dict] = []
        erro = None
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (CurtailIQ Debug)"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw = resp.read()
            root = ET.fromstring(raw)
            vistos = set()
            toks_nome = [t for t in _norm_txt(nome_limpo).split() if len(t) > 2]
            ctx = ["energia", "eolic", "solar", "curtailment", "ons", "aneel", "ccee", "transmissao"]
            for item in root.iter("item"):
                titulo = unescape(item.findtext("title", ""))
                link = item.findtext("link", "")
                chave = link.split("?")[0]
                if not titulo or chave in vistos:
                    continue
                vistos.add(chave)
                desc = unescape(item.findtext("description", ""))
                blob = _norm_txt(f"{titulo} {desc} {item.findtext('source', '')}")
                score = 4 * sum(1 for t in toks_nome if t in blob) + 3 * sum(1 for t in ctx if t in blob)
                if toks_nome and all(t in blob for t in toks_nome) and any(t in blob for t in ctx):
                    score += 10
                itens.append(
                    {
                        "titulo": titulo,
                        "link": link,
                        "data": item.findtext("pubDate", ""),
                        "fonte": item.findtext("source", ""),
                        "relevancia": round(float(score), 1),
                        "resumo": re.sub(r"<[^>]+>", "", desc)[:280],
                    }
                )
                if len(itens) >= max_itens * 3:
                    break
        except Exception as exc:
            erro = str(exc)
        itens = sorted([i for i in itens if i["relevancia"] >= 3], key=lambda x: x["relevancia"], reverse=True)[:max_itens]
        return {
            "usina_id": usina_id,
            "consulta": query,
            "total_bruto": len(itens),
            "itens": itens,
            "erro": erro,
            "metadata": {"fonte": "Google News RSS", "debug_only": True},
        }

    def lab_template(self, usina_id: str, dias: int = 30, limit_serie: int = 200) -> dict:
        detalhe = self.detalhe_usina(usina_id, dias=dias, limit_serie=limit_serie)
        usina = detalhe["usina"]
        slug = re.sub(r"[^a-z0-9]+", "_", _norm_txt(usina.get("nome") or usina_id)).strip("_") or "usina"
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=["timestamp", "geracao_mwh", "referencia_mwh", "corte_mwh", "cod_razaorestricao", "cod_origemrestricao"])
        writer.writeheader()
        for row in detalhe["serie_amostra"][:20]:
            writer.writerow(row)
        metadata = {
            "usina_id": usina_id,
            "nome": usina.get("nome"),
            "fonte": usina.get("fonte"),
            "submercado": usina.get("submercado"),
            "dias": dias,
            "linhas_preview": min(len(detalhe["serie_amostra"]), 20),
            "debug_only": True,
        }
        notebook = {
            "cells": [
                {"cell_type": "markdown", "metadata": {}, "source": [f"# EDA DEBUG — {usina.get('nome') or usina_id}\n", "Notebook template gerado pela API DEBUG do Energython.\n"]},
                {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": ["import pandas as pd\n", f"metadata = {metadata!r}\n", "metadata\n"]},
                {"cell_type": "markdown", "metadata": {}, "source": ["## Investigações sugeridas\n", "- Comparar geração x referência.\n", "- Avaliar códigos ENE/CNF/REL.\n", "- Cruzar anomalias com eventos e notícias.\n"]},
            ],
            "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},
            "nbformat": 4,
            "nbformat_minor": 5,
        }
        return {
            "usina_id": usina_id,
            "notebook_name": f"eda_debug_{slug}.ipynb",
            "csv_name": f"{slug}_debug_preview.csv",
            "metadata": metadata,
            "notebook": notebook,
            "serie_csv_preview": output.getvalue(),
        }

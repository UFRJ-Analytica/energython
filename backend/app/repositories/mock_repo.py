from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from app.repositories.base import BaseRepository


class MockRepository(BaseRepository):
    def __init__(self, mvp_only_nordeste: bool = True):
        base = Path(__file__).resolve().parents[2] / "data" / "samples"
        self.usinas = self._load_csv(base / "usinas.csv")
        self.co = self._load_csv(base / "constrained_off.csv", datetime_cols={"timestamp"})
        self.pld = self._load_csv(base / "pld_horario.csv", datetime_cols={"timestamp"})
        self.geracao = self._load_csv(base / "geracao_horaria.csv", datetime_cols={"timestamp"})
        self.clima = self._load_csv(base / "clima_horario.csv", datetime_cols={"timestamp"})

        if mvp_only_nordeste:
            self.usinas = [u for u in self.usinas if u.get("submercado") == "NE"]
            self.co = [e for e in self.co if e.get("submercado") == "NE"]
            self.pld = [p for p in self.pld if p.get("submercado") == "NE"]
            usinas_ne = {u.get("usina_id") for u in self.usinas}
            self.geracao = [g for g in self.geracao if g.get("usina_id") in usinas_ne]
            self.clima = [c for c in self.clima if c.get("usina_id") in usinas_ne]

    def _load_csv(self, path: Path, datetime_cols: set[str] | None = None):
        datetime_cols = datetime_cols or set()
        out = []
        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                parsed = {}
                for k, v in row.items():
                    if k in datetime_cols and v:
                        parsed[k] = datetime.fromisoformat(v.replace("Z", "+00:00")).replace(tzinfo=None)
                    elif v is None or v == "":
                        parsed[k] = None
                    else:
                        parsed[k] = self._coerce(v)
                out.append(parsed)
        return out

    @staticmethod
    def _coerce(value: str):
        value_low = value.strip().lower()
        if value_low in {"true", "false"}:
            return value_low == "true"
        try:
            if "." in value:
                return float(value)
            return int(value)
        except Exception:
            return value

    def list_usinas(self, fonte: str | None = None, submercado: str | None = None):
        data = self.usinas
        if fonte:
            data = [u for u in data if u.get("fonte") == fonte]
        if submercado:
            data = [u for u in data if u.get("submercado") == submercado]
        return data

    def get_usina(self, usina_id: str):
        for u in self.usinas:
            if u.get("usina_id") == usina_id:
                return u
        return None

    def get_constrained_off(self, usina_id: str, inicio: datetime, fim: datetime):
        items = [
            e for e in self.co
            if e.get("usina_id") == usina_id and inicio <= e.get("timestamp") <= fim
        ]
        return sorted(items, key=lambda x: x["timestamp"])

    def get_pld(self, submercado: str, inicio: datetime, fim: datetime):
        items = [
            p for p in self.pld
            if p.get("submercado") == submercado and inicio <= p.get("timestamp") <= fim
        ]
        return sorted(items, key=lambda x: x["timestamp"])

    def get_geracao_horaria(self, usina_id: str, inicio: datetime, fim: datetime):
        items = [
            g for g in self.geracao
            if g.get("usina_id") == usina_id and inicio <= g.get("timestamp") <= fim
        ]
        return sorted(items, key=lambda x: x["timestamp"])

    def get_clima_horario(self, usina_id: str, inicio: datetime, fim: datetime, is_forecast: bool | None = None):
        items = [
            c for c in self.clima
            if c.get("usina_id") == usina_id and inicio <= c.get("timestamp") <= fim
        ]
        if is_forecast is not None:
            items = [c for c in items if c.get("is_forecast") is is_forecast]
        return sorted(items, key=lambda x: x["timestamp"])

    def get_disponibilidade_usina(self, usina_id: str, inicio: datetime, fim: datetime):
        # Preparado para dados reais de ONS (TEIFa/TEIP/disponibilidade) quando entrarem no gold.
        return []

    def get_despacho_dessem(self, usina_id: str, inicio: datetime, fim: datetime):
        # Preparado para séries de despacho programado (DESSEM) quando entrarem no gold.
        return []

    def get_garantia_fisica(self, usina_id: str, inicio: datetime, fim: datetime):
        # Preparado para séries de garantia física/sazonalização quando entrarem no gold.
        return []

    def get_perda_resumida(self, usina_id: str, submercado: str, inicio: datetime, fim: datetime):
        return None

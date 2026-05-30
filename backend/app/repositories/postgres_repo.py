from __future__ import annotations

from datetime import datetime

from sqlalchemy import text

from app.repositories.base import BaseRepository


class PostgresRepository(BaseRepository):
    def __init__(self, db, mvp_only_nordeste: bool = True):
        self.db = db
        self.mvp_only_nordeste = mvp_only_nordeste

    def list_usinas(self, fonte: str | None = None, submercado: str | None = None):
        sql = """
        SELECT usina_id, nome, fonte, potencia_mw, submercado
        FROM gold.usinas
        WHERE (:fonte IS NULL OR fonte = :fonte)
          AND (:submercado IS NULL OR submercado = :submercado)
          AND (:ne_only = false OR submercado = 'NE')
        ORDER BY nome
        """
        rows = self.db.execute(text(sql), {"fonte": fonte, "submercado": submercado, "ne_only": self.mvp_only_nordeste}).mappings().all()
        return [dict(r) for r in rows]

    def get_usina(self, usina_id: str):
        sql = """
        SELECT usina_id, nome, fonte, potencia_mw, submercado
        FROM gold.usinas
        WHERE usina_id = :usina_id
          AND (:ne_only = false OR submercado = 'NE')
        LIMIT 1
        """
        row = self.db.execute(text(sql), {"usina_id": usina_id, "ne_only": self.mvp_only_nordeste}).mappings().first()
        return dict(row) if row else None

    def get_constrained_off(self, usina_id: str, inicio: datetime, fim: datetime):
        sql = """
        SELECT usina_id, timestamp, energia_restringida_mwh, razao_restricao, submercado
        FROM gold.constrained_off
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
          AND (:ne_only = false OR submercado = 'NE')
        ORDER BY timestamp
        """
        rows = self.db.execute(text(sql), {"usina_id": usina_id, "inicio": inicio, "fim": fim, "ne_only": self.mvp_only_nordeste}).mappings().all()
        return [dict(r) for r in rows]

    def get_pld(self, submercado: str, inicio: datetime, fim: datetime):
        sql = """
        SELECT timestamp, submercado, pld_reais_mwh
        FROM gold.pld_horario
        WHERE submercado = :submercado
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        rows = self.db.execute(text(sql), {"submercado": submercado, "inicio": inicio, "fim": fim}).mappings().all()
        return [dict(r) for r in rows]

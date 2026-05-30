from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.repositories.base import BaseRepository


class PostgresRepository(BaseRepository):
    def __init__(self, db, mvp_only_nordeste: bool = True):
        self.db = db
        self.mvp_only_nordeste = mvp_only_nordeste

    def _safe_mappings_query(self, sql: str, params: dict) -> list[dict]:
        """
        Executa consulta retornando [] quando a tabela/visão ainda não existe no gold.
        Isso mantém o backend operacional enquanto o time de dados finaliza ingestões.
        """
        try:
            rows = self.db.execute(text(sql), params).mappings().all()
            return [dict(r) for r in rows]
        except (ProgrammingError, OperationalError):
            return []

    @staticmethod
    def _validate_range(inicio: datetime, fim: datetime) -> None:
        if inicio > fim:
            raise ValueError("intervalo_invalido")

    def _assert_usina_exists(self, usina_id: str) -> None:
        if not self.get_usina(usina_id):
            raise ValueError("usina_nao_encontrada")

    def list_usinas(self, fonte: str | None = None, submercado: str | None = None):
        sql = """
        SELECT usina_id, nome, fonte, potencia_mw, submercado, latitude, longitude, garantia_fisica_mwm
        FROM gold.usinas
        WHERE (:fonte IS NULL OR fonte = :fonte)
          AND (:submercado IS NULL OR submercado = :submercado)
          AND (:ne_only = false OR submercado = 'NE')
        ORDER BY nome
        """
        rows = self.db.execute(
            text(sql),
            {
                "fonte": fonte,
                "submercado": submercado,
                "ne_only": self.mvp_only_nordeste,
            },
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_usina(self, usina_id: str):
        sql = """
        SELECT usina_id, nome, fonte, potencia_mw, submercado, latitude, longitude, garantia_fisica_mwm
        FROM gold.usinas
        WHERE usina_id = :usina_id
          AND (:ne_only = false OR submercado = 'NE')
        LIMIT 1
        """
        row = self.db.execute(text(sql), {"usina_id": usina_id, "ne_only": self.mvp_only_nordeste}).mappings().first()
        return dict(row) if row else None

    def get_constrained_off(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql = """
        SELECT
            usina_id,
            timestamp,
            fonte,
            geracao_verificada_mwh,
            geracao_referencia_mwh,
            energia_restringida_mwh,
            razao_restricao,
            submercado
        FROM gold.constrained_off
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
          AND (:ne_only = false OR submercado = 'NE')
        ORDER BY timestamp
        """
        rows = self.db.execute(
            text(sql),
            {"usina_id": usina_id, "inicio": inicio, "fim": fim, "ne_only": self.mvp_only_nordeste},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_pld(self, submercado: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        sql = """
        SELECT timestamp, submercado, pld_reais_mwh
        FROM gold.pld_horario
        WHERE submercado = :submercado
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        rows = self.db.execute(
            text(sql),
            {"submercado": submercado, "inicio": inicio, "fim": fim},
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_geracao_horaria(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql = """
        SELECT usina_id, timestamp, geracao_mwh, fator_capacidade
        FROM gold.geracao_horaria
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        rows = self.db.execute(text(sql), {"usina_id": usina_id, "inicio": inicio, "fim": fim}).mappings().all()
        return [dict(r) for r in rows]

    def get_clima_horario(self, usina_id: str, inicio: datetime, fim: datetime, is_forecast: bool | None = None):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql = """
        SELECT usina_id, timestamp, irradiancia_wm2, vento_ms, temperatura_c, is_forecast
        FROM gold.clima_horario
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
          AND (:is_forecast IS NULL OR is_forecast = :is_forecast)
        ORDER BY timestamp
        """
        rows = self.db.execute(
            text(sql),
            {
                "usina_id": usina_id,
                "inicio": inicio,
                "fim": fim,
                "is_forecast": is_forecast,
            },
        ).mappings().all()
        return [dict(r) for r in rows]

    def get_disponibilidade_usina(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql = """
        SELECT usina_id, timestamp, disponibilidade, teifa, teip
        FROM gold.disponibilidade_usina
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        return self._safe_mappings_query(sql, {"usina_id": usina_id, "inicio": inicio, "fim": fim})

    def get_despacho_dessem(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql = """
        SELECT usina_id, timestamp, geracao_programada_mwh
        FROM gold.despacho_dessem
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        return self._safe_mappings_query(sql, {"usina_id": usina_id, "inicio": inicio, "fim": fim})

    def get_garantia_fisica(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql = """
        SELECT usina_id, timestamp, garantia_fisica_mwh
        FROM gold.garantia_fisica_horaria
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        return self._safe_mappings_query(sql, {"usina_id": usina_id, "inicio": inicio, "fim": fim})

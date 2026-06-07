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
            self.db.rollback()
            return []

    @staticmethod
    def _validate_range(inicio: datetime, fim: datetime) -> None:
        if inicio > fim:
            raise ValueError("intervalo_invalido")

    def _assert_usina_exists(self, usina_id: str) -> None:
        if not self.get_usina(usina_id):
            raise ValueError("usina_nao_encontrada")

    def list_usinas(self, fonte: str | None = None, submercado: str | None = None):
        sql_gold = """
        SELECT usina_id, nome, fonte, potencia_mw, submercado, latitude, longitude, garantia_fisica_mwm
        FROM gold.usinas
        WHERE (:fonte IS NULL OR fonte = :fonte)
          AND (:submercado IS NULL OR submercado = :submercado)
          AND (:ne_only = false OR submercado = 'NE')
        ORDER BY nome
        """
        try:
            rows = self.db.execute(
                text(sql_gold),
                {
                    "fonte": fonte,
                    "submercado": submercado,
                    "ne_only": self.mvp_only_nordeste,
                },
            ).mappings().all()
            return [dict(r) for r in rows]
        except (ProgrammingError, OperationalError):
            self.db.rollback()
            sql_public_fc = """
            WITH cutoff AS (
                SELECT (MAX(din_instante) - INTERVAL '30 days') AS dt FROM public.fator_capacidade_2
            ), ranked AS (
                SELECT
                    id_ons AS usina_id,
                    nom_usina_conjunto AS nome,
                    COALESCE(nom_tipousina, 'desconhecida') AS fonte,
                    COALESCE(val_capacidadeinstalada, 0)::double precision AS potencia_mw,
                    CASE
                        WHEN UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') THEN 'NE'
                        WHEN UPPER(nom_subsistema) = 'NORDESTE' THEN 'NE'
                        WHEN UPPER(nom_subsistema) = 'NORTE' THEN 'N'
                        ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                    END AS submercado,
                    val_latitudesecoletora AS latitude,
                    val_longitudesecoletora AS longitude,
                    NULL::double precision AS garantia_fisica_mwm,
                    ROW_NUMBER() OVER (PARTITION BY id_ons ORDER BY din_instante DESC NULLS LAST) AS rn
                FROM public.fator_capacidade_2
                WHERE id_ons IS NOT NULL
                  AND din_instante >= (SELECT dt FROM cutoff)
            )
            SELECT usina_id, nome, fonte, potencia_mw, submercado, latitude, longitude, garantia_fisica_mwm
            FROM ranked
            WHERE rn = 1
              AND (:ne_only = false OR submercado = 'NE')
            ORDER BY nome
            """
            rows = self.db.execute(text(sql_public_fc), {"ne_only": self.mvp_only_nordeste}).mappings().all()
            data = [dict(r) for r in rows]
            if not data:
                sql_public_disp = """
                WITH cutoff AS (
                    SELECT (MAX(din_instante) - INTERVAL '30 days') AS dt FROM public.disponibilidade_usina
                ), ranked AS (
                    SELECT
                        id_ons AS usina_id,
                        nom_usina AS nome,
                        COALESCE(nom_tipocombustivel, 'desconhecida') AS fonte,
                        COALESCE(val_potenciainstalada, 0)::double precision AS potencia_mw,
                        CASE
                            WHEN UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') THEN 'NE'
                            WHEN UPPER(nom_subsistema) = 'NORDESTE' THEN 'NE'
                            WHEN UPPER(nom_subsistema) = 'NORTE' THEN 'N'
                            ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                        END AS submercado,
                        NULL::double precision AS latitude,
                        NULL::double precision AS longitude,
                        NULL::double precision AS garantia_fisica_mwm,
                        ROW_NUMBER() OVER (PARTITION BY id_ons ORDER BY din_instante DESC NULLS LAST) AS rn
                    FROM public.disponibilidade_usina
                    WHERE id_ons IS NOT NULL
                      AND din_instante >= (SELECT dt FROM cutoff)
                )
                SELECT usina_id, nome, fonte, potencia_mw, submercado, latitude, longitude, garantia_fisica_mwm
                FROM ranked
                WHERE rn = 1
                  AND (:ne_only = false OR submercado = 'NE')
                ORDER BY nome
                """
                rows = self.db.execute(text(sql_public_disp), {"ne_only": self.mvp_only_nordeste}).mappings().all()
                data = [dict(r) for r in rows]

            # Enriquecer coordenadas via fator_capacidade_2 quando fallback veio sem lat/lon.
            ids_sem_coord = [str(u.get("usina_id")) for u in data if u.get("latitude") is None or u.get("longitude") is None]
            if ids_sem_coord:
                try:
                    sql_coords = """
                    SELECT id_ons AS usina_id,
                           MAX(val_latitudesecoletora)::double precision AS latitude,
                           MAX(val_longitudesecoletora)::double precision AS longitude
                    FROM public.fator_capacidade_2
                    WHERE id_ons = ANY(:ids)
                    GROUP BY id_ons
                    """
                    rows_coords = self.db.execute(text(sql_coords), {"ids": ids_sem_coord}).mappings().all()
                    by_id = {str(r["usina_id"]): dict(r) for r in rows_coords}
                    for u in data:
                        uid = str(u.get("usina_id"))
                        if uid in by_id:
                            if u.get("latitude") is None:
                                u["latitude"] = by_id[uid].get("latitude")
                            if u.get("longitude") is None:
                                u["longitude"] = by_id[uid].get("longitude")
                except Exception:
                    self.db.rollback()

            if fonte:
                f = fonte.lower()
                data = [u for u in data if f in str(u.get("fonte", "")).lower()]
            if submercado:
                data = [u for u in data if str(u.get("submercado", "")).upper() == submercado.upper()]
            return data

    def get_usina(self, usina_id: str):
        sql_gold = """
        SELECT usina_id, nome, fonte, potencia_mw, submercado, latitude, longitude, garantia_fisica_mwm
        FROM gold.usinas
        WHERE usina_id = :usina_id
          AND (:ne_only = false OR submercado = 'NE')
        LIMIT 1
        """
        try:
            row = self.db.execute(text(sql_gold), {"usina_id": usina_id, "ne_only": self.mvp_only_nordeste}).mappings().first()
            return dict(row) if row else None
        except (ProgrammingError, OperationalError):
            self.db.rollback()
            sql_public = """
            SELECT
                id_ons AS usina_id,
                nom_usina AS nome,
                COALESCE(nom_tipocombustivel, 'desconhecida') AS fonte,
                COALESCE(val_potenciainstalada, 0) AS potencia_mw,
                CASE
                    WHEN UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') THEN 'NE'
                    WHEN UPPER(nom_subsistema) = 'NORDESTE' THEN 'NE'
                    WHEN UPPER(nom_subsistema) = 'NORTE' THEN 'N'
                    ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                END AS submercado,
                NULL::double precision AS latitude,
                NULL::double precision AS longitude,
                NULL::double precision AS garantia_fisica_mwm
            FROM public.disponibilidade_usina
            WHERE id_ons = :usina_id
              AND (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR UPPER(nom_subsistema) = 'NORDESTE')
            ORDER BY din_instante DESC
            LIMIT 1
            """
            row = self.db.execute(text(sql_public), {"usina_id": usina_id, "ne_only": self.mvp_only_nordeste}).mappings().first()
            if row:
                return dict(row)

            sql_public_fc = """
            SELECT
                id_ons AS usina_id,
                nom_usina_conjunto AS nome,
                COALESCE(nom_tipousina, 'desconhecida') AS fonte,
                COALESCE(val_capacidadeinstalada, 0) AS potencia_mw,
                CASE
                    WHEN UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') THEN 'NE'
                    WHEN UPPER(nom_subsistema) = 'NORDESTE' THEN 'NE'
                    WHEN UPPER(nom_subsistema) = 'NORTE' THEN 'N'
                    ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                END AS submercado,
                val_latitudesecoletora AS latitude,
                val_longitudesecoletora AS longitude,
                NULL::double precision AS garantia_fisica_mwm
            FROM public.fator_capacidade_2
            WHERE id_ons = :usina_id
              AND (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR UPPER(nom_subsistema) = 'NORDESTE')
            ORDER BY din_instante DESC
            LIMIT 1
            """
            row_fc = self.db.execute(text(sql_public_fc), {"usina_id": usina_id, "ne_only": self.mvp_only_nordeste}).mappings().first()
            if row_fc:
                return dict(row_fc)

            sql_public_ger = """
            SELECT
                id_ons AS usina_id,
                nom_usina AS nome,
                COALESCE(nom_tipocombustivel, nom_tipousina, 'desconhecida') AS fonte,
                0::double precision AS potencia_mw,
                CASE
                    WHEN UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') THEN 'NE'
                    WHEN UPPER(nom_subsistema) = 'NORDESTE' THEN 'NE'
                    WHEN UPPER(nom_subsistema) = 'NORTE' THEN 'N'
                    ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                END AS submercado,
                NULL::double precision AS latitude,
                NULL::double precision AS longitude,
                NULL::double precision AS garantia_fisica_mwm
            FROM public.geracao_usina_2
            WHERE id_ons = :usina_id
              AND (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR UPPER(nom_subsistema) = 'NORDESTE')
            ORDER BY din_instante DESC
            LIMIT 1
            """
            row_ger = self.db.execute(text(sql_public_ger), {"usina_id": usina_id, "ne_only": self.mvp_only_nordeste}).mappings().first()
            return dict(row_ger) if row_ger else None

    def get_constrained_off(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql_gold = """
        SELECT
            usina_id,
            timestamp,
            fonte,
            geracao_verificada_mwh,
            geracao_referencia_mwh,
            energia_restringida_mwh,
            razao_restricao,
            NULL::text AS cod_razaorestricao,
            NULL::text AS origem_restricao,
            submercado
        FROM gold.constrained_off
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
          AND (:ne_only = false OR submercado = 'NE')
        ORDER BY timestamp
        """
        try:
            rows = self.db.execute(
                text(sql_gold),
                {"usina_id": usina_id, "inicio": inicio, "fim": fim, "ne_only": self.mvp_only_nordeste},
            ).mappings().all()
            return [dict(r) for r in rows]
        except (ProgrammingError, OperationalError):
            self.db.rollback()

            # Fallback preferencial: tabelas COFF com código de razão explícito (CNF/ENE/REL)
            sql_public_coff = """
            WITH base AS (
                SELECT
                    id_ons AS usina_id,
                    CASE
                        WHEN pg_typeof(din_instante)::text LIKE 'timestamp%' THEN din_instante::timestamp
                        ELSE to_timestamp(din_instante, 'YYYY-MM-DD HH24:MI:SS')
                    END AS timestamp,
                    nom_usina AS fonte,
                    NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision AS geracao_verificada_mwh,
                    COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0) AS geracao_referencia_mwh,
                    COALESCE(
                        NULLIF(REPLACE(val_geracaolimitada::text, ',', '.'), '')::double precision,
                        GREATEST(
                            COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0)
                            - COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0),
                            0
                        )
                    ) AS energia_restringida_mwh,
                    cod_razaorestricao AS cod_razaorestricao,
                    cod_origemrestricao AS origem_restricao,
                    NULL::text AS razao_restricao,
                    CASE
                        WHEN UPPER(COALESCE(id_subsistema, nom_subsistema, '')) IN ('NE', 'NORDESTE') THEN 'NE'
                        WHEN UPPER(COALESCE(id_subsistema, nom_subsistema, '')) IN ('N', 'NORTE') THEN 'N'
                        ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                    END AS submercado
                FROM public.restricao_coff_eolica_usi
                WHERE id_ons = :usina_id

                UNION ALL

                SELECT
                    id_ons AS usina_id,
                    din_instante::timestamp AS timestamp,
                    nom_usina AS fonte,
                    COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0) AS geracao_verificada_mwh,
                    COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0) AS geracao_referencia_mwh,
                    COALESCE(
                        NULLIF(REPLACE(val_geracaolimitada::text, ',', '.'), '')::double precision,
                        GREATEST(
                            COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0)
                            - COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0),
                            0
                        )
                    ) AS energia_restringida_mwh,
                    cod_razaorestricao AS cod_razaorestricao,
                    cod_origemrestricao AS origem_restricao,
                    NULL::text AS razao_restricao,
                    CASE
                        WHEN UPPER(COALESCE(id_subsistema, nom_subsistema, '')) IN ('NE', 'NORDESTE') THEN 'NE'
                        WHEN UPPER(COALESCE(id_subsistema, nom_subsistema, '')) IN ('N', 'NORTE') THEN 'N'
                        ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                    END AS submercado
                FROM public.restricao_coff_fotovoltaica
                WHERE id_ons = :usina_id
            )
            SELECT usina_id, timestamp, fonte, geracao_verificada_mwh, geracao_referencia_mwh,
                   energia_restringida_mwh, razao_restricao, cod_razaorestricao, origem_restricao, submercado
            FROM base
            WHERE timestamp BETWEEN :inicio AND :fim
              AND cod_razaorestricao IS NOT NULL
              AND energia_restringida_mwh > 0
              AND (:ne_only = false OR submercado = 'NE')
            ORDER BY timestamp
            """
            rows_coff = self._safe_mappings_query(
                sql_public_coff,
                {"usina_id": usina_id, "inicio": inicio, "fim": fim, "ne_only": self.mvp_only_nordeste},
            )
            if rows_coff:
                return rows_coff

            sql_public = """
            SELECT
                id_ons AS usina_id,
                din_instante AS timestamp,
                nom_tipousina AS fonte,
                val_geracaoverificada AS geracao_verificada_mwh,
                val_geracaoprogramada AS geracao_referencia_mwh,
                GREATEST(COALESCE(val_geracaoprogramada,0) - COALESCE(val_geracaoverificada,0), 0) AS energia_restringida_mwh,
                NULL::text AS razao_restricao,
                NULL::text AS cod_razaorestricao,
                CASE
                    WHEN UPPER(nom_subsistema) = 'NORDESTE' THEN 'NE'
                    WHEN UPPER(nom_subsistema) = 'NORTE' THEN 'N'
                    ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                END AS submercado
            FROM public.fator_capacidade_2
            WHERE id_ons = :usina_id
              AND din_instante BETWEEN :inicio AND :fim
              AND (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR UPPER(nom_subsistema) = 'NORDESTE')
              AND COALESCE(val_geracaoprogramada,0) > COALESCE(val_geracaoverificada,0)
            ORDER BY din_instante
            """
            rows = self.db.execute(
                text(sql_public),
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
        rows = self._safe_mappings_query(
            sql,
            {"submercado": submercado, "inicio": inicio, "fim": fim},
        )
        if rows:
            return rows

        submercado_norm = (submercado or "").upper()
        submercado_public = {
            "NE": "NORDESTE",
            "N": "NORTE",
            "SE": "SUDESTE",
            "S": "SUL",
        }.get(submercado_norm, submercado_norm)

        sql_public = """
        WITH pld_norm AS (
            SELECT
                to_timestamp(mes_referencia || LPAD(dia, 2, '0') || LPAD(hora, 2, '0'), 'YYYYMMDDHH24') AS timestamp,
                UPPER(submercado) AS submercado,
                NULLIF(REPLACE(pld_hora, ',', '.'), '')::double precision AS pld_reais_mwh
            FROM public.ccee_pld_horario
            WHERE UPPER(submercado) = :submercado_public
        )
        SELECT timestamp, submercado, pld_reais_mwh
        FROM pld_norm
        WHERE timestamp BETWEEN :inicio AND :fim
          AND pld_reais_mwh IS NOT NULL
        ORDER BY timestamp
        """
        return self._safe_mappings_query(
            sql_public,
            {"submercado_public": submercado_public, "inicio": inicio, "fim": fim},
        )

    def get_geracao_horaria(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql_gold = """
        SELECT usina_id, timestamp, geracao_mwh, fator_capacidade
        FROM gold.geracao_horaria
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        try:
            rows = self.db.execute(text(sql_gold), {"usina_id": usina_id, "inicio": inicio, "fim": fim}).mappings().all()
            return [dict(r) for r in rows]
        except (ProgrammingError, OperationalError):
            self.db.rollback()
            sql_public_ger = """
            SELECT
                id_ons AS usina_id,
                din_instante AS timestamp,
                val_geracao AS geracao_mwh,
                0::double precision AS fator_capacidade
            FROM public.geracao_usina_2
            WHERE id_ons = :usina_id
              AND din_instante BETWEEN :inicio AND :fim
              AND (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR UPPER(nom_subsistema) = 'NORDESTE')
            ORDER BY din_instante
            """
            rows_ger = self.db.execute(
                text(sql_public_ger),
                {"usina_id": usina_id, "inicio": inicio, "fim": fim, "ne_only": self.mvp_only_nordeste},
            ).mappings().all()
            if rows_ger:
                return [dict(r) for r in rows_ger]

            sql_public_fc = """
            SELECT
                id_ons AS usina_id,
                din_instante AS timestamp,
                val_geracaoverificada AS geracao_mwh,
                COALESCE(val_fatorcapacidade, 0) AS fator_capacidade
            FROM public.fator_capacidade_2
            WHERE id_ons = :usina_id
              AND din_instante BETWEEN :inicio AND :fim
              AND (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR UPPER(nom_subsistema) = 'NORDESTE')
            ORDER BY din_instante
            """
            rows = self.db.execute(
                text(sql_public_fc),
                {"usina_id": usina_id, "inicio": inicio, "fim": fim, "ne_only": self.mvp_only_nordeste},
            ).mappings().all()
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
        return self._safe_mappings_query(
            sql,
            {
                "usina_id": usina_id,
                "inicio": inicio,
                "fim": fim,
                "is_forecast": is_forecast,
            },
        )

    def get_disponibilidade_usina(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql_gold = """
        SELECT usina_id, timestamp, disponibilidade, teifa, teip
        FROM gold.disponibilidade_usina
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        rows = self._safe_mappings_query(sql_gold, {"usina_id": usina_id, "inicio": inicio, "fim": fim})
        if rows:
            return rows

        sql_public = """
        SELECT
            id_ons AS usina_id,
            din_instante AS timestamp,
            COALESCE(val_dispoperacional, 0) AS disponibilidade,
            0::double precision AS teifa,
            0::double precision AS teip
        FROM public.disponibilidade_usina
        WHERE id_ons = :usina_id
          AND din_instante BETWEEN :inicio AND :fim
          AND (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR UPPER(nom_subsistema) = 'NORDESTE')
        ORDER BY din_instante
        """
        return self._safe_mappings_query(
            sql_public,
            {"usina_id": usina_id, "inicio": inicio, "fim": fim, "ne_only": self.mvp_only_nordeste},
        )

    def get_despacho_dessem(self, usina_id: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)
        sql_gold = """
        SELECT usina_id, timestamp, geracao_programada_mwh
        FROM gold.despacho_dessem
        WHERE usina_id = :usina_id
          AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        rows = self._safe_mappings_query(sql_gold, {"usina_id": usina_id, "inicio": inicio, "fim": fim})
        if rows:
            return rows

        sql_public = """
        SELECT
            id_ons AS usina_id,
            din_instante AS timestamp,
            COALESCE(val_geracaoprogramada, 0) AS geracao_programada_mwh
        FROM public.fator_capacidade_2
        WHERE id_ons = :usina_id
          AND din_instante BETWEEN :inicio AND :fim
          AND (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR UPPER(nom_subsistema) = 'NORDESTE')
        ORDER BY din_instante
        """
        return self._safe_mappings_query(
            sql_public,
            {"usina_id": usina_id, "inicio": inicio, "fim": fim, "ne_only": self.mvp_only_nordeste},
        )

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

    def get_perda_resumida(self, usina_id: str, submercado: str, inicio: datetime, fim: datetime):
        self._validate_range(inicio, fim)
        self._assert_usina_exists(usina_id)

        submercado_norm = (submercado or "").upper()
        submercado_public = {
            "NE": "NORDESTE",
            "N": "NORTE",
            "SE": "SUDESTE",
            "S": "SUL",
        }.get(submercado_norm, submercado_norm)

        sql = """
        WITH co AS (
            SELECT
                b.timestamp,
                b.energia_restringida_mwh,
                CASE
                    WHEN b.cod_razaorestricao ILIKE 'CF%' OR b.cod_razaorestricao ILIKE 'CNF%' OR b.cod_razaorestricao ILIKE 'CONFIAB%' THEN 'confiabilidade'
                    WHEN b.cod_razaorestricao ILIKE 'IE%' OR b.cod_razaorestricao ILIKE 'REL%' OR b.cod_razaorestricao ILIKE 'INDISP_EXT%' THEN 'indisponibilidade_externa'
                    WHEN b.cod_razaorestricao ILIKE 'EN%' OR b.cod_razaorestricao ILIKE 'ENE%' OR b.cod_razaorestricao ILIKE 'ENER%' THEN 'energetico'
                    WHEN b.cod_razaorestricao ILIKE 'RE%' OR b.cod_razaorestricao ILIKE 'ELE%' THEN 'restricao_eletrica'
                    WHEN b.cod_razaorestricao ILIKE 'SE%' OR b.cod_razaorestricao ILIKE 'SEG%' THEN 'seguranca_eletroenergetica'
                    ELSE 'indefinido'
                END AS razao_norm
            FROM (
                SELECT
                    CASE
                        WHEN pg_typeof(din_instante)::text LIKE 'timestamp%' THEN din_instante::timestamp
                        ELSE to_timestamp(din_instante, 'YYYY-MM-DD HH24:MI:SS')
                    END AS timestamp,
                    GREATEST(
                        COALESCE(NULLIF(val_geracaoreferenciafinal, '')::double precision, NULLIF(val_geracaoreferencia, '')::double precision, 0)
                        - COALESCE(NULLIF(val_geracao, '')::double precision, 0),
                        0
                    ) AS energia_restringida_mwh,
                    cod_razaorestricao,
                    CASE
                        WHEN UPPER(COALESCE(id_subsistema, nom_subsistema, '')) IN ('NE', 'NORDESTE') THEN 'NE'
                        WHEN UPPER(COALESCE(id_subsistema, nom_subsistema, '')) IN ('N', 'NORTE') THEN 'N'
                        ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                    END AS submercado
                FROM public.restricao_coff_eolica_usi
                WHERE id_ons = :usina_id

                UNION ALL

                SELECT
                    din_instante::timestamp AS timestamp,
                    GREATEST(
                        COALESCE(val_geracaoreferenciafinal, val_geracaoreferencia, 0)::double precision
                        - COALESCE(val_geracao, 0)::double precision,
                        0
                    ) AS energia_restringida_mwh,
                    cod_razaorestricao,
                    CASE
                        WHEN UPPER(COALESCE(id_subsistema, nom_subsistema, '')) IN ('NE', 'NORDESTE') THEN 'NE'
                        WHEN UPPER(COALESCE(id_subsistema, nom_subsistema, '')) IN ('N', 'NORTE') THEN 'N'
                        ELSE UPPER(COALESCE(id_subsistema, nom_subsistema, ''))
                    END AS submercado
                FROM public.restricao_coff_fotovoltaica
                WHERE id_ons = :usina_id
            ) b
            WHERE b.timestamp BETWEEN :inicio AND :fim
              AND b.energia_restringida_mwh > 0
              AND (:ne_only = false OR b.submercado = 'NE')
        ),
        pld AS (
            SELECT
                to_timestamp(mes_referencia || LPAD(dia, 2, '0') || LPAD(hora, 2, '0'), 'YYYYMMDDHH24') AS timestamp,
                NULLIF(REPLACE(pld_hora, ',', '.'), '')::double precision AS pld_reais_mwh
            FROM public.ccee_pld_horario
            WHERE UPPER(submercado) = :submercado_public
        )
        SELECT
            co.razao_norm AS razao,
            COUNT(*)::bigint AS total_eventos,
            SUM(co.energia_restringida_mwh)::double precision AS total_energia_mwh,
            SUM(co.energia_restringida_mwh * COALESCE(pld.pld_reais_mwh, 0))::double precision AS total_perda_reais,
            SUM(CASE WHEN pld.pld_reais_mwh IS NULL THEN 1 ELSE 0 END)::bigint AS pld_faltante_eventos
        FROM co
        LEFT JOIN pld ON date_trunc('hour', co.timestamp) = date_trunc('hour', pld.timestamp)
        GROUP BY co.razao_norm
        """

        rows = self._safe_mappings_query(
            sql,
            {
                "usina_id": usina_id,
                "inicio": inicio,
                "fim": fim,
                "submercado_public": submercado_public,
                "ne_only": self.mvp_only_nordeste,
            },
        )
        if not rows:
            return None

        total_eventos = int(sum(int(r.get("total_eventos") or 0) for r in rows))
        total_energia = float(sum(float(r.get("total_energia_mwh") or 0.0) for r in rows))
        total_perda = float(sum(float(r.get("total_perda_reais") or 0.0) for r in rows))
        pld_faltante = int(sum(int(r.get("pld_faltante_eventos") or 0) for r in rows))
        por_razao = {str(r.get("razao") or "indefinido"): round(float(r.get("total_perda_reais") or 0.0), 2) for r in rows}

        return {
            "total_eventos": total_eventos,
            "total_energia_restringida_mwh": round(total_energia, 4),
            "total_perda_reais": round(total_perda, 2),
            "por_razao": por_razao,
            "pld_faltante_eventos": pld_faltante,
        }

    def obter_franquia(self, ano: int, fonte: str | None):
        fonte_norm = (fonte or "").lower()
        if "eol" in fonte_norm:
            fonte_norm = "eolica"
        elif "solar" in fonte_norm or "fotov" in fonte_norm:
            fonte_norm = "solar"
        sql = """
        SELECT ano, fonte, franquia_horas, fonte_normativa, observacao
        FROM gold.franquia_anual
        WHERE ano = :ano AND fonte = :fonte
        LIMIT 1
        """
        rows = self._safe_mappings_query(sql, {"ano": int(ano), "fonte": fonte_norm})
        return rows[0] if rows else None

    def obter_contratos_vigentes(self, usina_id: str, data):
        sql = """
        SELECT usina_id, tipo_contrato, volume_mwm, preco_reais_mwh, vigencia_inicio, vigencia_fim
        FROM gold.contratos_usina
        WHERE usina_id = :usina_id
          AND vigencia_inicio <= :data
          AND (vigencia_fim IS NULL OR vigencia_fim >= :data)
        ORDER BY vigencia_inicio DESC
        """
        return self._safe_mappings_query(sql, {"usina_id": usina_id, "data": data})

    def get_dados_proprios_climatologia(self, usina_id: str, inicio: datetime, fim: datetime):
        sql = """
        SELECT usina_id, timestamp, vento_ms_proprio, irradiancia_wm2_proprio,
               disponibilidade_eletromecanica, fonte_dado
        FROM gold.dados_proprios_climatologia
        WHERE usina_id = :usina_id AND timestamp BETWEEN :inicio AND :fim
        ORDER BY timestamp
        """
        return self._safe_mappings_query(sql, {"usina_id": usina_id, "inicio": inicio, "fim": fim})

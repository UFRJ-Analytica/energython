from __future__ import annotations

import time as _time
from datetime import datetime
import re
import unicodedata

from sqlalchemy import text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.domain.top_plants import filter_top_50_usinas, is_top_50_usina, list_top_50_usinas
from app.repositories.base import BaseRepository

# ---------------------------------------------------------------------------
# Caches compartilhados (nível de módulo) para a camada de GRANULARIDADE ÚNICA.
# Os marts dw.mart_eolica/dw.mart_solar somam ~12M linhas e dim_usina ~25k.
# Sem cache, cada request DEBUG reagrega tudo (~10s). Como o repositório é
# instanciado por request (Depends), o cache precisa viver no módulo.
# ---------------------------------------------------------------------------
_MART_AGG_CACHE: dict = {}       # chave: ne_only -> (ts, rows)
_MART_AGG_TTL = 600              # segundos
_COORDS_SHARED_CACHE: dict = {"data": None}


class PostgresRepository(BaseRepository):
    _dw_usinas_cache_by_scope: dict[bool, list[dict]] = {}

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

    @staticmethod
    def _slugify(value: str) -> str:
        text = unicodedata.normalize("NFKD", str(value or ""))
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        text = re.sub(r"[^a-zA-Z0-9]+", "-", text.lower()).strip("-")
        return text or "sem-nome"

    @classmethod
    def _dw_fonte_key(cls, fonte: str | None) -> str:
        value_raw = str(fonte or "").strip().upper()
        value = unicodedata.normalize("NFKD", value_raw)
        value = "".join(ch for ch in value if not unicodedata.combining(ch))
        if "FOTOV" in value or "SOLAR" in value:
            return "solar"
        if "EOL" in value:
            return "eolica"
        return cls._slugify(value)

    @classmethod
    def _dw_usina_id(cls, fonte: str | None, id_estado: str | None, nom_usina: str, id_ons: str | None = None) -> str:
        # Para a solução por usina individual, o id estável deve ser o código ONS
        # do equipamento quando disponível. Nome/UF ficam apenas como fallback.
        if id_ons:
            return f"dw_{cls._dw_fonte_key(fonte)}_{cls._slugify(str(id_ons))}"
        return f"dw_{cls._dw_fonte_key(fonte)}_{str(id_estado or 'xx').lower()}_{cls._slugify(nom_usina)}"

    @staticmethod
    def _dw_table_for_fonte_key(fonte_key: str) -> str | None:
        return {"solar": "dw.mart_restricao_solar", "eolica": "dw.mart_restricao_eolica"}.get(fonte_key)

    @staticmethod
    def _dw_conjunto_table_for_fonte_key(fonte_key: str) -> str | None:
        return {"solar": "dw.mart_solar", "eolica": "dw.mart_eolica"}.get(fonte_key)

    @staticmethod
    def _submercado_expr(alias: str = "m") -> str:
        return f"""
        CASE
            WHEN UPPER(COALESCE({alias}.id_subsistema, {alias}.nom_subsistema, '')) IN ('NE', 'NORDESTE') THEN 'NE'
            WHEN UPPER(COALESCE({alias}.id_subsistema, {alias}.nom_subsistema, '')) IN ('N', 'NORTE') THEN 'N'
            WHEN UPPER(COALESCE({alias}.id_subsistema, {alias}.nom_subsistema, '')) IN ('SE', 'SUDESTE') THEN 'SE'
            WHEN UPPER(COALESCE({alias}.id_subsistema, {alias}.nom_subsistema, '')) IN ('S', 'SUL') THEN 'S'
            ELSE UPPER(COALESCE({alias}.id_subsistema, {alias}.nom_subsistema, ''))
        END
        """

    def _list_dw_usinas_raw(self) -> list[dict]:
        cached = self._dw_usinas_cache_by_scope.get(self.mvp_only_nordeste)
        if cached is not None:
            return list(cached)

        sql = f"""
        WITH limites AS (
            SELECT MAX(din_instante) AS max_dt
            FROM (
                SELECT MAX(din_instante) AS din_instante FROM dw.mart_restricao_solar_2026
                UNION ALL
                SELECT MAX(din_instante) AS din_instante FROM dw.mart_restricao_eolica_2026
            ) t
        ), eventos AS (
            SELECT 'dw.mart_restricao_solar'::text AS mart_table, nom_usina, id_ons, ceg, fonte,
                   id_estado, nom_estado, id_subsistema, nom_subsistema,
                   nom_conjuntousina, nom_usina_conjunto, potencia_mw, potencia_mw_conjunto,
                   din_instante, COALESCE(corte_mwh, 0)::double precision AS corte_mwh
            FROM dw.mart_restricao_solar_2026, limites
            WHERE COALESCE(corte_mwh, 0) > 0
              AND din_instante >= limites.max_dt - interval '2 months'
              AND din_instante <= limites.max_dt
            UNION ALL
            SELECT 'dw.mart_restricao_eolica'::text AS mart_table, nom_usina, id_ons, ceg, fonte,
                   id_estado, nom_estado, id_subsistema, nom_subsistema,
                   nom_conjuntousina, nom_usina_conjunto, potencia_mw, potencia_mw_conjunto,
                   din_instante, COALESCE(corte_mwh, 0)::double precision AS corte_mwh
            FROM dw.mart_restricao_eolica_2026, limites
            WHERE COALESCE(corte_mwh, 0) > 0
              AND din_instante >= limites.max_dt - interval '2 months'
              AND din_instante <= limites.max_dt
        ), pld AS (
            SELECT
                to_timestamp(mes_referencia || LPAD(dia, 2, '0') || LPAD(hora, 2, '0'), 'YYYYMMDDHH24') AS timestamp,
                NULLIF(REPLACE(pld_hora, ',', '.'), '')::double precision AS pld_reais_mwh
            FROM public.ccee_pld_horario
            WHERE UPPER(submercado) = 'NORDESTE'
        ), mart AS (
            SELECT e.mart_table, e.nom_usina, e.id_ons, e.ceg, e.fonte,
                   e.id_estado, e.nom_estado, e.id_subsistema, e.nom_subsistema,
                   e.nom_conjuntousina, e.nom_usina_conjunto,
                   MAX(e.potencia_mw) AS potencia_mw,
                   MAX(e.potencia_mw_conjunto) AS potencia_mw_conjunto,
                   MIN(e.din_instante) AS data_inicio,
                   MAX(e.din_instante) AS data_fim,
                   SUM(e.corte_mwh)::double precision AS total_corte_mwh,
                   SUM(e.corte_mwh * COALESCE(pld.pld_reais_mwh, 0))::double precision AS total_perda_reais,
                   SUM(CASE WHEN pld.pld_reais_mwh IS NULL THEN 1 ELSE 0 END)::bigint AS pld_faltante_intervalos,
                   COUNT(*)::bigint AS total_intervalos_restricao
            FROM eventos e
            LEFT JOIN pld ON date_trunc('hour', e.din_instante) = date_trunc('hour', pld.timestamp)
            GROUP BY e.mart_table, e.nom_usina, e.id_ons, e.ceg, e.fonte, e.id_estado, e.nom_estado,
                     e.id_subsistema, e.nom_subsistema, e.nom_conjuntousina, e.nom_usina_conjunto
        ), ranked AS (
            SELECT mart.*,
                   REGEXP_REPLACE(ceg, '\\.\\d+$', '') AS ceg_core,
                   {self._submercado_expr('mart')} AS submercado,
                   CASE
                       WHEN UPPER(COALESCE(fonte, '')) LIKE '%FOTOV%' OR UPPER(COALESCE(fonte, '')) LIKE '%SOLAR%' THEN 'solar'
                       WHEN UPPER(COALESCE(fonte, '')) LIKE '%EOL%' THEN 'eolica'
                       ELSE 'outra'
                   END AS fonte_key
            FROM mart
            WHERE (:ne_only = false OR UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') OR {self._submercado_expr('mart')} = 'NE')
              AND COALESCE(total_perda_reais, 0) > 0
        ), selected AS (
            SELECT ranked.*,
                   ROW_NUMBER() OVER (ORDER BY total_perda_reais DESC NULLS LAST, total_corte_mwh DESC NULLS LAST) AS rank_overall,
                   ROW_NUMBER() OVER (PARTITION BY fonte_key ORDER BY total_perda_reais DESC NULLS LAST, total_corte_mwh DESC NULLS LAST) AS rank_fonte
            FROM ranked
        )
        SELECT r.mart_table, r.nom_usina, r.id_ons, r.ceg, r.fonte, r.id_estado, r.nom_estado,
               r.id_subsistema, r.nom_subsistema, r.nom_conjuntousina, r.nom_usina_conjunto,
               COALESCE(r.potencia_mw, p.potencia_mw, r.potencia_mw_conjunto) AS potencia_mw, r.data_inicio, r.data_fim, r.total_corte_mwh,
               r.total_perda_reais, r.total_intervalos_restricao, r.submercado,
               u.lat AS latitude, u.lon AS longitude
        FROM selected r
        LEFT JOIN dw.dim_usina u ON u.ceg_core = r.ceg_core
        LEFT JOIN dw.dim_usina_potencia p
          ON p.nom_usina = r.nom_usina
         AND p.id_estado = r.id_estado
        WHERE r.rank_overall <= 45
           OR (r.fonte_key = 'solar' AND r.rank_fonte <= 10 AND COALESCE(r.total_perda_reais, 0) >= 1000)
        ORDER BY r.total_perda_reais DESC NULLS LAST, r.total_corte_mwh DESC NULLS LAST, r.fonte, r.id_estado, r.nom_usina
        LIMIT 50
        """
        rows = self._safe_mappings_query(sql, {"ne_only": self.mvp_only_nordeste})
        if rows:
            self._dw_usinas_cache_by_scope[self.mvp_only_nordeste] = list(rows)
        return rows

    def _format_dw_usina(self, row: dict) -> dict:
        fonte_key = self._dw_fonte_key(row.get("fonte"))
        fonte_label = "solar" if fonte_key == "solar" else ("eolica" if fonte_key == "eolica" else str(row.get("fonte") or "desconhecida").lower())
        usina_id = self._dw_usina_id(row.get("fonte"), row.get("id_estado"), str(row.get("nom_usina") or ""), row.get("id_ons"))
        return {
            "usina_id": usina_id,
            "nome": str(row.get("nom_usina") or ""),
            "fonte": fonte_label,
            "potencia_mw": float(row.get("potencia_mw") or 0.0),
            "submercado": str(row.get("submercado") or ""),
            "latitude": float(row["latitude"]) if row.get("latitude") is not None else None,
            "longitude": float(row["longitude"]) if row.get("longitude") is not None else None,
            "garantia_fisica_mwm": None,
            "mart_table": row.get("mart_table"),
            "mart_nom_usina": row.get("nom_usina"),
            "id_ons": row.get("id_ons"),
            "ceg": row.get("ceg"),
            "nom_conjuntousina": row.get("nom_conjuntousina"),
            "nom_usina_conjunto": row.get("nom_usina_conjunto"),
            "id_estado": row.get("id_estado"),
            "nom_estado": row.get("nom_estado"),
            "id_subsistema": row.get("id_subsistema"),
            "nom_subsistema": row.get("nom_subsistema"),
            "data_inicio": row.get("data_inicio").isoformat() if hasattr(row.get("data_inicio"), "isoformat") else row.get("data_inicio"),
            "data_fim": row.get("data_fim").isoformat() if hasattr(row.get("data_fim"), "isoformat") else row.get("data_fim"),
            "total_corte_mwh": round(float(row.get("total_corte_mwh") or 0.0), 3),
            "total_perda_reais": round(float(row.get("total_perda_reais") or 0.0), 2),
            "total_intervalos_restricao": int(row.get("total_intervalos_restricao") or 0),
            "nivel_granularidade": "usina_individual_mart_restricao_dw",
        }

    def _resolve_dw_usina(self, usina_id: str) -> dict | None:
        raw = str(usina_id or "")
        if not raw.startswith("dw_"):
            return None
        for row in self._list_dw_usinas_raw():
            formatted = self._format_dw_usina(row)
            if formatted["usina_id"] == raw:
                return formatted
        return None

    def _assert_usina_exists(self, usina_id: str) -> None:
        if not self.get_usina(usina_id):
            raise ValueError("usina_nao_encontrada")

    def list_usinas(self, fonte: str | None = None, submercado: str | None = None):
        rows_dw = self._list_dw_usinas_raw()
        if rows_dw:
            data = [self._format_dw_usina(r) for r in rows_dw]
            if fonte:
                f = self._dw_fonte_key(fonte)
                data = [u for u in data if self._dw_fonte_key(str(u.get("fonte", ""))) == f]
            if submercado:
                data = [u for u in data if str(u.get("submercado", "")).upper() == submercado.upper()]
            return data

        data = list_top_50_usinas()
        if self.mvp_only_nordeste:
            data = [u for u in data if str(u.get("submercado", "")).upper() == "NE"]
        if fonte:
            f = self._dw_fonte_key(fonte)
            data = [u for u in data if self._dw_fonte_key(str(u.get("fonte", ""))) == f]
        if submercado:
            data = [u for u in data if str(u.get("submercado", "")).upper() == submercado.upper()]
        return filter_top_50_usinas(data)

    def get_usina(self, usina_id: str):
        dw_usina = self._resolve_dw_usina(usina_id)
        if dw_usina:
            return dw_usina

        if not is_top_50_usina(usina_id):
            return None

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
        dw_usina = self._resolve_dw_usina(usina_id)
        if dw_usina:
            fonte_key = self._dw_fonte_key(dw_usina.get("fonte"))
            table = self._dw_table_for_fonte_key(fonte_key)
            conjunto_table = self._dw_conjunto_table_for_fonte_key(fonte_key)
            if table and conjunto_table:
                sql_dw = f"""
                SELECT
                    :usina_id AS usina_id,
                    m.din_instante AS timestamp,
                    m.fonte AS fonte,
                    COALESCE(m.val_geracaoverificada, 0)::double precision * 0.5 AS geracao_verificada_mwh,
                    COALESCE(m.val_geracaoestimada, m.val_geracaoreferenciafinal_conjunto, m.val_geracaoreferencia_conjunto, 0)::double precision * 0.5 AS geracao_referencia_mwh,
                    COALESCE(m.corte_mwh, GREATEST(COALESCE(m.val_geracaoreferenciafinal_conjunto, m.val_geracaoreferencia_conjunto, 0)::double precision - COALESCE(m.val_geracaoverificada, 0)::double precision, 0) * 0.5)::double precision AS energia_restringida_mwh,
                    (m.val_geracaoreferenciafinal_conjunto IS NOT NULL OR m.corte_mwh IS NOT NULL) AS referencia_oficial,
                    'mart_restricao_por_usina_com_razao_do_conjunto'::text AS referencia_calculo_curtailment,
                    m.val_corte_mwmed::double precision AS geracao_limitada_mwmed,
                    NULL::text AS razao_restricao,
                    COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) AS cod_razaorestricao,
                    COALESCE(m.cod_origemrestricao, cj.cod_origemrestricao) AS cod_origemrestricao,
                    COALESCE(m.cod_origemrestricao, cj.cod_origemrestricao) AS origem_restricao,
                    {self._submercado_expr('m')} AS submercado
                FROM {table} m
                LEFT JOIN {conjunto_table} cj
                  ON cj.din_instante = m.din_instante
                 AND cj.nom_usina = m.nom_usina_conjunto
                WHERE m.id_ons = :id_ons
                  AND m.din_instante BETWEEN :inicio AND :fim
                  AND (CAST(:ceg AS text) IS NULL OR m.ceg = CAST(:ceg AS text))
                  AND (:ne_only = false OR {self._submercado_expr('m')} = 'NE' OR UPPER(COALESCE(m.id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA'))
                  AND COALESCE(m.corte_mwh, 0) > 0
                ORDER BY m.din_instante
                """
                rows_dw = self._safe_mappings_query(
                    sql_dw,
                    {
                        "usina_id": usina_id,
                        "id_ons": dw_usina.get("id_ons"),
                        "ceg": dw_usina.get("ceg"),
                        "inicio": inicio,
                        "fim": fim,
                        "ne_only": self.mvp_only_nordeste,
                    },
                )
                return rows_dw

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

            # Fallback preferencial — BANCO ATUALIZADO (hacka-energinn / camada silver):
            # a base nova traz a COFF eólica em `public.restricao_coff_eolica_detail`
            # (granularidade 30min). As antigas `restricao_coff_eolica_usi` e
            # `restricao_coff_fotovoltaica` não existem mais. Esta tabela não possui
            # `cod_razaorestricao`; usamos a sentinela 'COFF' para preservar o evento e
            # mantemos exatamente os MESMOS aliases de saída do contrato.
            #   geracao_verificada_mwh <- val_geracaoverificada
            #   geracao_referencia_mwh <- val_geracaoestimada
            #   chave da usina         <- nom_usina (a detail não tem id_ons)
            sql_public_coff = """
            WITH base AS (
                SELECT
                    nom_usina AS usina_id,
                    CASE
                        WHEN pg_typeof(din_instante)::text LIKE 'timestamp%' THEN din_instante::timestamp
                        ELSE to_timestamp(din_instante, 'YYYY-MM-DD HH24:MI:SS')
                    END AS timestamp,
                    nom_usina AS fonte,
                    COALESCE(NULLIF(REPLACE(val_geracaoverificada::text, ',', '.'), '')::double precision, 0) * 0.5 AS geracao_verificada_mwh,
                    COALESCE(NULLIF(REPLACE(val_geracaoestimada::text, ',', '.'), '')::double precision, 0) * 0.5 AS geracao_referencia_mwh,
                    GREATEST(
                        COALESCE(NULLIF(REPLACE(val_geracaoestimada::text, ',', '.'), '')::double precision, 0)
                        - COALESCE(NULLIF(REPLACE(val_geracaoverificada::text, ',', '.'), '')::double precision, 0),
                        0
                    ) * 0.5 AS energia_restringida_mwh,
                    (NULLIF(REPLACE(val_geracaoestimada::text, ',', '.'), '') IS NOT NULL) AS referencia_oficial,
                    'coff_eolica_detail_geracao_estimada'::text AS referencia_calculo_curtailment,
                    NULL::double precision AS geracao_limitada_mwmed,
                    'COFF'::text AS cod_razaorestricao,
                    NULL::text AS origem_restricao,
                    NULL::text AS razao_restricao,
                    CASE
                        WHEN UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') THEN 'NE'
                        WHEN UPPER(COALESCE(id_estado, '')) IN ('PA','TO','AP','AM','RR','AC','RO') THEN 'N'
                        ELSE UPPER(COALESCE(id_estado, ''))
                    END AS submercado
                FROM public.restricao_coff_eolica_detail
                WHERE nom_usina = :usina_id
            )
            SELECT usina_id, timestamp, fonte, geracao_verificada_mwh, geracao_referencia_mwh,
                   energia_restringida_mwh, referencia_oficial, referencia_calculo_curtailment,
                   geracao_limitada_mwmed, razao_restricao, cod_razaorestricao,
                   origem_restricao AS cod_origemrestricao, origem_restricao, submercado
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
                false AS referencia_oficial,
                'geracao_programada_menos_verificada_legacy_fallback'::text AS referencia_calculo_curtailment,
                NULL::text AS razao_restricao,
                NULL::text AS cod_razaorestricao,
                NULL::text AS cod_origemrestricao,
                NULL::text AS origem_restricao,
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

        sql_stg = """
        WITH pld_norm AS (
            SELECT
                (to_timestamp(mes_referencia::text || '01', 'YYYYMMDD')
                 + ((NULLIF(periodo_comercializacao, '')::integer - 1) * interval '1 hour'))::timestamp AS timestamp,
                UPPER(submercado) AS submercado,
                pld::double precision AS pld_reais_mwh
            FROM stg_ccee.pld_horario_submercado
            WHERE UPPER(submercado) = :submercado_public
              AND NULLIF(periodo_comercializacao, '') ~ '^[0-9]+$'
        )
        SELECT timestamp, submercado, pld_reais_mwh
        FROM pld_norm
        WHERE timestamp BETWEEN :inicio AND :fim
          AND pld_reais_mwh IS NOT NULL
        ORDER BY timestamp
        """
        rows_stg = self._safe_mappings_query(
            sql_stg,
            {"submercado_public": submercado_public, "inicio": inicio, "fim": fim},
        )
        if rows_stg:
            return rows_stg

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
        dw_usina = self._resolve_dw_usina(usina_id)
        if dw_usina:
            table = self._dw_table_for_fonte_key(self._dw_fonte_key(dw_usina.get("fonte")))
            if table:
                sql_dw = f"""
                SELECT
                    :usina_id AS usina_id,
                    m.din_instante AS timestamp,
                    COALESCE(m.val_geracao, 0)::double precision * 0.5 AS geracao_mwh,
                    CASE
                        WHEN COALESCE(m.potencia_mw, 0) > 0 THEN COALESCE(m.val_geracao, 0)::double precision / m.potencia_mw::double precision
                        ELSE 0::double precision
                    END AS fator_capacidade
                FROM {table} m
                WHERE m.nom_usina = :nom_usina
                  AND m.din_instante BETWEEN :inicio AND :fim
                  AND (CAST(:id_estado AS text) IS NULL OR m.id_estado = CAST(:id_estado AS text))
                  AND (:ne_only = false OR {self._submercado_expr('m')} = 'NE' OR UPPER(COALESCE(m.id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA'))
                ORDER BY m.din_instante
                """
                return self._safe_mappings_query(
                    sql_dw,
                    {
                        "usina_id": usina_id,
                        "nom_usina": dw_usina.get("mart_nom_usina") or dw_usina.get("nome"),
                        "id_estado": dw_usina.get("id_estado"),
                        "inicio": inicio,
                        "fim": fim,
                        "ne_only": self.mvp_only_nordeste,
                    },
                )

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

        dw_usina = self._resolve_dw_usina(usina_id)
        if dw_usina:
            fonte_key = self._dw_fonte_key(dw_usina.get("fonte"))
            table = self._dw_table_for_fonte_key(fonte_key)
            conjunto_table = self._dw_conjunto_table_for_fonte_key(fonte_key)
            if table and conjunto_table:
                sql_dw = f"""
                WITH co AS (
                    SELECT
                        m.din_instante AS timestamp,
                        COALESCE(m.corte_mwh, 0)::double precision AS energia_restringida_mwh,
                        CASE
                            WHEN COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'CF%' OR COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'CNF%' OR COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'CONFIAB%' THEN 'confiabilidade'
                            WHEN COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'IE%' OR COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'REL%' OR COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'INDISP_EXT%' THEN 'indisponibilidade_externa'
                            WHEN COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'EN%' OR COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'ENE%' OR COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'ENER%' THEN 'energetico'
                            WHEN COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'RE%' OR COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'ELE%' THEN 'restricao_eletrica'
                            WHEN COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'SE%' OR COALESCE(m.cod_razaorestricao, cj.cod_razaorestricao) ILIKE 'SEG%' THEN 'seguranca_eletroenergetica'
                            ELSE 'indefinido'
                        END AS razao_norm
                    FROM {table} m
                    LEFT JOIN {conjunto_table} cj
                      ON cj.din_instante = m.din_instante
                     AND cj.nom_usina = m.nom_usina_conjunto
                    WHERE m.id_ons = :id_ons
                      AND (CAST(:ceg AS text) IS NULL OR m.ceg = CAST(:ceg AS text))
                      AND m.din_instante BETWEEN :inicio AND :fim
                      AND COALESCE(m.corte_mwh, 0) > 0
                      AND (:ne_only = false OR {self._submercado_expr('m')} = 'NE')
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
                    sql_dw,
                    {
                        "id_ons": dw_usina.get("id_ons"),
                        "ceg": dw_usina.get("ceg"),
                        "inicio": inicio,
                        "fim": fim,
                        "submercado_public": submercado_public,
                        "ne_only": self.mvp_only_nordeste,
                    },
                )
                if rows:
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
                        COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0)
                        - COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0),
                        0
                    ) * 0.5 AS energia_restringida_mwh,
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
                        COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0)
                        - COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0),
                        0
                    ) * 0.5 AS energia_restringida_mwh,
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

    # ------------------------------------------------------------------ #
    # GRANULARIDADE ÚNICA (marts renováveis) — usado pela camada DEBUG.
    # Fonte: dw.mart_eolica + dw.mart_solar (1 linha por usina, grão 30min,
    # colunas cruas). Unifica eólica e solar numa mesma granularidade para
    # análise e treino dos modelos. NÃO altera o fluxo de produção; apenas
    # adiciona uma forma de carregar os dados do banco atualizado.
    #
    # Esquema real (validado em hacka-energinn):
    #   dw.mart_eolica / dw.mart_solar: din_instante, nom_usina, id_estado,
    #     id_subsistema (NE/N/S/SE), nom_subsistema, fonte (EOLICA/FOTOVOLTAICA),
    #     potencia_mw, val_geracao, val_geracaoreferencia,
    #     val_geracaoreferenciafinal, cod_razaorestricao, cod_origemrestricao.
    #   Coordenadas/potência: o mart traz potencia_mw (parcial) e NÃO traz lat/lon.
    #   dim_usina.potencia_mw é nula e os nomes não casam 1:1; por isso usamos a
    #   potência do próprio mart e deixamos lat/lon nulos (coords entram depois,
    #   quando houver chave estável de join).
    # ------------------------------------------------------------------ #
    _MART_AGG_SQL = """
        SELECT
            m.nom_usina                                  AS usina_id,
            m.nom_usina                                  AS nome,
            '{fonte_out}'::text                          AS fonte,
            max(COALESCE(m.potencia_mw, 0))::double precision AS potencia_mw,
            CASE
                WHEN UPPER(COALESCE(max(m.id_subsistema), '')) IN ('NE','NORDESTE') THEN 'NE'
                WHEN UPPER(COALESCE(max(m.id_subsistema), '')) IN ('N','NORTE') THEN 'N'
                WHEN UPPER(COALESCE(max(m.id_subsistema), '')) IN ('S','SUL') THEN 'S'
                ELSE 'SE'
            END                                          AS submercado,
            max(m.id_estado)                             AS id_estado,
            NULL::double precision                       AS latitude,
            NULL::double precision                       AS longitude,
            count(*)                                     AS n_reg,
            sum(COALESCE(m.val_geracao, 0))/2.0          AS ger_mwh,
            sum(GREATEST(
                COALESCE(m.val_geracaoreferenciafinal, m.val_geracaoreferencia, 0)
                - COALESCE(m.val_geracao, 0), 0))/2.0    AS corte_mwh,
            sum(CASE WHEN m.cod_razaorestricao IN ('CNF','REL','CF','IE')
                     THEN GREATEST(COALESCE(m.val_geracaoreferenciafinal, m.val_geracaoreferencia, 0) - COALESCE(m.val_geracao, 0), 0)
                     ELSE 0 END)/2.0                      AS corte_ressarc_mwh,
            sum(CASE WHEN m.cod_razaorestricao IS NOT NULL THEN 1 ELSE 0 END) AS n_restrito
        FROM dw.{table} m
        GROUP BY m.nom_usina
    """

    def _aggregate_all_marts(self) -> list[dict]:
        """Agrega TODAS as usinas (eólica + solar) dos marts uma única vez, com
        cache de módulo (TTL). É a base de granularidade ÚNICA por nom_usina —
        list/get/ranking/unidades derivam daqui sem reescanear os 12M de linhas."""
        key = bool(self.mvp_only_nordeste)
        hit = _MART_AGG_CACHE.get(key)
        if hit and (_time.time() - hit[0]) < _MART_AGG_TTL:
            return hit[1]

        eol = self._MART_AGG_SQL.format(fonte_out="eolica", table="mart_eolica")
        sol = self._MART_AGG_SQL.format(fonte_out="solar", table="mart_solar")
        sql = f"""
        WITH eol AS ({eol}),
             sol AS ({sol}),
             uni AS (SELECT * FROM eol UNION ALL SELECT * FROM sol)
        SELECT usina_id, nome, fonte, potencia_mw, submercado, id_estado, latitude, longitude,
               n_reg, ger_mwh, corte_mwh, corte_ressarc_mwh, n_restrito
        FROM uni
        WHERE (:ne_only = false OR submercado = 'NE')
        ORDER BY corte_mwh DESC
        """
        rows = self._safe_mappings_query(sql, {"ne_only": self.mvp_only_nordeste})
        rows = self._enrich_coords(rows)
        _MART_AGG_CACHE[key] = (_time.time(), rows)
        return rows

    def list_usinas_mart(self, limit: int = 50):
        """Lista usinas na granularidade única (eólica + solar) a partir dos marts."""
        rows = self._aggregate_all_marts()
        return rows[: int(limit)]

    # --- coordenadas para o mapa: match por nome + fallback centróide estadual ---
    @staticmethod
    def _norm_nome(s) -> str:
        import re
        import unicodedata
        s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode().lower()
        s = re.sub(r"\b(conj|conjunto|eolico|eolica|complexo|parque|eol|usina|kv|\d+)\b", " ", s)
        s = re.sub(r"[^a-z ]", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    def _coords_indexes(self):
        if _COORDS_SHARED_CACHE["data"] is not None:
            return _COORDS_SHARED_CACHE["data"]
        por_nome: dict[str, tuple[float, float]] = {}
        centro: dict[str, list] = {}
        try:
            rows = self.db.execute(text(
                "SELECT d.nom_usina, d.lat, d.lon, g.id_estado "
                "FROM dw.dim_usina d LEFT JOIN dw.dim_geografia g ON g.sk_geografia = d.sk_geografia "
                "WHERE d.lat IS NOT NULL AND d.lon IS NOT NULL"
            )).mappings().all()
            acc: dict[str, list] = {}
            for r in rows:
                key = self._norm_nome(r["nom_usina"])
                if key:
                    acc.setdefault(key, []).append((float(r["lat"]), float(r["lon"])))
                uf = (r.get("id_estado") or "").upper()
                if uf:
                    centro.setdefault(uf, []).append((float(r["lat"]), float(r["lon"])))
            for k, v in acc.items():
                la = sum(p[0] for p in v) / len(v)
                lo = sum(p[1] for p in v) / len(v)
                por_nome[k] = (la, lo)
        except Exception:
            self.db.rollback()
        centroides = {uf: (sum(p[0] for p in v) / len(v), sum(p[1] for p in v) / len(v)) for uf, v in centro.items()}
        _COORDS_SHARED_CACHE["data"] = {"nome": por_nome, "centro": centroides}
        return _COORDS_SHARED_CACHE["data"]

    def _enrich_coords(self, rows: list[dict]) -> list[dict]:
        if not rows:
            return rows
        idx = self._coords_indexes()
        por_nome, centro = idx["nome"], idx["centro"]
        nome_keys = list(por_nome.keys())
        import random
        rng = random.Random(42)
        for r in rows:
            if r.get("latitude") is not None and r.get("longitude") is not None:
                continue
            key = self._norm_nome(r.get("nome") or r.get("usina_id"))
            coord = por_nome.get(key)
            if coord is None and key:
                mt = set(key.split())
                best, best_sc = None, 0.0
                for dn in nome_keys:
                    dt = set(dn.split())
                    if not dt:
                        continue
                    sc = len(mt & dt) / max(len(mt | dt), 1)
                    if sc > best_sc:
                        best_sc, best = sc, dn
                if best is not None and best_sc >= 0.5:
                    coord = por_nome[best]
            if coord is None:
                uf = str(r.get("id_estado") or "").upper()
                base = centro.get(uf)
                if base is not None:
                    coord = (base[0] + rng.uniform(-0.25, 0.25), base[1] + rng.uniform(-0.25, 0.25))
            if coord is not None:
                r["latitude"], r["longitude"] = round(coord[0], 5), round(coord[1], 5)
        return rows

    def get_usina_mart(self, usina_id: str):
        """Ficha de uma usina (eólica/solar) na granularidade única dos marts.

        Deriva do agregado já cacheado (_aggregate_all_marts) para não reescanear
        os marts a cada detalhe. Inclui métricas agregadas (corte/ger/n_reg) além
        do contrato base de identificação.
        """
        for r in self._aggregate_all_marts():
            if str(r.get("usina_id")) == str(usina_id):
                return dict(r)
        return None

    def get_serie_mart(self, usina_id: str, inicio: datetime, fim: datetime, limit: int = 4000):
        """Série semi-horária de uma usina (eólica OU solar) no grão único do mart.

        Mantém os MESMOS aliases consumidos pela camada DEBUG:
        timestamp, geracao_mwh, geracao_referencia_mwh, energia_restringida_mwh,
        cod_razaorestricao, cod_origemrestricao, fonte.
        """
        sql = """
        WITH base AS (
            SELECT
                nom_usina AS usina_id,
                din_instante::timestamp AS timestamp,
                'eolica'::text AS fonte,
                COALESCE(val_geracao, 0)::double precision AS geracao_mw,
                COALESCE(val_geracaoreferenciafinal, val_geracaoreferencia, 0)::double precision AS referencia_mw,
                cod_razaorestricao,
                cod_origemrestricao
            FROM dw.mart_eolica
            WHERE nom_usina = :usina_id AND din_instante BETWEEN :inicio AND :fim
            UNION ALL
            SELECT
                nom_usina AS usina_id,
                din_instante::timestamp AS timestamp,
                'solar'::text AS fonte,
                COALESCE(val_geracao, 0)::double precision AS geracao_mw,
                COALESCE(val_geracaoreferenciafinal, val_geracaoreferencia, 0)::double precision AS referencia_mw,
                cod_razaorestricao,
                cod_origemrestricao
            FROM dw.mart_solar
            WHERE nom_usina = :usina_id AND din_instante BETWEEN :inicio AND :fim
        )
        SELECT
            usina_id,
            timestamp,
            fonte,
            geracao_mw / 2.0 AS geracao_mwh,
            referencia_mw / 2.0 AS geracao_referencia_mwh,
            GREATEST(referencia_mw - geracao_mw, 0) / 2.0 AS energia_restringida_mwh,
            cod_razaorestricao,
            cod_origemrestricao
        FROM base
        ORDER BY timestamp
        LIMIT :limit
        """
        return self._safe_mappings_query(
            sql, {"usina_id": usina_id, "inicio": inicio, "fim": fim, "limit": int(limit)}
        )


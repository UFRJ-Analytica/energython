from __future__ import annotations

"""SQLs de referência para adaptar PostgresRepository ao DW usado no Streamlit.

Objetivo: alterar somente a leitura do banco mantendo os aliases esperados pelo
Energython. Copie os trechos relevantes para `backend/app/repositories/postgres_repo.py`.

Não há credenciais neste arquivo.
"""

NE_STATES = "('MA','PI','CE','RN','PB','PE','AL','SE','BA')"

LIST_USINAS_DW_SQL = f"""
WITH coords AS (
    SELECT
        upper(trim(nom_usina)) AS nom_key,
        avg(lat)::double precision AS latitude,
        avg(lon)::double precision AS longitude
    FROM dw.dim_usina
    WHERE ceg_core LIKE 'EOL%' AND lat IS NOT NULL AND lon IS NOT NULL
    GROUP BY 1
), frota AS (
    SELECT
        nom_usina AS usina_id,
        nom_usina AS nome,
        'eolica'::text AS fonte,
        max(potencia_mw)::double precision AS potencia_mw,
        CASE
            WHEN UPPER(COALESCE(id_estado, '')) IN {NE_STATES} THEN 'NE'
            WHEN UPPER(COALESCE(nom_subsistema, '')) = 'NORDESTE' THEN 'NE'
            WHEN UPPER(COALESCE(nom_subsistema, '')) = 'NORTE' THEN 'N'
            WHEN UPPER(COALESCE(nom_subsistema, '')) = 'SUL' THEN 'S'
            ELSE UPPER(COALESCE(nom_subsistema, 'SE'))
        END AS submercado,
        upper(trim(nom_usina)) AS nom_key
    FROM dw.mart_eolica
    WHERE nom_usina <> 'Usina nao identificada'
    GROUP BY nom_usina, id_estado, nom_subsistema
)
SELECT
    f.usina_id,
    f.nome,
    f.fonte,
    COALESCE(f.potencia_mw, 0)::double precision AS potencia_mw,
    f.submercado,
    c.latitude,
    c.longitude,
    NULL::double precision AS garantia_fisica_mwm
FROM frota f
LEFT JOIN coords c ON c.nom_key = f.nom_key
WHERE (:ne_only = false OR f.submercado = 'NE')
ORDER BY f.nome
"""

GET_USINA_DW_SQL = f"""
WITH base AS (
    {LIST_USINAS_DW_SQL.rstrip().rstrip(';')}
)
SELECT usina_id, nome, fonte, potencia_mw, submercado, latitude, longitude, garantia_fisica_mwm
FROM base
WHERE usina_id = :usina_id
LIMIT 1
"""

CONSTRAINED_OFF_DW_SQL = """
-- BANCO ATUALIZADO: a COFF eólica vive em public.restricao_coff_eolica_detail (30min).
-- Não há cod_razaorestricao na tabela; usamos a sentinela 'COFF'.
SELECT
    nom_usina AS usina_id,
    din_instante::timestamp AS timestamp,
    'eolica'::text AS fonte,
    COALESCE(val_geracaoverificada, 0)::double precision * 0.5 AS geracao_verificada_mwh,
    COALESCE(val_geracaoestimada, 0)::double precision * 0.5 AS geracao_referencia_mwh,
    GREATEST(COALESCE(val_geracaoestimada, 0) - COALESCE(val_geracaoverificada, 0), 0)::double precision * 0.5 AS energia_restringida_mwh,
    'COFF'::text AS cod_razaorestricao,
    NULL::text AS cod_origemrestricao,
    NULL::text AS origem_restricao,
    CASE
        WHEN UPPER(COALESCE(id_estado, '')) IN ('MA','PI','CE','RN','PB','PE','AL','SE','BA') THEN 'NE'
        WHEN UPPER(COALESCE(id_estado, '')) IN ('PA','TO','AP','AM','RR','AC','RO') THEN 'N'
        ELSE UPPER(COALESCE(id_estado, ''))
    END AS submercado
FROM public.restricao_coff_eolica_detail
WHERE nom_usina = :usina_id
  AND din_instante BETWEEN :inicio AND :fim
  AND GREATEST(COALESCE(val_geracaoestimada, 0) - COALESCE(val_geracaoverificada, 0), 0) > 0
ORDER BY din_instante
"""

GERACAO_HORARIA_DW_SQL = """
SELECT
    nom_usina AS usina_id,
    din_instante::timestamp AS timestamp,
    COALESCE(val_geracao, 0)::double precision AS geracao_mwh,
    0::double precision AS fator_capacidade
FROM public.geracao_usina_2
WHERE nom_usina = :usina_id
  AND din_instante BETWEEN :inicio AND :fim
ORDER BY din_instante
"""

DISPONIBILIDADE_DW_SQL = """
SELECT
    nom_usina AS usina_id,
    din_instante::timestamp AS timestamp,
    COALESCE(val_dispoperacional, 0)::double precision AS disponibilidade,
    0::double precision AS teifa,
    0::double precision AS teip
FROM public.disponibilidade_usina
WHERE nom_usina = :usina_id
  AND din_instante BETWEEN :inicio AND :fim
ORDER BY din_instante
"""

DESPACHO_DW_SQL = """
SELECT
    nom_pontoconexao AS usina_id,
    din_instante::timestamp AS timestamp,
    COALESCE(val_geracaoprogramada, 0)::double precision AS geracao_programada_mwh
FROM public.fator_capacidade_2
WHERE nom_pontoconexao = :usina_id
  AND din_instante BETWEEN :inicio AND :fim
ORDER BY din_instante
"""

GARANTIA_FISICA_EMPTY_SQL = """
SELECT
    :usina_id AS usina_id,
    NULL::timestamp AS timestamp,
    NULL::double precision AS garantia_fisica_mwh
WHERE false
"""

# Se a tabela de PLD permanecer no schema public, manter o SQL atual do repositório.
# Se existir uma tabela DW nova, adapte para devolver:
# timestamp, submercado, pld_reais_mwh.
PLD_EXPECTED_COLUMNS = ("timestamp", "submercado", "pld_reais_mwh")

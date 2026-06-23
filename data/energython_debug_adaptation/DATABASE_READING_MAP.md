# Mapa de leitura do banco — contrato Energython x DW

Este documento define como trocar a leitura do banco sem alterar nomes de variáveis, schemas ou contratos da API.

## Contrato que o backend/frontend já esperam

### Usina

| Campo esperado | Tipo | Uso no front/back |
|---|---:|---|
| `usina_id` | string | rota `/usinas/{id}` e seleção |
| `nome` | string | cards, tabelas, header |
| `fonte` | string | filtro e ícone solar/eólica |
| `potencia_mw` | float | capacidade instalada |
| `submercado` | string | filtro e PLD |
| `latitude` | float/null | mapa |
| `longitude` | float/null | mapa |

### Evento constrained/off

| Campo esperado | Origem conceitual |
|---|---|
| `usina_id` | identificador ONS/conjunto |
| `timestamp` | instante da restrição |
| `fonte` | nome/tipo de usina no evento |
| `geracao_verificada_mwh` | geração observada convertida para MWh |
| `geracao_referencia_mwh` | referência convertida para MWh |
| `energia_restringida_mwh` | gap positivo convertido para MWh |
| `razao_restricao` | classificação textual quando existir |
| `cod_razaorestricao` | código ENE/CNF/REL/etc. |
| `cod_origemrestricao` | origem SIS/LOC/etc. |
| `origem_restricao` | alias textual da origem |
| `submercado` | NE/N/SE/S |

## Princípio de alteração

Alterar apenas o SQL para devolver **os mesmos aliases**.

Exemplo:

```sql
SELECT
  id_ons AS usina_id,
  nom_usina AS nome,
  'eolica' AS fonte,
  potencia_mw AS potencia_mw,
  'NE' AS submercado,
  lat AS latitude,
  lon AS longitude
FROM ...
```

O restante do backend deve continuar consumindo `usina_id`, `nome`, `fonte`, etc.

## Fontes DW observadas no Streamlit

| Tabela | Uso sugerido |
|---|---|
| `dw.mart_eolica` | frota por `nom_usina`, séries de geração/referência/restrição |
| `dw.dim_usina` | coordenadas, `sk_usina`, metadados e filtro `ceg_core LIKE 'EOL%'` |
| `dw.dim_geografia` | fallback geográfico por estado |
| `dw.fato_restricao_coff` | granularidade unitária `sk_usina` e restrições COFF |

## Mapeamento sugerido para `dw.mart_eolica`

| Contrato Energython | Campo DW sugerido |
|---|---|
| `usina_id` | `nom_usina` ou identificador estável se existir (`id_ons`/`cod_ons`) |
| `nome` | `nom_usina` |
| `fonte` | literal `'eolica'` ou coluna normalizada |
| `potencia_mw` | `max(potencia_mw)` |
| `submercado` | `nom_subsistema` normalizado para `NE/N/SE/S` |
| `latitude` | `dim_usina.lat` ou fallback |
| `longitude` | `dim_usina.lon` ou fallback |
| `timestamp` | `din_instante` |
| `geracao_verificada_mwh` | `val_geracao / 2` para 30 min |
| `geracao_referencia_mwh` | `val_geracaoreferencia / 2` |
| `energia_restringida_mwh` | `greatest(val_geracaoreferencia - val_geracao, 0) / 2` |
| `cod_razaorestricao` | `cod_razaorestricao` |
| `cod_origemrestricao` | `cod_origemrestricao` |

## Arquivo com SQLs prontos

Ver:

```text
data/energython_debug_adaptation/backend/postgres_repo_dw_queries.py
```

Esse arquivo contém consultas com aliases do contrato atual. Elas devem ser copiadas gradualmente para `backend/app/repositories/postgres_repo.py` quando a migração for aplicada.

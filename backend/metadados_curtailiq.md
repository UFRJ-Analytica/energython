# Metadados do CurtailIQ — Catálogo de Dados e Dicionário de Colunas

> Documento de referência de dados do projeto. Combina (A) **catálogo de datasets** — o que é cada fonte, onde fica, granularidade — e (B) **dicionário de colunas** — definição, unidade e tipo de cada campo.
>
> **Procedência de cada parte:**
> - As seções de **fontes externas (ONS, CCEE, ANEEL)** vêm dos **dicionários oficiais** do ONS (Restrição Constrained-off, versões verificadas em 2025) e do guia da CCEE Dados Abertos. São confiáveis.
> - As seções do **banco interno (`public.*`, `gold.*`)** e dos **campos calculados** vêm dos documentos de engenharia do próprio time — **devem ser validadas contra o schema real** antes de tratar como verdade absoluta.
> - Onde há incerteza, está marcado com ⚠️.

---

# PARTE A — Catálogo de Datasets

## A.1 Fontes externas (públicas)

| Fonte | Dataset | Conteúdo | Granularidade | Atualização | Acesso |
|---|---|---|---|---|---|
| ONS | `restricao_coff_eolica_usi` | Constrained-off eólico **por conjunto** (razão/origem/energia) | 30 min (semi-horário), MWmed | Recorrente (consistência contínua) | CSV/XLSX via portal/S3 |
| ONS | `restricao_coff_fotovoltaica` | Constrained-off solar **por conjunto** | 30 min, MWmed | Recorrente | CSV/XLSX |
| ONS | `restricao_coff_eolica_detail` | Constrained-off eólico **por usina individual** (geração/recurso, **sem** razão/origem) | 30 min, MWmed | Recorrente | CSV/XLSX |
| ONS | `restricao_coff_fotovoltaica_detail` | Constrained-off solar **por usina individual** | 30 min, MWmed | Recorrente | CSV/XLSX |
| CCEE | `pld_horario` | PLD por submercado e hora | Horário, R$/MWh | Diária (ano corrente) | CKAN API / CSV (dump) |
| ANEEL | SIGA | Cadastro de usinas (fonte, potência, fase, localização) | Cadastral | Periódica | dadosabertos.aneel.gov.br |

**URLs base:**
- ONS: `https://dados.ons.org.br/dataset/<nome_do_dataset>` (arquivos mensais no S3 `ons-aws-prod-opendata`)
- CCEE: `https://dadosabertos.ccee.org.br` (CKAN 2.10, anônimo)
- ANEEL: `https://dadosabertos.aneel.gov.br`

**Separação crítica ONS (não confundir):** razão/origem/energia regulatória existem **só nas tabelas agregadas por conjunto**; granularidade por usina existe **só nas detail** (sem razão/origem). Cruzar as duas: agregada = verdade regulatória; detail = abre o conjunto em usinas via `estimada − verificada` como chave de rateio (marcar como **alocação estimada**).

## A.2 Banco interno (CurtailIQ) ⚠️ validar contra schema real

| Schema | Tabela | Papel | Observação |
|---|---|---|---|
| `public` | `restricao_coff_eolica_usi` | Espelho da COFF agregada eólica do ONS | Fonte regulatória/financeira atual |
| `public` | `restricao_coff_fotovoltaica` | Espelho da COFF agregada solar | Idem |
| `public` | `restricao_coff_eolica_detail` | Espelho da detail eólica | Para drill-down por usina |
| `public` | `restricao_coff_fotovoltaica_detail` | Espelho da detail solar | Idem |
| `public` | `ccee_pld_horario` | Espelho do PLD CCEE | Fallback do PLD |
| `gold` | `constrained_off` | COFF normalizado (camada gold) | ⚠️ "não temos schema gold operacional" — hoje cai no fallback `public.*` |
| `gold` | `pld_horario` | PLD normalizado | Preferencial; fallback `public.ccee_pld_horario` |
| `gold` | `usinas` | Cadastro de usinas | Para join de submercado/fonte |

---

# PARTE B — Dicionário de Colunas

## B.1 ONS — COFF Agregada (`restricao_coff_eolica_usi` / `restricao_coff_fotovoltaica`)
*Fonte: Dicionário oficial ONS, Restrição Constrained-off Fotovoltaicas v1.2 (26/09/2025) — eólica análoga.*

| Código | Definição oficial | Tipo | Unidade | Nulo? |
|---|---|---|---|---|
| `id_subsistema` | Identificador do subsistema | TEXTO | — | Não |
| `nom_subsistema` | Nome do subsistema | TEXTO | — | Não |
| `id_estado` | Sigla do estado | TEXTO | — | Não |
| `nom_estado` | Nome do estado | TEXTO | — | Não |
| `nom_usina` | Nome da usina **ou conjunto** | TEXTO | — | Sim |
| `id_ons` | Identificador da usina/conjunto no ONS | TEXTO (6) | — | Não |
| `ceg` | Código Único de Empreendimento de Geração (ANEEL) | TEXTO (30) | — | Não |
| `din_instante` | Data/hora (hora de Brasília, UTC−3) | DATETIME | — | Não |
| `val_geracao` | **Geração efetivamente realizada** | FLOAT | **MWmed** | Não |
| `val_geracaolimitada` | **Geração limitada por alguma restrição** (teto sob restrição — **NÃO é o corte**) | FLOAT | **MWmed** | Sim |
| `val_disponibilidade` | Disponibilidade verificada em tempo real | FLOAT | **MWmed** | Sim |
| `val_geracaoreferencia` | Geração de referência (estimada) — o que **teria gerado** | FLOAT | **MWmed** | Sim |
| `val_geracaoreferenciafinal` | Geração de referência **final** (`G_Ref_Final`) conforme MPO/RO-AO.BR.13 Rev.09 item 5.2.2.10: menor entre referência e disponibilidade, ajustado por tolerância e eventual diferença `Geração Limitada - Geração Verificada`; **não é a frustração diretamente** | FLOAT | **MWmed** | Sim |
| `cod_razaorestricao` | Razão: **REL** (indisp. externa/elétrica), **CNF** (confiabilidade), **ENE** (energética), **PAR** (parecer de acesso) | TEXTO (3) | — | Sim |
| `cod_origemrestricao` | Origem: **LOC** (local), **SIS** (sistêmica) | TEXTO (3) | — | Sim |
| `dsc_restricao` | Detalhamento textual do motivo (add. set/2025) | TEXTO (600) | — | Sim |

**Energia constrained-off / energia restringida — fórmula correta:**
`max((val_geracaoreferenciafinal ou val_geracaoreferencia) − val_geracao, 0) × 0,5`
(× 0,5 = MWmed → MWh em intervalo de 30 min). Pelo MPO, a grandeza energética usada na apuração ESS é “Frustração de Geração”; no código ela é exposta como `energia_restringida_mwh`. **Não usar `val_geracaolimitada` como corte direto**: ela é ordem/teto operacional e pode entrar apenas indiretamente no cálculo ONS da `G_Ref_Final`.

## B.2 ONS — COFF Detail (`restricao_coff_eolica_detail` / `_fotovoltaica_detail`)
*Fonte: Dicionário oficial ONS, Detalhamento por Usina v1.4 (20/04/2025).*

| Código | Definição oficial | Tipo | Unidade | Nulo? |
|---|---|---|---|---|
| `id_subsistema` | Identificador do subsistema | TEXTO (3) | — | Não |
| `id_estado` | Sigla do estado | TEXTO (2) | — | Não |
| `nom_modalidadeoperacao` | Modalidade de operação da usina | TEXTO (20) | — | Não |
| `nom_conjuntousina` | Nome do conjunto (usinas Tipo II-C) | TEXTO (50) | — | Sim |
| `nom_usina` | Nome da **usina individual** | TEXTO (50) | — | Não |
| `id_ons` | Identificador da usina/conjunto no ONS | TEXTO (6) | — | Não |
| `ceg` | Código Único de Empreendimento (ANEEL) | TEXTO (30) | — | Não |
| `din_instante` | Data/hora | DATETIME | — | Não |
| `val_ventoverificado` | Vento verificado (eólica) | FLOAT | m/s* | Sim |
| `val_irradianciaverificado` | Irradiância verificada (solar) | FLOAT | W/m² | Sim |
| `flg_dadoventoinvalido` | Flag = 1 se medição de vento inválida (>6 min de falha na semi-hora) | FLOAT | — | Sim |
| `val_geracaoestimada` | Geração estimada (do recurso) | FLOAT | **MWmed** | Sim |
| `val_geracaoverificada` | Geração verificada | FLOAT | **MWmed** | Sim |

*O dicionário grafa "m3/s" para vento — provável erro de digitação do ONS; velocidade de vento é m/s.

**Não há** `cod_razaorestricao`, `cod_origemrestricao`, `val_geracaolimitada` nem `val_geracaoreferenciafinal` na detail. Frustração estimada por usina ≈ `(val_geracaoestimada − val_geracaoverificada) × 0,5`.

## B.3 CCEE — PLD Horário (`pld_horario`)
*Fonte: guia CCEE Dados Abertos (CKAN).*

| Código | Definição | Tipo | Unidade |
|---|---|---|---|
| `MES_REFERENCIA` | Mês de referência (AAAAMM) | TEXTO | — |
| `SUBMERCADO` | Submercado **por extenso**: `SUDESTE`, `SUL`, `NORDESTE`, `NORTE` | TEXTO | — |
| `PERIODO_COMERCIALIZACAO` | Período de 1h dentro do mês | NUMÉRICO | — |
| `DIA` | Dia | TEXTO | — |
| `HORA` | Hora | NUMÉRICO | — |
| `PLD_HORA` | Preço de Liquidação das Diferenças | NUMÉRICO | **R$/MWh** |

**De-para de submercado obrigatório no join:** `SUDESTE→SE_CO`, `SUL→S`, `NORDESTE→NE`, `NORTE→N`. Limites de sanidade do PLD 2025: R$ 58,60 a R$ 1.542,23/MWh.

## B.4 Domínio interno — `ConstrainedOffEvent` / eventos ⚠️ validar
*Fonte: documentos de engenharia do time.*

| Campo | Conteúdo | Origem |
|---|---|---|
| `timestamp` | Início do intervalo/evento | COFF `din_instante` |
| `energia_restringida_mwh` | Energia cortada (após fórmula correta + ×0,5) | calculado |
| `razao_restricao` / `cod_razaorestricao` | Razão normalizada | COFF |
| `cod_origemrestricao` / `origem_restricao` | Origem (SIS/LOC) | COFF |
| `total_intervalos_restricao` | Nº de intervalos de 30 min | calculado |
| `total_eventos_curtailment` | Nº de eventos contínuos agregados | calculado (eventização) |
| `duracao_horas` | Duração real do evento agregado | calculado |
| `flag gap` | Quebra por descontinuidade temporal | calculado |
| `referencia_oficial` | True se `val_geracaoreferenciafinal` presente; False quando o cálculo caiu no fallback estimativo por `val_geracaoreferencia` | implementado/recomendado |
| `referencia_calculo_curtailment` | `geracao_referencia_final_mpo_5_13`, `geracao_referencia_estimativa_fallback` ou `energia_restringida_precomputada` | implementado/recomendado |

---

# PARTE C — Campos Calculados pelo Backend ⚠️ validar

| Campo | Cálculo | Regra/Fonte |
|---|---|---|
| `energia_restringida_mwh` | `max(referência_final − geração verificada, 0) × 0,5`; se referência final ausente, fallback estimativo por referência calculada | MPO/RO-AO.BR.13 Rev.09 item 5.2.2.10 + glossário 3.12/3.13 |
| `elegibilidade` / `status` | REL+SIS→elegível (Protocolo, c/ franquia); CNF+SIS→elegível só na janela 01/09/2023–25/11/2025 (Termo); ENE/PAR→não; LOC/origem ausente→revisão humana | REN 1.030/2022, 1.073/2023, Lei 15.269/2025 |
| `canal` | `PROTOCOLO_ONS` (REL, ≤90 dias) / `TERMO_COMPROMISSO_LEI_15269` (CNF na janela) | — |
| `energia_ressarcivel_mwh` | 0 se não elegível; REL: só acima da franquia anual; CNF: energia restringida (estimativa) | — |
| `valor_pleitavel_reais` | `energia_ressarcivel_mwh × PLD_horário_do_evento` | ESS valora pelo PLD do período |
| franquia (parâmetro) | eólica ⚠️ 78–82h/ano; solar ⚠️ 30,5–41h/ano (ano civil, acumulada) | REN 1.030/1.073 — **confirmar valor vigente** |

---

# PARTE D — Parâmetros Regulatórios (config, não hardcode)

| Parâmetro | Valor (MVP) | Fonte | Status |
|---|---|---|---|
| Janela Termo de Compromisso | 01/09/2023 a 25/11/2025 | Lei 15.269/2025 | Regulamentação em curso ⚠️ |
| Prazo Protocolo ONS | 90 dias corridos da ocorrência | RO-AO.BR.13 | — |
| Franquia eólica | ⚠️ 78–82 h/ano | REN 1.030 / divulgação | Atualizada anualmente pelo ONS |
| Franquia solar | ⚠️ 30,5–41 h/ano | REN 1.073 / divulgação | Idem |
| Razões ressarcíveis | REL (oficial), CNF (via Termo, janela) | REN + Lei 15.269 | ENE e PAR nunca |
| Mecanismo de pagamento | ESS (Encargo de Serviços do Sistema), via CCEE | — | Limitado a CCEAR/CER (ACR) |
| Intervalo COFF | 30 min (MWmed → ×0,5 para MWh) | Dicionário ONS | Confirmado |

---

# Avisos de procedência

1. **Confiável (fonte oficial):** Partes B.1, B.2, B.3 e os intervalos/unidades — vêm dos dicionários oficiais do ONS e do guia CCEE.
2. **Validar contra schema real:** Parte A.2, B.4 e C — vêm dos documentos de engenharia do time; nomes de tabela/coluna podem divergir.
3. **Regulação em movimento:** Parte D — Lei 15.269/2025, franquias e janela do Termo estão em regulamentação (consultas públicas, revisão da REN 1.030). Reconfirmar antes de uso real e manter em config.
4. Este documento reflete o estado do conhecimento na data de elaboração; os datasets do ONS/CCEE evoluem (versões de dicionário citadas explicitamente acima).

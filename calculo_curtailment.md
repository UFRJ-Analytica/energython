# Cálculo de Curtailment no CurtailIQ

Este documento explica o código, os dados, os metadados e a lógica técnica/legal usados hoje no backend para calcular:

1. Energia restringida / curtailment, em MWh.
2. Perda financeira, em reais.
3. Valor pleiteável / ressarcível, em reais.

Estado atual analisado:

- Commit: `6fc1f8e`
- Fórmula energética atual: corrigida.
- O backend não usa mais `val_geracaolimitada` como energia cortada.
- O backend calcula curtailment como diferença entre geração de referência e geração efetiva.

---

## 1. Entrada principal da parte financeira

Endpoint:

`backend/app/routers/financeiro.py`

Linhas 14-29:

```py
14|@router.get("/usinas/{usina_id}/perda", response_model=PerdaOut)
15|def perda_financeira(
...
24|        i, f = parse_range(inicio, fim, max_dias=366)
25|        out = service.calcular_perda(usina_id, i, f)
26|        total = len(out["serie"])
27|        out["paginacao_serie"] = {"total_count": total, "limit": limit, "offset": offset}
28|        out["serie"] = out["serie"][offset : offset + limit]
29|        return out
```

Ou seja:

`GET /api/usinas/{usina_id}/perda`

chama:

`FinanceiroService.calcular_perda(...)`

que é onde a perda em reais é calculada.

---

## 2. Fonte dos dados energéticos

Hoje, para COFF real, o backend tenta primeiro uma camada `gold.constrained_off`.

Se a gold não existe ou falha, cai no fallback das tabelas públicas do banco, que espelham o ONS:

- `public.restricao_coff_eolica_usi`
- `public.restricao_coff_fotovoltaica`

Isso está em:

`backend/app/repositories/postgres_repo.py`

Linhas 169-170:

```py
169|            # Fallback preferencial: tabelas COFF com código de razão explícito (CNF/ENE/REL)
170|            sql_public_coff = """
```

Tabelas usadas:

```py
195|                FROM public.restricao_coff_eolica_usi
...
220|                FROM public.restricao_coff_fotovoltaica
```

---

## 3. Parte energética: fórmula atual do curtailment

A fórmula principal está em:

`backend/app/repositories/postgres_repo.py`

### 3.1 Eólica

Linhas 179-186:

```py
179|                    COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0) * 0.5 AS geracao_verificada_mwh,
180|                    COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0) * 0.5 AS geracao_referencia_mwh,
181|                    GREATEST(
182|                        COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0)
183|                        - COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0),
184|                        0
185|                    ) * 0.5 AS energia_restringida_mwh,
186|                    NULLIF(REPLACE(val_geracaolimitada::text, ',', '.'), '')::double precision AS geracao_limitada_mwmed,
```

### 3.2 Solar / fotovoltaica

Linhas 204-211:

```py
204|                    COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0) * 0.5 AS geracao_verificada_mwh,
205|                    COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0) * 0.5 AS geracao_referencia_mwh,
206|                    GREATEST(
207|                        COALESCE(NULLIF(REPLACE(val_geracaoreferenciafinal::text, ',', '.'), '')::double precision, NULLIF(REPLACE(val_geracaoreferencia::text, ',', '.'), '')::double precision, 0)
208|                        - COALESCE(NULLIF(REPLACE(val_geracao::text, ',', '.'), '')::double precision, 0),
209|                        0
210|                    ) * 0.5 AS energia_restringida_mwh,
211|                    NULLIF(REPLACE(val_geracaolimitada::text, ',', '.'), '')::double precision AS geracao_limitada_mwmed,
```

Fórmula limpa:

```text
energia_restringida_mwh =
  max(
    (val_geracaoreferenciafinal ou val_geracaoreferencia)
    - val_geracao,
    0
  ) * 0.5
```

Interpretação:

- `val_geracao`: geração verificada, em MWmed.
- `val_geracaoreferenciafinal`: referência final oficial, em MWmed.
- `val_geracaoreferencia`: referência estimada, em MWmed, fallback quando a final não está preenchida.
- `0.5`: conversão de MWmed para MWh em intervalo de 30 minutos.
- `val_geracaolimitada`: fica apenas como metadado diagnóstico, não entra na energia restringida.

Importante: o código retorna MWh, não MW.

O dado original do ONS está em MWmed. Como o intervalo é de 30 minutos, o backend converte para energia:

```text
MWmed * 0.5 hora = MWh
```

---

## 4. Confirmação no domínio: função defensiva

Além do SQL, existe uma função de domínio que documenta e protege a mesma regra:

`backend/app/domain/curtailment_events.py`

Linhas 9-12:

```py
 9|COFF_INTERVAL_HOURS = 0.5
10|COFF_VAL_GERACAOLIMITADA_UNIT = "mwmed"
11|COFF_ENERGY_UNIT_VALIDATED = True
12|COFF_ENERGY_FORMULA = "max((val_geracaoreferenciafinal or val_geracaoreferencia) - val_geracao, 0) * 0.5"
```

Linhas 137-158:

```py
137|def calculate_coff_energy_mwh(row: dict[str, Any], *, fallback_precomputed_is_mwmed: bool = False) -> tuple[float, float | None, float | None]:
138|    """Return curtailed energy for ONS COFF rows.
139|
140|    ONS COFF fields are MWmed for each 30-minute interval. The physical cut is
141|    reference generation minus verified generation, not val_geracaolimitada.
142|    val_geracaolimitada is retained only as diagnostic/source metadata.
143|    """
144|    raw_generation = row.get("val_geracao")
145|    raw_reference = row.get("val_geracaoreferenciafinal")
146|    if raw_reference in (None, ""):
147|        raw_reference = row.get("val_geracaoreferencia")
148|
149|    has_official_coff_fields = raw_generation not in (None, "") and raw_reference not in (None, "")
150|    if has_official_coff_fields:
151|        generation_mwmed = _as_float(raw_generation)
152|        reference_mwmed = _as_float(raw_reference)
153|        restricted_mwh = max(reference_mwmed - generation_mwmed, 0.0) * COFF_INTERVAL_HOURS
154|        return restricted_mwh, generation_mwmed * COFF_INTERVAL_HOURS, reference_mwmed * COFF_INTERVAL_HOURS
155|
156|    precomputed = _as_float(row.get("energia_restringida_mwh"))
157|    energy = precomputed * COFF_INTERVAL_HOURS if fallback_precomputed_is_mwmed else precomputed
158|    return energy, _as_optional_float(row.get("geracao_verificada_mwh")), _as_optional_float(row.get("geracao_referencia_mwh"))
```

Essa função reforça a decisão técnica:

- se vierem os campos oficiais do ONS, calcula com referência menos geração;
- se já vier uma `energia_restringida_mwh` pré-computada, usa esse valor;
- `val_geracaolimitada` não é usado como corte.

---

## 5. Filtro de intervalos válidos

Depois do cálculo energético, o repositório filtra:

`backend/app/repositories/postgres_repo.py`

Linhas 223-230:

```py
223|            SELECT usina_id, timestamp, fonte, geracao_verificada_mwh, geracao_referencia_mwh,
224|                   energia_restringida_mwh, geracao_limitada_mwmed, razao_restricao, cod_razaorestricao,
225|                   origem_restricao AS cod_origemrestricao, origem_restricao, submercado
226|            FROM base
227|            WHERE timestamp BETWEEN :inicio AND :fim
228|              AND cod_razaorestricao IS NOT NULL
229|              AND energia_restringida_mwh > 0
230|              AND (:ne_only = false OR submercado = 'NE')
```

Então, no fluxo detalhado atual, entram apenas intervalos que têm:

- data dentro da janela;
- `cod_razaorestricao` preenchido;
- `energia_restringida_mwh > 0`;
- submercado NE quando o MVP Nordeste está ativo.

---

## 6. Contrato interno do evento energético

Depois que o repositório devolve os dados, eles são convertidos para `ConstrainedOffEvent`.

Arquivo:

`backend/app/domain/contracts.py`

Linhas 8-21:

```py
 8|@dataclass(frozen=True)
 9|class ConstrainedOffEvent:
10|    timestamp: datetime
11|    energia_restringida_mwh: float
12|    razao_restricao: str | None
13|    cod_razaorestricao: str | None
14|    cod_origemrestricao: str | None = None
15|    origem_restricao: str | None = None
16|    usina_id: str | None = None
17|    fonte: str | None = None
18|    geracao_verificada_mwh: float | None = None
19|    geracao_referencia_mwh: float | None = None
20|    geracao_limitada_mwmed: float | None = None
21|    submercado: str | None = None
```

Linhas 65-84:

```py
65|def parse_constrained_off(items: list[dict[str, Any]]) -> list[ConstrainedOffEvent]:
66|    out: list[ConstrainedOffEvent] = []
67|    for e in items:
68|        out.append(
69|            ConstrainedOffEvent(
70|                timestamp=_as_datetime(e.get("timestamp")),
71|                energia_restringida_mwh=_as_float(e.get("energia_restringida_mwh")),
72|                razao_restricao=e.get("razao_restricao"),
73|                cod_razaorestricao=e.get("cod_razaorestricao"),
74|                cod_origemrestricao=e.get("cod_origemrestricao") or e.get("origem_restricao"),
75|                origem_restricao=e.get("origem_restricao"),
76|                usina_id=e.get("usina_id"),
77|                fonte=e.get("fonte"),
78|                geracao_verificada_mwh=_as_float(e.get("geracao_verificada_mwh")) if e.get("geracao_verificada_mwh") is not None else None,
79|                geracao_referencia_mwh=_as_float(e.get("geracao_referencia_mwh")) if e.get("geracao_referencia_mwh") is not None else None,
80|                geracao_limitada_mwmed=_as_float(e.get("geracao_limitada_mwmed")) if e.get("geracao_limitada_mwmed") is not None else None,
81|                submercado=e.get("submercado"),
82|            )
83|        )
84|    return out
```

Aqui o backend carrega:

- energia cortada em MWh;
- geração verificada em MWh;
- geração referência em MWh;
- geração limitada em MWmed apenas como metadado.

---

## 7. Parte financeira: cálculo de quantos reais

A parte financeira principal está em:

`backend/app/services/financeiro_service.py`

Entrada do cálculo:

Linhas 86-99:

```py
 86|    def calcular_perda(self, usina_id: str, inicio: datetime, fim: datetime) -> dict:
...
 94|        usina = self.repo.get_usina(usina_id)
...
 98|        eventos = parse_constrained_off(self.repo.get_constrained_off(usina_id, inicio, fim))
 99|        pld = parse_pld(self.repo.get_pld(usina["submercado"], inicio, fim))
```

Ou seja:

1. Busca eventos COFF já com energia corrigida.
2. Busca PLD do submercado.
3. Calcula perda por intervalo.

Linhas 100-121:

```py
100|        pld_map = {str(p.timestamp): p.pld_reais_mwh for p in pld}
101|        pld_map_hora = {str(p.timestamp.replace(minute=0, second=0, microsecond=0)): p.pld_reais_mwh for p in pld}
...
111|        for e in eventos:
112|            ts = str(e.timestamp)
113|            ts_exato, ts_hora = ts_keys(e.timestamp)
114|            energia = e.energia_restringida_mwh
115|            preco = pld_map.get(ts_exato)
116|            if preco is None:
117|                preco = pld_map_hora.get(ts_hora)
118|            if preco is None:
119|                pld_faltante_intervalos += 1
120|                preco = 0.0
121|            perda = energia * preco
```

Fórmula financeira:

```text
perda_reais = energia_restringida_mwh * pld_reais_mwh
```

Unidade:

```text
MWh * R$/MWh = R$
```

Linhas 123-125 acumulam:

```py
123|            total_perda += perda
124|            total_energia += energia
125|            por_razao[razao] = por_razao.get(razao, 0.0) + perda
```

Linhas 142-148 montam a série por intervalo:

```py
142|            serie.append(
143|                {
144|                    "timestamp": ts,
145|                    "energia_restringida_mwh": round(energia, 4),
146|                    "pld_reais_mwh": round(preco, 4),
147|                    "perda_reais": round(perda, 2),
148|                    "razao_restricao": razao,
```

Linhas 207-211 retornam os totais:

```py
207|        out = {
208|            "usina_id": usina_id,
209|            "total_perda_reais": round(total_perda, 2),
210|            "total_energia_restringida_mwh": round(total_energia, 4),
211|            "por_razao": {k: round(v, 2) for k, v in por_razao.items()},
```

---

## 8. Eventização: intervalo de 30 min vs evento agregado

O cálculo financeiro primeiro calcula cada intervalo de 30 min. Depois agrega intervalos contínuos em eventos de negócio.

Arquivo:

`backend/app/services/financeiro_service.py`

Linhas 155-162:

```py
155|        intervalos = build_curtailment_intervals(
156|            rows_intervalos,
157|            perda_por_intervalo=perda_por_intervalo,
158|            source_table="repo.get_constrained_off",
159|            convert_limited_value_from_mwmed=False,
160|        )
161|        eventos_curtailment = group_intervals_into_events(intervalos)
162|        total_eventos_curtailment = len(eventos_curtailment)
```

O agrupamento fica em:

`backend/app/domain/curtailment_events.py`

Linhas 237-240:

```py
237|def _make_event(intervals: list[CurtailmentInterval], *, gap_detectado: bool = False) -> CurtailmentEvent:
238|    first = intervals[0]
239|    perda_total = sum(i.perda_reais for i in intervals)
240|    status = classify_regulatory_eligibility(first.razao_normalizada, first.origem_normalizada)
```

Ou seja:

- cada linha COFF = intervalo de 30 min;
- evento agregado = sequência contínua de intervalos com mesma usina/fonte/razão/origem;
- perda do evento = soma das perdas dos intervalos.

---

## 9. Parte financeira do pleito de ressarcimento

A perda financeira total e a valoração do pleito são parecidas, mas não são exatamente a mesma coisa.

No Financeiro:

- calcula perda econômica total;
- inclui ENE, REL, CNF etc.;
- não aplica franquia/ressarcibilidade final.

No Pleito:

- pega eventos agregados;
- classifica elegibilidade;
- aplica franquia;
- calcula valor pleiteável.

Arquivo:

`backend/app/services/pleito_service.py`

Linhas 86-97: cálculo de valor por intervalo para alimentar evento agregado:

```py
 86|        for raw in eventos_raw:
 87|            ts = self._as_datetime(raw.get("timestamp"))
 88|            energia = self._as_float(raw.get("energia_restringida_mwh"))
 89|            pld = round(pld_map.get(ts_hour_key(ts), 0.0), 4)
...
 96|            valor_por_intervalo[ts.replace(tzinfo=None).isoformat(sep=" ")] = energia * pld
```

Linhas 98-104: eventização:

```py
 98|        intervalos = build_curtailment_intervals(
 99|            interval_rows,
100|            perda_por_intervalo=valor_por_intervalo,
101|            source_table="repo.get_constrained_off",
102|            convert_limited_value_from_mwmed=False,
103|        )
104|        eventos_agrupados = group_intervals_into_events(intervalos)
```

Linhas 111-114: energia e PLD médio do evento:

```py
111|            duracao = float(evento.duracao_horas or 0.0)
112|            energia = float(evento.energia_restringida_mwh or 0.0)
113|            valor_intervalos = float(evento.perda_total_reais or 0.0)
114|            pld_medio = valor_intervalos / energia if energia > 0 else 0.0
```

Depois aplica franquia:

`backend/app/engine/franquia.py`

Linhas 4-11:

```py
 4|def aplicar_franquia_eventos(eventos: list[dict], franquia_horas: float) -> list[dict]:
 5|    """Aplica franquia anual apenas a eventos REL, preservando ordem temporal."""
...
10|        duracao = float(item.get("duracao_horas") or 1.0)
11|        energia = float(item.get("energia_restringida_mwh") or 0.0)
```

Linhas 16-29:

```py
16|        if not elegivel:
17|            item["status_franquia"] = "nao_aplicavel_inelegivel"
18|            item["status_franquia_label"] = "Não aplicável: evento inelegível"
19|            item["energia_ressarcivel_mwh"] = 0.0
...
23|        if razao != "REL":
24|            item["status_franquia"] = f"nao_aplicavel_{str(razao or 'indefinido').lower()}_termo"
25|            item["status_franquia_label"] = "Não consome franquia anual: compensação por termo/regramento específico fora da franquia REL"
26|            item["energia_ressarcivel_mwh"] = energia
```

Interpretação:

- se evento não é elegível: energia ressarcível = 0;
- se é CNF elegível: não consome franquia REL, energia ressarcível = energia do evento;
- se é REL: aplica franquia anual em horas.

Linhas 31-47:

```py
31|        antes = acumulado
32|        depois = acumulado + duracao
33|        acumulado = depois
...
35|        if depois <= franquia_horas:
36|            item["status_franquia"] = "dentro_franquia"
37|            item["status_franquia_label"] = "Dentro da franquia anual REL"
38|            item["energia_ressarcivel_mwh"] = 0.0
39|        elif antes >= franquia_horas:
40|            item["status_franquia"] = "acima_franquia"
41|            item["status_franquia_label"] = "Acima da franquia anual REL"
42|            item["energia_ressarcivel_mwh"] = energia
43|        else:
44|            frac_acima = (depois - franquia_horas) / duracao if duracao > 0 else 0.0
45|            item["status_franquia"] = "parcialmente_franquia"
46|            item["status_franquia_label"] = "Parcialmente dentro da franquia anual REL"
47|            item["energia_ressarcivel_mwh"] = round(energia * frac_acima, 4)
```

Depois a valoração do pleito fica em:

`backend/app/engine/valoracao.py`

Linhas 4-18:

```py
 4|def valorar_evento(energia_ressarcivel_mwh: float, pld_reais_mwh: float, contratos: list[dict] | None = None) -> dict:
 5|    valor = float(energia_ressarcivel_mwh or 0.0) * float(pld_reais_mwh or 0.0)
...
14|        "valor_pleitavel_reais": round(valor, 2),
15|        "pld_usado_reais_mwh": round(float(pld_reais_mwh or 0.0), 4),
16|        "destinatario_do_ressarcimento": destinatario,
17|        "fonte_valoracao": "CCEE/PLD horário; contratos manuais quando disponíveis",
```

Fórmula do pleito:

```text
valor_pleitavel_reais = energia_ressarcivel_mwh * pld_reais_mwh
```

---

## 10. Elegibilidade técnica/legal usada hoje

Arquivo:

`backend/app/engine/elegibilidade.py`

Canais:

Linhas 9-11:

```py
 9|CANAL_PROTOCOLO_ONS = "PROTOCOLO_ONS"
10|CANAL_TERMO = "TERMO_COMPROMISSO_LEI_15269"
11|CANAL_NENHUM = "NENHUM"
```

Normalização de razão:

Linhas 42-58:

```py
42|    mapa = {
43|        "REL": "REL",
...
50|        "CNF": "CNF",
...
54|        "ENE": "ENE",
...
58|        "RESTRICAO_ENERGETICA": "ENE",
```

Regra de elegibilidade:

Linhas 75-113:

```py
75|def classificar_elegibilidade(razao: str | None, origem: str | None = None, data_evento: date | None = None) -> Elegibilidade:
76|    razao_norm = normalizar_razao_pleito(razao)
77|    origem_norm = (origem or "SIS").strip().upper()
78|
79|    if razao_norm == "ENE":
80|        return Elegibilidade(
81|            elegivel=False,
...
88|    if origem_norm == "LOC":
89|        return Elegibilidade(
90|            elegivel=False,
...
97|    if razao_norm == "REL":
98|        return Elegibilidade(
99|            elegivel=True,
100|            canal_recomendado=CANAL_PROTOCOLO_ONS,
...
102|            fonte_normativa="REN ANEEL 1.030/2022; Procedimentos de Rede ONS Submódulo 5.13",
...
106|    if razao_norm == "CNF":
107|        return Elegibilidade(
108|            elegivel=True,
109|            canal_recomendado=CANAL_TERMO,
...
111|            fonte_normativa="Lei 15.269/2025 art. 1º-B; regulamentação MME/CCEE parametrizável",
```

Regra atual:

- `ENE`: não elegível;
- origem `LOC`: não elegível automático, exige revisão;
- `REL + SIS`: elegível via Protocolo ONS;
- `CNF + SIS`: elegível via Termo/Lei 15.269;
- outros: não elegível automático.

Também existe uma regra de domínio, usada na eventização:

`backend/app/domain/curtailment_events.py`

Linhas 95-106:

```py
 95|def classify_regulatory_eligibility(reason: str | None, origin: str | None) -> str:
 96|    reason_norm = normalize_reason(reason)
 97|    origin_norm = normalize_origin(origin)
 98|    if not reason_norm or not origin_norm:
 99|        return "REVISAO_HUMANA"
100|    if reason_norm in {"CNF", "REL"} and origin_norm == "SIS":
101|        return "ELEGIVEL"
102|    if reason_norm in {"CNF", "REL"} and origin_norm == "LOC":
103|        return "REVISAO_HUMANA"
104|    if reason_norm == "ENE":
105|        return "NAO_ELEGIVEL"
106|    return "REVISAO_HUMANA"
```

---

## 11. Metadados que justificam tecnicamente a fórmula

Documento:

`backend/metadados_curtailiq.md`

Linhas 49-73:

```md
49|## B.1 ONS — COFF Agregada (`restricao_coff_eolica_usi` / `restricao_coff_fotovoltaica`)
...
62|| `val_geracao` | **Geração efetivamente realizada** | FLOAT | **MWmed** | Não |
63|| `val_geracaolimitada` | **Geração limitada por alguma restrição** (teto sob restrição — **NÃO é o corte**) | FLOAT | **MWmed** | Sim |
64|| `val_disponibilidade` | Disponibilidade verificada em tempo real | FLOAT | **MWmed** | Sim |
65|| `val_geracaoreferencia` | Geração de referência (estimada) — o que **teria gerado** | FLOAT | **MWmed** | Sim |
66|| `val_geracaoreferenciafinal` | Geração de referência **final** — base oficial de apuração (preenchida p/ REL) | FLOAT | **MWmed** | Sim |
67|| `cod_razaorestricao` | Razão: **REL** ... **CNF** ... **ENE** ... |
68|| `cod_origemrestricao` | Origem: **LOC** (local), **SIS** (sistêmica) | TEXTO (3) | — | Sim |
...
71|**Energia restringida (cortada) — fórmula correta:**
72|`max((val_geracaoreferenciafinal ou val_geracaoreferencia) − val_geracao, 0) × 0,5`
73|(× 0,5 = MWmed → MWh em intervalo de 30 min). **Não usar `val_geracaolimitada` como corte.**
```

PLD:

Linhas 98-110:

```md
98|## B.3 CCEE — PLD Horário (`pld_horario`)
...
108|| `PLD_HORA` | Preço de Liquidação das Diferenças | NUMÉRICO | **R$/MWh** |
110|**De-para de submercado obrigatório no join:** `SUDESTE→SE_CO`, `SUL→S`, `NORDESTE→NE`, `NORTE→N`.
```

Campos calculados:

Linhas 131-138:

```md
131|| Campo | Cálculo | Regra/Fonte |
133|| `energia_restringida_mwh` | `max(referência_final − geração, 0) × 0,5` | Dicionário ONS + Submódulo 5.13 |
134|| `elegibilidade` / `status` | REL+SIS→elegível ... CNF+SIS→elegível ... ENE/PAR→não; LOC/origem ausente→revisão humana | REN 1.030/2022, 1.073/2023, Lei 15.269/2025 |
136|| `energia_ressarcivel_mwh` | 0 se não elegível; REL: só acima da franquia anual; CNF: energia restringida (estimativa) | — |
137|| `valor_pleitavel_reais` | `energia_ressarcivel_mwh × PLD_horário_do_evento` | ESS valora pelo PLD do período |
138|| franquia (parâmetro) | eólica ⚠️ 78–82h/ano; solar ⚠️ 30,5–41h/ano ... |
```

---

## 12. Testes que garantem a fórmula atual

Arquivo:

`backend/tests/test_curtailment_events_domain.py`

Teste do caso onde há corte real:

Linhas 87-108:

```py
 87|    def test_build_intervals_calculates_coff_energy_from_reference_minus_generation(self):
...
 93|                "val_geracao": 9.038,
 94|                "val_geracaolimitada": 38.0,
 95|                "val_geracaoreferencia": 11.313,
...
104|        self.assertEqual(COFF_INTERVAL_HOURS, 0.5)
105|        self.assertEqual(len(intervals), 1)
106|        self.assertAlmostEqual(intervals[0].energia_restringida_mwh, 1.1375)
107|        self.assertAlmostEqual(intervals[0].geracao_verificada_mwh, 4.519)
108|        self.assertAlmostEqual(intervals[0].geracao_referencia_mwh, 5.6565)
```

Esse teste prova:

```text
(11.313 - 9.038) * 0.5 = 1.1375 MWh
```

Mesmo com `val_geracaolimitada = 38.0`, o código não usa esse valor como corte.

Teste do caso onde não há corte:

Linhas 112-129:

```py
112|    def test_build_intervals_drops_metadata_when_generation_exceeds_reference_even_if_limitada_exists(self):
...
118|                "val_geracao": 23.899,
119|                "val_geracaolimitada": 31.8,
120|                "val_geracaoreferencia": 16.439,
...
127|        intervals = build_curtailment_intervals(rows)
129|        self.assertEqual(intervals, [])
```

Esse teste prova:

```text
max(16.439 - 23.899, 0) * 0.5 = 0
```

Mesmo que `val_geracaolimitada = 31.8`, não há energia cortada.

---

## 13. Exemplo real atual: Sol do Piauí / PISDP1

Cálculo atual no banco real para PISDP1, últimos 90 dias disponíveis:

Período:

- início: `2026-02-28T23:30:00`
- fim: `2026-05-29T23:30:00`

Resultado do `FinanceiroService.calcular_perda`:

```text
total_energia_restringida_mwh = 7980.9990 MWh
total_perda_reais = R$ 572.403,09
total_intervalos_restricao = 1006
total_eventos_curtailment = 136
PLD faltante = 0
```

Por razão:

```text
ENE / energético: R$ 560.781,76
REL / indisponibilidade externa: R$ 10.861,90
CNF / confiabilidade: R$ 759,43
```

Exemplo de intervalo real CNF/SIS:

`2026-03-11 17:00`

O backend retornou:

```text
geracao_verificada_mwh = 4.519
geracao_referencia_mwh = 5.6565
energia_restringida_mwh = 1.1375
geracao_limitada_mwmed = 38.0
cod_razaorestricao = CNF
cod_origemrestricao = SIS
```

A conta é:

```text
val_geracao original = 9.038 MWmed
val_geracaoreferencia = 11.313 MWmed

energia = (11.313 - 9.038) * 0.5
energia = 1.1375 MWh
```

Note que:

```text
val_geracaolimitada = 38.0 MWmed
```

mas esse campo não entra no cálculo da energia cortada.

---

## 14. O que é legal/técnico vs o que é estimativa

Tecnicamente:

- o cálculo de energia cortada está alinhado com os metadados e com a semântica ONS:
  - geração de referência menos geração verificada;
  - clip em zero;
  - conversão MWmed para MWh por 30 min.

Legal/regulatório no MVP:

- `REL + SIS` é tratado como elegível por Protocolo ONS;
- `CNF + SIS` é tratado como elegível por Termo/Lei 15.269;
- `ENE` não é tratado como ressarcível;
- `LOC` não é elegível automático.

Financeiramente:

- perda econômica total:
  - `energia_restringida_mwh * PLD horário`
- valor pleiteável:
  - `energia_ressarcivel_mwh * PLD horário`
  - depois de elegibilidade e franquia.

Ponto importante:

```text
perda econômica total != valor ressarcível
```

A perda econômica inclui todo curtailment calculado.

O pleito filtra:

- razão;
- origem;
- elegibilidade;
- franquia;
- canal regulatório.

---

## 15. Observação importante sobre um campo de display

No `PleitoService`, os eventos de pleito ainda colocam estes campos como zero no payload:

`backend/app/services/pleito_service.py`

Linhas 128-130:

```py
128|                    "geracao_verificada_mwh": 0.0,
129|                    "geracao_referencia_ons_mwh": 0.0,
130|                    "geracao_referencia_mwh": 0.0,
```

Isso não afeta o cálculo da energia nem dos reais, porque a energia já vem de:

```py
112|            energia = float(evento.energia_restringida_mwh or 0.0)
113|            valor_intervalos = float(evento.perda_total_reais or 0.0)
```

Mas é uma inconsistência de metadado/display no payload do pleito: a energia está correta, mas os campos de geração verificada/referência do evento de pleito não estão sendo propagados para exibição.

---

## Conclusão

Hoje o cálculo energético oficial do backend é:

```text
energia_restringida_mwh =
  max(
    (val_geracaoreferenciafinal ou val_geracaoreferencia)
    - val_geracao,
    0
  ) * 0.5
```

Localização principal:

- `backend/app/repositories/postgres_repo.py`
  - linhas 179-186 para eólica;
  - linhas 204-211 para solar;
- `backend/app/domain/curtailment_events.py`
  - linhas 137-158 como regra de domínio defensiva.

A parte financeira é:

```text
perda_reais =
  energia_restringida_mwh * pld_reais_mwh
```

Localização principal:

- `backend/app/services/financeiro_service.py`
  - linhas 98-121 para buscar COFF/PLD e calcular perda por intervalo;
  - linhas 123-125 para acumular total;
  - linhas 142-148 para montar série;
  - linhas 207-211 para retornar total.

Para pleito ressarcível:

```text
valor_pleitavel_reais =
  energia_ressarcivel_mwh * pld_reais_mwh
```

Localização:

- `backend/app/engine/franquia.py`
  - linhas 4-49 para franquia e energia ressarcível;
- `backend/app/engine/valoracao.py`
  - linhas 4-18 para valor em reais;
- `backend/app/services/pleito_service.py`
  - linhas 86-114 para energia/PLD/eventos;
  - linhas 143-178 para franquia, valoração e totais.


---

# Adenda normativa — MPO/RO-AO.BR.13 Rev.09, Submódulo 5.13

Documento lido no projeto:

`backend/_MPO_Documento Normativo_4. Rotinas Operacionais - SM 5.13_4.3. Rotinas Pós-Operação_4.3.2. Apuração de Dados_RO-AO.BR.13_Rev.09.pdf`

## Terminologia correta

O documento usa os termos:

- `Frustração de Geração`: montante energético utilizado para apuração dos Encargos de Serviços do Sistema — ESS, sob responsabilidade da CCEE.
- `Valor de constrained-off eólico e fotovoltaico`: redução da produção de energia por comando do ONS, originada externamente às instalações das usinas/conjuntos.

No produto/código, o campo `energia_restringida_mwh` representa essa energia de constrained-off/frustração calculada por patamar semi-horário. Para evitar ambiguidade de produto, preferir labels como “energia constrained-off / energia restringida” e explicar que, no documento, a grandeza energética usada na apuração ESS é chamada de “Frustração de Geração”.

## Fórmula normativa confirmada

O item 5.2.2.10 define a `Geração de Referência Final (G_Ref_Final)` em etapas:

1. Calcular `G_ref_Disp` como o menor valor entre:
   - Geração de Referência; e
   - Disponibilidade eletromecânica.

2. Verificar o critério de tolerância de 5% ou 5 MW, o que for menor.

3. Se o critério de tolerância for atendido:

```text
G_Ref_Final = G_ref_Disp
```

4. Se o critério de tolerância não for atendido:

```text
G_Ref_Final = G_ref_Disp - (Geração Limitada - Geração Verificada)
```

5. Se o resultado for menor que zero:

```text
G_Ref_Final = 0
```

Portanto, `val_geracaoreferenciafinal` é referência final ajustada pelo ONS, não a energia/frustração diretamente.

A energia constrained-off/frustração por patamar semi-horário deve ser:

```text
energia_restringida_mwh = max(val_geracaoreferenciafinal - val_geracao, 0) * 0,5
```

Quando `val_geracaoreferenciafinal` estiver ausente, o uso de `val_geracaoreferencia` como fallback deve ser marcado como estimativa operacional:

```text
energia_restringida_mwh_estimada = max(val_geracaoreferencia - val_geracao, 0) * 0,5
```

## Papel da Geração Limitada

`val_geracaolimitada` é a limitação de geração solicitada pelo ONS em tempo real. Ela pode entrar indiretamente no cálculo oficial da `G_Ref_Final`, conforme item 5.2.2.10, mas não deve ser usada diretamente como energia cortada.

## Exemplo normativo

Se:

```text
Geração de Referência = 150 MWmed
Disponibilidade = 200 MWmed
Geração Limitada = 100 MWmed
Geração Verificada = 94 MWmed
```

Então:

```text
G_ref_Disp = min(150, 200) = 150
G_Ref_Final = 150 - (100 - 94) = 144 MWmed
energia_restringida_mwh = max(144 - 94, 0) * 0,5 = 25 MWh
```

Se o campo `val_geracaoreferenciafinal` viesse como 50 MWmed e `val_geracao` fosse 94 MWmed, então pela definição normativa de `G_Ref_Final` não haveria energia restringida:

```text
max(50 - 94, 0) * 0,5 = 0 MWh
```

## Metadados implementados no backend

Para distinguir apuração com referência final ONS de estimativa por fallback, o backend passa a expor:

```text
referencia_oficial: true/false
referencia_calculo_curtailment:
  - geracao_referencia_final_mpo_5_13
  - geracao_referencia_estimativa_fallback
  - energia_restringida_precomputada
```

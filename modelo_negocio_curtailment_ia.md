# CurtailIQ — Inteligência de Curtailment para Geradores Renováveis

### Descritivo de Modelo de Negócio — EnergINNthon
*Plataforma e agentes de IA que transformam o corte de geração renovável de prejuízo silencioso em decisão gerenciável: do evento físico de corte à posição financeira e ao pleito regulatório.*

---

## 1. O Problema

O Brasil construiu uma das matrizes mais limpas do mundo, mas não consegue usar tudo que ela gera. Quando sobra energia solar e eólica — porque o sol está forte ao meio-dia, o vento sopra de madrugada, a demanda está baixa, ou a linha de transmissão não dá conta de escoar — o Operador Nacional do Sistema (ONS) manda *desligar* usinas renováveis. Esse corte forçado se chama **curtailment** (ou *constrained-off*).

O que era um ajuste operacional marginal virou uma sangria estrutural. O percentual de geração renovável cortada saltou de 3,6% (2023) para 9,3% (2024) e para **20,6% em 2025** — mais de seis vezes o patamar de sistemas elétricos maduros (1% a 3%). Em 2025 isso significou cerca de R$6,5 bilhões de prejuízo distribuídos por aproximadamente 1.500 usinas centralizadas. As solares foram as mais penalizadas (média de ~35% de corte; as eólicas, ~15%). Em 2026 o problema não cedeu: só no primeiro quadrimestre já foram cortados quase 3 GW médios, agora liderados por **sobreoferta** ("razão energética"), que sozinha respondeu por ~1,77 GW médios.

O dano transcende o MWh perdido. O corte vira **exposição financeira ao mercado de curto prazo** (a usina não entrega o contratado e precisa se cobrir ao PLD horário), **degrada a garantia física** do empreendimento, e desencadeia uma **briga regulatória** sobre quem paga a conta. O resultado macro é assustador: cerca de R$38,8 bilhões em investimentos suspensos no Nordeste entre 2025 e 2026, 141 usinas devolveram outorgas em 2025, e o mercado solar encolheu 29% no ano.

---

## 2. A Dor (e a dor oculta)

**Dor explícita — o gerador sabe que sangra, mas não sabe quantificar nem reagir a tempo.**
O produtor recebe a instrução de corte do ONS e assiste à geração ser desligada. No fim do mês, descobre o estrago somado na contabilização da CCEE — tarde demais para agir. Ele não tem, hoje, uma ferramenta que diga *em tempo quase real*: quanto perdi, por quê fui cortado, e o que isso fez com a minha posição contratual.

**Dor oculta 1 — a classificação do corte é dinheiro, e quase ninguém faz bem.**
Nem todo corte dá direito a ressarcimento. A regra (REN ANEEL 1.030/2022, e agora a Lei 15.269/2025) só compensa cortes por *indisponibilidade externa* e *confiabilidade elétrica* — e exclui *razão energética* (sobreoferta), que é justamente a fatia que mais cresce. Classificar corretamente cada evento, hora a hora, usina por usina, e montar o dossiê probatório é um trabalho técnico-jurídico penoso. Cada evento mal classificado ou mal documentado é receita de ressarcimento perdida. Com o veto ao ressarcimento amplo na Lei 15.269/2025, o rigor dessa classificação ficou *mais* valioso, não menos.

**Dor oculta 2 — o corte é um problema financeiro disfarçado de problema operacional.**
Quando a usina é cortada, a posição de hedge do gerador se desajusta: ele vendeu energia que não vai entregar e fica exposto ao PLD. Re-equilibrar a carteira, ajustar a sazonalização da garantia física e decidir o despacho exigem uma resposta rápida que hoje é feita em planilhas, no susto, depois do fato.

**Dor oculta 3 — a decisão de investir em bateria (BESS) é tomada às cegas.**
Com o primeiro leilão de armazenamento do Brasil (LRCAP 2026) na mesa, todo gerador precisa decidir se entra. Mas dimensionar uma bateria exige saber *exatamente* o padrão de corte da usina — quando, quanto, por quê. Esse business case técnico hoje depende de consultoria cara e demorada.

---

## 3. Proposta de Valor

> **Transformamos o curtailment de prejuízo invisível em decisão gerenciável.** Um único cérebro de dados que conecta o corte físico à perda financeira e ao pleito regulatório — antecipando o corte, quantificando o dano em tempo real, maximizando o ressarcimento elegível e embasando a próxima decisão de investimento.

Para o **gerador renovável** (eólica, solar, e quem avalia BESS), a CurtailIQ entrega quatro ganhos diretos:

1. **Antecipar** — saber, com horas a dias de antecedência, a probabilidade e a magnitude de corte de cada usina, para poder negociar, deslocar despacho ou operar bateria.
2. **Quantificar** — medir a perda financeira de cada evento (MWh cortados × PLD horário + impacto na garantia física) sem esperar o fechamento mensal da CCEE.
3. **Recuperar** — classificar automaticamente cada corte por motivação regulatória, identificar o que é ressarcível e gerar o dossiê de pleito pronto.
4. **Decidir** — usar o histórico real de corte para dimensionar bateria, avaliar o leilão de BESS e re-hedgear a carteira.

**O que nos diferencia:** existe forecasting de geração (Steadysun, Solcast, o próprio ONS) e existe gestão de ativos/O&M (Delfos, Power Factors) e ETRM (Thunders). Mas *ninguém* empacotou, como produto self-service, a inteligência que liga o evento de corte → perda financeira → pleito regulatório. A Volt Robotics, que mais entende do tema, atua como **consultoria** — o que prova a dor e deixa o espaço de produto aberto.

---

## 4. A Solução — Arquitetura em Três Elos

A solução é uma plataforma com uma camada de modelos de ML e uma camada de agentes de IA, organizada em três elos que seguem a jornada da dor: do físico ao financeiro ao regulatório. O clima entra como *insumo* — não como produto.

### Elo 1 — Físico/Preditivo (núcleo de Machine Learning)
**Pergunta que responde:** "Quanto vou gerar, e qual a chance de eu ser cortado?"

- **Modelo de risco de curtailment:** prevê probabilidade e magnitude de corte por usina nas próximas 24–48h. Não é um modelo meteorológico próprio (terreno saturado e caro) — é um modelo que *consome* previsão climática aberta como uma de várias features.
- **Features:**
  - *Climáticas (abertas):* irradiância e velocidade do vento previstas (ex.: Open-Meteo), temperatura (proxy de demanda), via API gratuita.
  - *De rede/operação:* geração programada do DESSEM, restrições por submercado, histórico de constrained-off por usina (ONS).
  - *De mercado:* PLD horário e sua trajetória (CCEE).
  - *Estruturais:* fonte, potência e localização da usina (SIGA/ANEEL), sazonalidade, perfil de demanda regional.
- **Saída:** um "índice de risco de corte" por usina e por hora, com a magnitude esperada em MWh.

### Elo 2 — Financeiro (otimização e gestão de risco)
**Pergunta que responde:** "O que o corte fez (e vai fazer) com a minha posição, e como reajo?"

- **Quantificador de perda em tempo quase real:** valora cada evento de corte (MWh × PLD horário) e estima o impacto acumulado na garantia física.
- **Motor de exposição e hedge:** projeta a exposição ao mercado de curto prazo decorrente dos cortes e simula cenários de re-hedge e sazonalização (Monte Carlo sobre cenários de PLD).
- **Business case de BESS:** usa o padrão de corte real da usina (Elo 1) para dimensionar bateria, simular o retorno e avaliar a participação no leilão de armazenamento — respondendo "guardar essa energia compensa?".
- *Natureza:* mistura de ML (otimização, simulação de cenários) e regras de negócio.

### Elo 3 — Regulatório (agentes de IA)
**Pergunta que responde:** "O que posso recuperar, e como provo isso para a CCEE/ANEEL?"

- **Agente classificador de cortes:** lê os datasets de constrained-off do ONS e rotula cada evento por motivação regulatória (indisponibilidade externa / confiabilidade elétrica / razão energética), marcando a elegibilidade de ressarcimento sob a REN 1.030/2022 e a Lei 15.269/2025.
- **Agente de dossiê de pleito:** monta automaticamente o relatório probatório de ressarcimento para os eventos elegíveis (evento, horário, MWh, valoração, enquadramento regulatório).
- **Agente regulatório (RAG):** mantém o gerador atualizado sobre mudanças nas regras de comercialização, consultas públicas (CP 45/2019, CP 009/2026) e prazos da CCEE, respondendo dúvidas com base na norma vigente.
- *Natureza:* agentes de IA integrados a dados e documentos, com humano no loop antes de qualquer submissão.

---

## 5. O MVP do Hackathon

**Objetivo:** provar a tese de ponta a ponta com dados abertos reais (sem depender de dado sintético no caminho crítico), usando uma ou duas usinas reais do Nordeste como estudo de caso.

**Escopo construível no evento (os três elos, em versão enxuta):**

| Elo | Entregável no MVP | Fonte de dados (aberta) |
|-----|-------------------|--------------------------|
| 1 — Físico/ML | Modelo que prevê risco de corte 24–48h para a usina-caso, com features climáticas + rede + mercado | ONS (constrained-off por usina, geração, DESSEM), Open-Meteo, CCEE (PLD), SIGA/ANEEL |
| 2 — Financeiro | Cálculo da perda por evento (MWh × PLD) e painel de exposição; mini business case de BESS para a usina-caso | ONS + CCEE (PLD horário) |
| 3 — Regulatório | Agente que classifica cada corte por motivação e gera um dossiê de pleito automático; agente RAG sobre as regras | ONS + base normativa (REN 1.030/2022, Lei 15.269/2025) |

**Demonstração (fluxo do pitch):**
1. Seleciona-se uma usina real do Nordeste com alto histórico de corte.
2. A plataforma ingere os CSVs do ONS e o PLD da CCEE e mostra: *"esta usina perdeu R$ X em 2025 com curtailment"* — número real, calculado na hora.
3. O agente classifica os cortes e mostra: *"R$ Y deste total era potencialmente ressarcível; aqui está o dossiê"*.
4. O modelo de ML projeta o risco de corte para as próximas 48h.
5. O módulo de BESS responde: *"uma bateria de Z MW recuperaria W% dessa perda — vale o leilão?"*.

**Por que é defensável:** cada número no palco vem de dado público verificável. A previsão climática é insumo via API aberta, não um modelo meteorológico que precisaríamos validar. O dado sintético, se usado, aparece só onde seria naturalmente privado do cliente (ex.: estrutura exata da carteira de contratos), sempre calibrado por dados reais e declarado no pitch.

**Divisão sugerida para o time de 5 (DS/IA, ML, back, front, banco + agentes):**
- Engenharia de dados/banco: pipelines de ingestão ONS/CCEE/SIGA/Open-Meteo.
- ML: modelo de risco de corte (Elo 1) e simulação financeira (Elo 2).
- Agentes de IA: classificador regulatório e RAG (Elo 3).
- Back-end: API que orquestra modelos + agentes.
- Front-end: dashboard do estudo de caso e narrativa do pitch.

---

## 6. Produto e Roadmap (a visão de startup)

**MVP (hackathon):** prova de conceito de inteligência de curtailment sobre dados abertos, com os três elos em versão demonstrável.

**Pós-evento (PoC com uma geradora):** integração de dados privados (medição, carteira de contratos) ao motor já validado em dados abertos — o que aumenta a precisão sem mudar a arquitetura.

**Expansão natural:**
- *Operação de BESS:* quando as baterias do leilão 2026 entrarem (suprimento a partir de ago/2028), o mesmo cérebro passa a otimizar o despacho de carga/descarga — de ferramenta de *business case* a ferramenta de *operação*.
- *Plataforma de gestão de carteira:* aprofundar o Elo 2 rumo a um ETRM leve, focado em renováveis expostas a curtailment.
- *Camada de demanda:* conectar a energia hoje desperdiçada a novas cargas (indústria eletrointensiva, hidrogênio verde, data centers instalados estrategicamente) — aderência aos pilares Descentralização/Diversificação, como visão de longo prazo.

**Encaixe nos pilares do evento:** Descarbonização (evita o desperdício de energia limpa já gerada), Digitalização (núcleo de ML + agentes de IA), e Democratização (transparência sobre dados públicos que hoje só consultorias caras decifram).

---

## 7. Riscos e Sensibilidades (honestidade que fortalece o pitch)

- **Risco regulatório:** se o Congresso reverter o veto ao ressarcimento amplo da Lei 15.269/2025, o ângulo "maximizar pleito" perde força — e o produto pivota para prevenção/otimização e operação de bateria, que seguem valiosas.
- **Risco competitivo:** se a Delfos ou a Volt lançarem um módulo dedicado de ressarcimento, a diferenciação precisa migrar para a integração dos três elos (a maioria dos concorrentes faz só um).
- **Risco de dado:** a precisão fina do Elo 1 melhora muito com dado privado de medição; o MVP prova a tese com dado aberto, mas a versão comercial depende da PoC com geradora.
- **Procedência dos números:** as cifras de prejuízo (R$6,5 bi, 20,6%) vêm majoritariamente da Volt Robotics e das associações de geradores (Absolar/ABEEólica), corroboradas pela XP — no MVP, recalculamos a partir do dado primário do ONS para blindar a narrativa.

---

*Documento de trabalho para validação do time. Os dados de mercado refletem o levantamento de maio de 2026 e devem ser reconfirmados contra as fontes primárias (ONS, CCEE, ANEEL) e contra o regulamento oficial do evento antes do pitch final.*

# CurtailIQ — Predição de Curtailment para Geradores Renováveis

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green)
![TypeScript](https://img.shields.io/badge/TypeScript-Frontend-blue)
![Machine Learning](https://img.shields.io/badge/Machine%20Learning-Curtailment-orange)
![Energy](https://img.shields.io/badge/Energy-Renewables-yellow)
![Status](https://img.shields.io/badge/Status-MVP%20Hackathon-purple)

Projeto finalista do **EnergINNthon | A Maratona de Inovação do Setor de Energia**, desenvolvido no contexto do **Energy Summit Global**, evento global voltado à inovação, empreendedorismo, energia e sustentabilidade, realizado em colaboração com o **Massachusetts Institute of Technology (MIT)**.

O **CurtailIQ** é uma solução de inteligência aplicada ao setor elétrico brasileiro, criada para prever, quantificar e apoiar decisões relacionadas ao **curtailment** — o corte de geração renovável causado por restrições operacionais, sobreoferta de energia ou limitações de transmissão.

> Reagir. Ressarcir. Investir.

---

## Sumário

- [Sobre o projeto](#sobre-o-projeto)
- [Contexto do evento](#contexto-do-evento)
- [Problema](#problema)
- [Solução](#solução)
- [Arquitetura em três elos](#arquitetura-em-três-elos)
- [Minha contribuição](#minha-contribuição)
- [Arquitetura técnica](#arquitetura-técnica)
- [Stack utilizada](#stack-utilizada)
- [Fontes de dados](#fontes-de-dados)
- [Cálculo de curtailment](#cálculo-de-curtailment)
- [Endpoints principais](#endpoints-principais)
- [Como executar localmente](#como-executar-localmente)
- [Variáveis de ambiente](#variáveis-de-ambiente)
- [Roadmap](#roadmap)
- [Equipe](#equipe)
- [Status do projeto](#status-do-projeto)
- [Referências](#referências)

---

## Sobre o projeto

O Brasil vem expandindo rapidamente sua matriz renovável, especialmente com o crescimento da geração solar e eólica. Porém, parte dessa energia limpa não consegue ser aproveitada devido a restrições do sistema elétrico.

Quando há excesso de geração, baixa demanda, restrição de transmissão ou necessidade de segurança operacional, o Operador Nacional do Sistema Elétrico pode determinar o corte da geração de usinas renováveis. Esse evento é conhecido como **curtailment** ou **constrained-off**.

O **CurtailIQ** foi criado para transformar esse problema em uma decisão gerenciável, conectando dados públicos, engenharia de dados, modelos de previsão, análise financeira e inteligência regulatória.

A proposta é responder a três perguntas centrais para geradores renováveis:

1. **Quanto estou perdendo com curtailment?**
2. **O que pode ser ressarcido?**
3. **Vale investir em bateria para reduzir perdas futuras?**

---

## Contexto do evento

Este projeto foi desenvolvido durante o **EnergINNthon | A Maratona de Inovação do Setor de Energia**, como parte do ecossistema de inovação do **Energy Summit Global**.

O **Energy Summit Global** é um evento voltado à discussão do futuro da energia, inovação, empreendedorismo, sustentabilidade e transição energética, realizado em colaboração com o **MIT — Massachusetts Institute of Technology**.

O CurtailIQ foi selecionado como **projeto finalista** da maratona.

---

## Problema

O curtailment afeta diretamente geradores solares, eólicos e híbridos.

Quando uma usina é obrigada a reduzir ou interromper sua geração, surgem impactos relevantes:

- perda de receita;
- exposição ao PLD;
- dificuldade de ressarcimento;
- incerteza regulatória;
- perda de previsibilidade financeira;
- dificuldade para justificar investimentos em armazenamento;
- tomada de decisão baseada em planilhas e análises manuais.

O problema não é apenas operacional. Ele também é financeiro, regulatório e estratégico.

Hoje, muitos geradores sabem que estão perdendo energia e receita, mas não possuem uma plataforma integrada para antecipar cortes, calcular perdas, avaliar ressarcimento e simular alternativas como baterias.

---

## Solução

O **CurtailIQ** é uma plataforma de inteligência para curtailment que integra:

- predição de risco de corte;
- cálculo de energia restringida;
- cálculo de perda financeira;
- análise de exposição ao PLD;
- classificação regulatória dos eventos;
- geração de dossiês de ressarcimento;
- simulação de baterias BESS;
- dashboard para apoio à decisão.

A solução foi pensada como um produto para:

- geradores de energia solar;
- geradores de energia eólica;
- geradores híbridos;
- asset managers de energia;
- investidores em BESS;
- consultorias regulatórias;
- comercializadoras de energia.

---


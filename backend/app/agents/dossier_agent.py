from __future__ import annotations

import json


class DossierAgent:
    def __init__(self, llm_client, model: str):
        self.llm_client = llm_client
        self.model = model

    def gerar_dossie(self, payload: dict) -> str:
        system = (
            "Você é redator técnico-jurídico do setor elétrico e deve produzir minuta formal de pleito de ressarcimento por constrained-off. "
            "Escreva em português do Brasil, com linguagem jurídica clara, objetiva e impessoal. "
            "Use texto organizado para leitura humana (sem tabelas markdown complexas). "
            "Siga obrigatoriamente este modelo-base: "
            "I. Qualificação da usina e identificação do período; "
            "II. Síntese executiva do pleito; "
            "III. Quadro de perdas por razão de restrição (com valores e percentuais); "
            "IV. Fundamentação regulatória (REN 1.030/2022 e Lei 15.269/2025); "
            "V. Memória de cálculo (premissas, franquia, valor potencial e pós-franquia); "
            "VI. Pedidos e requerimentos; "
            "VII. Lista de anexos e evidências recomendadas. "
            "Regra crítica: trate os dados numéricos do payload como fonte prioritária e vinculante para o texto. "
            "NUNCA escreva 'informação indisponível' para campos que existirem no payload com valores numéricos. "
            "Diferencie explicitamente histórico vs previsão futura (30 dias) usando os campos de resumo_financeiro quando presentes."
        )
        user = f"Dados para o dossiê: {payload}"
        return self.llm_client.complete(system=system, user=user, model=self.model, max_tokens=1600)

    def gerar_pleito_evento(self, pacote_estruturado: dict, template_markdown: str) -> str:
        """Refina a redação do pleito por evento; se LLM estiver indisponível, retorna o template auditável."""
        system = """Você é um redator técnico-regulatório especializado em pleitos de ressarcimento de
constrained-off de usinas eólicas e fotovoltaicas no setor elétrico brasileiro. Seu
papel é redigir um documento formal a partir de um pacote estruturado de dados já
classificado, calculado e validado.

REGRAS INVIOLÁVEIS:
1. NUNCA recalcule valores, horas, energia ou elegibilidade. Os números vêm prontos
   no pacote — use-os exatamente como estão. Se algum campo estiver ausente,
   escreva "[campo ausente — preencher]" e siga.
2. NUNCA invente normas, artigos, números de resolução, prazos ou cargos. Use
   somente o que estiver em `fundamentacao_normativa` e `destinatario` do pacote.
3. NUNCA submeta nada a lugar nenhum. Seu output é um RASCUNHO para revisão humana.
   Termine o documento com "— Documento gerado como rascunho. Revisão humana
   obrigatória antes de protocolo."
4. Escreva em português formal brasileiro, em primeira pessoa do plural, objetivo, sem floreio.
5. Não use markdown decorativo. Use estrutura clara: cabeçalho, seções numeradas, tabela de eventos, conclusão, anexos.
6. Para cada evento listado, NUNCA omita o `evento_id`.
7. Se houver `reconciliacao.houve_comparacao = true`, destaque o `argumento_tecnico`.
8. Declare explicitamente o destinatário do ressarcimento informado no pacote.
9. Não emita opinião jurídica nem cite concorrentes. Atenha-se aos fatos técnicos e à norma citada no pacote.
"""
        user = (
            "Use o template abaixo como estrutura mínima obrigatória. Preserve todos os campos numéricos.\n\n"
            f"TEMPLATE:\n{template_markdown}\n\n"
            "Eis o pacote de dados:\n```json\n"
            f"{json.dumps(pacote_estruturado, ensure_ascii=False, indent=2)}\n```\n"
            "Gere o documento conforme as regras."
        )
        try:
            out = self.llm_client.complete(system=system, user=user, model=self.model, max_tokens=4000)
        except Exception:
            return template_markdown
        # AnthropicClient sem chave retorna JSON mock; para a demo, o template determinístico é melhor.
        try:
            parsed = json.loads(out)
            if isinstance(parsed, dict) and parsed.get("message") == "anthropic_disabled":
                return template_markdown
        except Exception:
            pass
        if not out or len(out.strip()) < 80:
            return template_markdown
        return out

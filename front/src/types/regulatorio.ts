export interface QualidadeClassificacao {
  eventos_totais: number
  eventos_classificados_por_ia: number
  eventos_com_razao_gold: number
}

export interface QualidadeDados {
  status: string
  pld_faltante_eventos: number
  eventos_sem_razao_original: number
  eventos_com_razao_normalizada: number
  total_eventos: number
}

export interface EventoElegivel {
  timestamp: string
  razao_restricao: string
  energia_restringida_mwh: number
  elegivel_ressarcimento: boolean
  valor_potencial_reais: number
  valor_ressarcivel_pos_franquia_reais: number
  dentro_franquia: boolean
  classificacao_fonte: "gold" | "ia"
  classificacao_confianca: number
  classificacao_justificativa: string
  auditoria_regra: string
  auditoria_motivo_status: string
  auditoria_detalhe: string
}

export interface ElegibilidadeOut {
  usina_id: string
  total_potencial_ressarcivel_reais: number
  total_ressarcivel_pos_franquia_reais: number
  franquia_horas_ano: number
  horas_elegiveis_no_periodo: number
  horas_excedentes_franquia_no_periodo: number
  qualidade_classificacao: QualidadeClassificacao
  qualidade_dados: QualidadeDados
  metadata: Record<string, unknown>
  paginacao_eventos: { total_count: number; limit: number; offset: number }
  eventos: EventoElegivel[]
}

export interface DossieRequest {
  inicio: string
  fim: string
}

export interface DossieOut {
  usina_id: string
  dossie_markdown: string
}

export interface DossieExportRequest {
  inicio: string
  fim: string
  formato: "markdown" | "json"
  franquia_horas_override?: number
}

export interface DossieExportOut {
  usina_id: string
  formato: string
  file_name: string
  content_type: string
  content: string
}

export interface FluxoRessarcimentoRequest {
  inicio: string
  fim: string
  franquia_horas_override?: number
}

export interface FluxoRessarcimentoOut {
  usina_id: string
  periodo: { inicio: string; fim: string }
  selecao: { fonte_eventos: string; eventos_totais: number; eventos_elegiveis?: number }
  reconciliacao: {
    energia_total_mwh: number
    perda_total_reais: number
    potencial_ressarcivel_reais: number
    ressarcivel_pos_franquia_reais: number
    pld_faltante_eventos: number
    eventos_sem_razao_original: number
  }
  etapas: string[]
  resultado_elegibilidade: ElegibilidadeOut
  dossie_markdown: string
  human_in_the_loop: {
    submissao_automatica_habilitada: boolean
    acao_recomendada: string
  }
  metadata: Record<string, unknown>
}

export interface ConsultaRequest {
  pergunta: string
}

export interface ConsultaOut {
  resposta: string
  fontes: string[]
}

export interface ApiError {
  code: string
  detail: string
}

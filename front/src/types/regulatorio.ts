export interface QualidadeClassificacao {
  eventos_totais: number
  eventos_classificados_por_ia: number
  eventos_com_razao_gold: number
}

export interface EventoElegivel {
  timestamp: string
  razao_restricao: string
  energia_restringida_mwh: number
  elegivel_ressarcimento: boolean
  valor_potencial_reais: number
  classificacao_fonte: "gold" | "ia"
  classificacao_confianca: number
  classificacao_justificativa: string
}

export interface ElegibilidadeOut {
  usina_id: string
  total_potencial_ressarcivel_reais: number
  qualidade_classificacao: QualidadeClassificacao
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

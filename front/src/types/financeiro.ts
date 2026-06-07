export interface QualidadeDados {
  status: "completo" | "parcial" | "sem_pld"
  pld_faltante_eventos: number
  total_eventos: number
}

export interface SeriePerdaItem {
  timestamp: string
  energia_restringida_mwh: number
  pld_reais_mwh: number
  perda_reais: number
  razao_restricao: string
}

export interface PerdaOut {
  usina_id: string
  total_perda_reais: number
  total_energia_restringida_mwh: number
  por_razao: Record<string, number>
  qualidade_dados: QualidadeDados
  serie: SeriePerdaItem[]
}

export interface ExposicaoPremissas {
  energia_media_restringida_mwh_por_hora: number
  pld_medio_reais_mwh: number
  metodo: string
}

export interface ExposicaoOut {
  usina_id: string
  horizonte_horas: number
  exposicao_estimada_reais: number
  premissas: ExposicaoPremissas
}

export interface BessRequest {
  potencia_mw: number
  duracao_horas: number
  eficiencia: number
  capex?: number
}

export interface BessOut {
  usina_id: string
  energia_recuperada_mwh: number
  receita_recuperada_reais: number
  percentual_mitigado: number
  capex?: number
  payback_anos?: number
  dimensionamento_com_previsao?: {
    tipo_dado: "previsao"
    horizonte_dias?: number
    metodo_previsao: string
    energia_perdida_prevista_mwh: number
    energia_recuperavel_prevista_mwh: number
    perda_financeira_evitavel_prevista_reais: number
  }
}


export interface QualidadeDados {
  status: "completo" | "parcial" | "sem_pld"
  pld_faltante_eventos: number
  total_eventos: number
  pld_faltante_intervalos?: number
  total_eventos_curtailment?: number
  total_intervalos_restricao?: number
  eventos_sem_origem?: number
  energia_unidade_validada?: boolean
  referencia_oficial_intervalos?: number
  referencia_estimativa_intervalos?: number
}

export interface SeriePerdaItem {
  timestamp: string
  energia_restringida_mwh: number
  pld_reais_mwh: number
  perda_reais: number
  razao_restricao: string
  cod_razaorestricao?: string | null
  cod_origemrestricao?: string | null
  referencia_oficial?: boolean | null
  referencia_calculo_curtailment?: string | null
  nivel_semantico?: string | null
}

export interface EventoCurtailmentItem {
  event_id: string
  usina_id: string
  inicio: string
  fim: string
  duracao_horas: number
  n_intervalos: number
  energia_restringida_mwh: number
  perda_total_reais: number
  cod_razaorestricao?: string | null
  cod_origemrestricao?: string | null
  referencia_oficial?: boolean | null
  referencia_calculo_curtailment?: string | null
  razao_normalizada?: string | null
  origem_normalizada?: string | null
  elegibilidade_status: string
  evidence_score: number
  source_interval_ids: string[]
  gap_detectado?: boolean
}

export interface PerdaOut {
  usina_id: string
  total_perda_reais: number
  total_energia_restringida_mwh: number
  por_razao: Record<string, number>
  qualidade_dados: QualidadeDados
  eventos?: EventoCurtailmentItem[]
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
    metadados_previsao?: Record<string, unknown>
  }
}

export interface PrevisaoPerdasSerieItem {
  timestamp: string
  energia_mwh: number
  pld_reais_mwh: number
  perda_reais: number
  tipo_dado: "historico" | "previsao"
  prob_corte?: number
}

export interface PrevisaoPerdasOut {
  usina_id: string
  metodo_previsao: string
  horizonte_horas: number
  historico_horas: number
  resumo: {
    perda_historica_reais: number
    perda_prevista_reais: number
    energia_historica_mwh: number
    energia_prevista_mwh: number
  }
  serie_historico: PrevisaoPerdasSerieItem[]
  serie_previsao: PrevisaoPerdasSerieItem[]
}


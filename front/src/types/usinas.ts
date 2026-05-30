export interface UsinaOut {
  usina_id: string
  nome: string
  fonte: "solar" | "eolica"
  potencia_mw: number
  submercado: string
}

export interface UsinaListOut {
  total_count: number
  limit: number
  offset: number
  items: UsinaOut[]
}

export interface RiscoHora {
  timestamp: string
  probabilidade_corte: number
  magnitude_estimada_mwh: number
}

export interface UsinaResumoOut {
  usina: UsinaOut
  total_corte_mwh: number
  total_perda_reais: number
  percentual_ressarcivel: number
  total_eventos_corte: number
  ticket_medio_evento_reais: number
  risco_48h: RiscoHora[]
}

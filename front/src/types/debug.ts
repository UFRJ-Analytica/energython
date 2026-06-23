export interface DebugKpiOut {
  label: string
  value: number | string
  unit?: string | null
  description?: string | null
}

export interface DebugUsinaScoreOut {
  usina_id: string
  nome: string
  fonte?: string | null
  submercado?: string | null
  potencia_mw?: number | null
  latitude?: number | null
  longitude?: number | null
  total_corte_mwh: number
  total_perda_reais: number
  percentual_corte: number
  percentual_ressarcivel: number
  fator_capacidade?: number | null
  health_score: number
}

export interface DebugHealthDadosOut {
  status: string
  repository: string
  total_usinas_amostra: number
  observacoes: string[]
  amostra_usinas: Record<string, unknown>[]
}

export interface DebugControlTowerOut {
  kpis: DebugKpiOut[]
  ranking: DebugUsinaScoreOut[]
  metadata: Record<string, unknown>
}

export interface DebugRankingOut {
  melhores: DebugUsinaScoreOut[]
  piores: DebugUsinaScoreOut[]
  metadata: Record<string, unknown>
}

export interface DebugUnidadesOut {
  kpis: DebugKpiOut[]
  unidades: DebugUsinaScoreOut[]
  metadata: Record<string, unknown>
}

export interface DebugSeriePointOut {
  timestamp: string
  geracao_mwh: number
  referencia_mwh?: number | null
  corte_mwh: number
  cod_razaorestricao?: string | null
  cod_origemrestricao?: string | null
}

export interface DebugUsinaDetalheOut {
  usina: Record<string, unknown>
  kpis: DebugKpiOut[]
  serie_amostra: DebugSeriePointOut[]
  score: DebugUsinaScoreOut
  metadata: Record<string, unknown>
}

export interface DebugAnomaliaOut extends DebugSeriePointOut {
  score_anomalia: number
  metodo: string
}

export interface DebugAnomaliasOut {
  usina_id: string
  total_pontos: number
  total_anomalias: number
  metodo: string
  anomalias: DebugAnomaliaOut[]
}

export interface DebugForecastPointOut {
  timestamp: string
  real_mwh?: number | null
  baseline_mwh?: number | null
  forecast_mwh: number
  p10_mwh?: number | null
  p90_mwh?: number | null
}

export interface DebugForecastOut {
  usina_id: string
  modelo: string
  horizonte: number
  mae_baseline?: number | null
  mae_hibrido?: number | null
  ganho_pct?: number | null
  pontos: DebugForecastPointOut[]
  feature_importance: Record<string, unknown>[]
}

export interface DebugNoticiaOut {
  titulo: string
  link: string
  data?: string | null
  fonte?: string | null
  relevancia: number
  resumo?: string | null
}

export interface DebugNoticiasOut {
  usina_id: string
  consulta: string
  total_bruto: number
  itens: DebugNoticiaOut[]
  erro?: string | null
  metadata: Record<string, unknown>
}

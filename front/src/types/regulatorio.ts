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
  classificacao_fonte: "gold" | "ia" | "regra_default"
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

export interface ReconciliacaoPleito {
  houve_comparacao: boolean
  divergencia_significativa?: boolean
  argumento_tecnico: string
  vento_ons_ms?: number
  vento_proprio_ms?: number
  delta_vento_relativo?: number
  geracao_referencia_recalculada_mwh?: number
  delta_geracao_referencia_mwh?: number
  fonte_dados_proprios?: string
}

export interface JanelaPleito {
  data_referencia_hoje: string
  dias_restantes_protocolo_ons: number
  pode_pleitear_protocolo_ons: boolean
  elegivel_termo: boolean
  janela_adesao_termo: string
  sager_dias_restantes: number
  sager_informativo: boolean
}

export interface EventoPleito {
  evento_id: string
  timestamp: string
  data_inicio: string
  data_fim: string
  duracao_horas: number
  n_intervalos?: number
  source_interval_ids?: string[]
  razao_classificada_ons: "REL" | "CNF" | "ENE" | string
  razao_original?: string | null
  origem: string
  geracao_verificada_mwh: number
  geracao_referencia_ons_mwh: number
  energia_restringida_mwh: number
  pld_reais_mwh: number
  valor_intervalos_reais?: number | null
  submercado: string
  elegivel: boolean
  canal_recomendado: "PROTOCOLO_ONS" | "TERMO_COMPROMISSO_LEI_15269" | "NENHUM" | string
  motivo_inelegibilidade?: string | null
  fonte_normativa: string
  confianca: number
  status_franquia: string
  status_franquia_label?: string | null
  horas_acumuladas_antes: number
  horas_acumuladas_depois: number
  energia_ressarcivel_mwh: number
  valor_pleitavel_reais: number
  destinatario_do_ressarcimento: string
  reconciliacao: ReconciliacaoPleito
  janela_prazo: JanelaPleito
  anexos_recomendados: string[]
}

export interface EventosPleitoOut {
  usina_id: string
  periodo: { inicio: string; fim: string }
  franquia: { ano: number; fonte: string; horas_definidas: number; fonte_normativa: string }
  total_eventos: number
  total_intervalos_restricao?: number
  eventos_elegiveis: number
  valor_total_pleitavel_reais: number
  energia_ressarcivel_total_mwh: number
  eventos: EventoPleito[]
  metadata: Record<string, unknown>
}

export interface PleitoCreateRequest {
  eventos_ids: string[]
  canal: string
  inicio?: string
  fim?: string
}

export interface PleitoUpdateRequest {
  markdown_gerado?: string
  status?: string
}

export interface PleitoOut {
  pleito_id: string
  usina_id: string
  canal: string
  eventos_ids: string[]
  status: string
  markdown_gerado: string
  metadados_json: Record<string, unknown>
  criado_em: string
  atualizado_em: string
}

export interface FranquiaStatusOut {
  usina_id: string
  ano: number
  fonte: string
  franquia_horas: number
  fonte_normativa: string
  horas_rel_acumuladas: number
  horas_restantes: number
  metadata: Record<string, unknown>
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
  content_encoding?: "utf-8" | "base64"
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
  usina_id?: string
  inicio?: string
  fim?: string
}

export interface ConsultaOut {
  resposta: string
  fontes: string[]
}

export interface ApiError {
  code: string
  detail: string
}

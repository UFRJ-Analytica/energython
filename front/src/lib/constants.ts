export const API_BASE = "/api"

export const FONTES = ["solar", "eolica"] as const
export const SUBMERCADOS = ["NE", "SE", "S", "N"] as const

export const QUALIDADE_LABELS: Record<string, string> = {
  completo: "Dados completos",
  parcial: "PLD parcial",
  sem_pld: "Sem PLD",
}

export const RAZAO_LABELS: Record<string, string> = {
  confiabilidade: "Confiabilidade",
  indisponibilidade_externa: "Indisp. externa",
  energetico: "Energético",
  indefinido: "Indefinido",
}

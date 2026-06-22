import { get } from "./client"
import type {
  DebugAnomaliasOut,
  DebugControlTowerOut,
  DebugForecastOut,
  DebugHealthDadosOut,
  DebugNoticiasOut,
  DebugRankingOut,
  DebugUnidadesOut,
  DebugUsinaDetalheOut,
} from "@/types/debug"

export const getDebugHealthDados = (limit = 5) =>
  get<DebugHealthDadosOut>(`/debug/health-dados?limit=${limit}`)

export const getDebugControlTower = (limit = 20, dias = 90) =>
  get<DebugControlTowerOut>(`/debug/control-tower?limit=${limit}&dias=${dias}`)

export const getDebugRanking = (limit = 30, dias = 90) =>
  get<DebugRankingOut>(`/debug/ranking?limit=${limit}&dias=${dias}`)

export const getDebugUnidades = (limit = 30, dias = 90) =>
  get<DebugUnidadesOut>(`/debug/unidades?limit=${limit}&dias=${dias}`)

export const getDebugUsina = (id: string, dias = 90, limitSerie = 200) =>
  get<DebugUsinaDetalheOut>(`/debug/usinas/${encodeURIComponent(id)}?dias=${dias}&limit_serie=${limitSerie}`)

export const getDebugAnomalias = (id: string, dias = 90, limit = 30) =>
  get<DebugAnomaliasOut>(`/debug/usinas/${encodeURIComponent(id)}/anomalias?dias=${dias}&limit=${limit}`)

export const getDebugForecast = (id: string, horizonte = 48, dias = 120) =>
  get<DebugForecastOut>(`/debug/usinas/${encodeURIComponent(id)}/forecast?horizonte=${horizonte}&dias=${dias}`)

export const getDebugNoticias = (id: string, termosExtra = "", maxItens = 12) =>
  get<DebugNoticiasOut>(`/debug/usinas/${encodeURIComponent(id)}/noticias?termos_extra=${encodeURIComponent(termosExtra)}&max_itens=${maxItens}`)

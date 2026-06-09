import { subDays } from "date-fns"
import { toIso } from "@/lib/formatters"

export const DEFAULT_HISTORY_DAYS = 90
export const MAX_LOOKBACK_DAYS = 365

const SOLAR_MAX = new Date("2026-05-29T23:30:00")
const EOLICA_MAX = new Date("2023-02-28T23:30:00")

function normalizeFonte(fonte?: string | null) {
  const value = String(fonte ?? "").toLowerCase()
  if (value.includes("eol")) return "eolica"
  if (value.includes("solar") || value.includes("fotov")) return "solar"
  return "solar"
}

export interface PlantDateWindow {
  minDate: Date
  maxDate: Date
  defaultInicio: string
  defaultFim: string
}

export function getPlantDateWindow(fonte?: string | null): PlantDateWindow {
  const normalized = normalizeFonte(fonte)
  const maxDate = normalized === "eolica" ? EOLICA_MAX : SOLAR_MAX
  const minDate = subDays(maxDate, MAX_LOOKBACK_DAYS)
  const defaultStart = subDays(maxDate, DEFAULT_HISTORY_DAYS)
  const defaultInicio = toIso(defaultStart < minDate ? minDate : defaultStart)
  const defaultFim = toIso(maxDate)

  return {
    minDate,
    maxDate,
    defaultInicio,
    defaultFim,
  }
}

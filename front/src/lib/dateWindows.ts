import { subDays } from "date-fns"
import { toIso } from "@/lib/formatters"

export const DEFAULT_HISTORY_DAYS = 60
export const MAX_LOOKBACK_DAYS = 365

const FALLBACK_MAX = new Date("2026-05-29T23:30:00")

export interface PlantDateWindow {
  minDate: Date
  maxDate: Date
  defaultInicio: string
  defaultFim: string
}

function parseAvailableDate(value?: string | null): Date | null {
  if (!value) return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed
}

export function getPlantDateWindow(availableFim?: string | null): PlantDateWindow {
  const maxDate = parseAvailableDate(availableFim) ?? FALLBACK_MAX
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

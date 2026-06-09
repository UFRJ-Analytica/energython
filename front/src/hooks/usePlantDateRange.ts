import { useEffect, useMemo, useState } from "react"
import { getPlantDateWindow } from "@/lib/dateWindows"

export function usePlantDateRange(fonte?: string | null) {
  const window = useMemo(() => getPlantDateWindow(fonte), [fonte])
  const [inicio, setInicio] = useState("")
  const [fim, setFim] = useState("")

  useEffect(() => {
    if (!fonte) return
    setInicio(window.defaultInicio)
    setFim(window.defaultFim)
  }, [fonte, window.defaultInicio, window.defaultFim])

  return {
    inicio,
    fim,
    setRange: (nextInicio: string, nextFim: string) => {
      setInicio(nextInicio)
      setFim(nextFim)
    },
    minDate: window.minDate,
    maxDate: window.maxDate,
    ready: Boolean(fonte && inicio && fim),
  }
}

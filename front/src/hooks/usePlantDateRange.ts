import { useEffect, useMemo, useState } from "react"
import { getPlantDateWindow } from "@/lib/dateWindows"

export function usePlantDateRange(availableFim?: string | null) {
  const window = useMemo(() => getPlantDateWindow(availableFim), [availableFim])
  const [inicio, setInicio] = useState("")
  const [fim, setFim] = useState("")

  useEffect(() => {
    setInicio(window.defaultInicio)
    setFim(window.defaultFim)
  }, [window.defaultInicio, window.defaultFim])

  return {
    inicio,
    fim,
    setRange: (nextInicio: string, nextFim: string) => {
      setInicio(nextInicio)
      setFim(nextFim)
    },
    minDate: window.minDate,
    maxDate: window.maxDate,
    ready: Boolean(inicio && fim),
  }
}

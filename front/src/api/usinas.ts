import { get } from "./client"
import type { UsinaListOut, UsinaOut, UsinaResumoOut } from "@/types/usinas"

interface ListParams {
  fonte?: string
  submercado?: string
  limit?: number
  offset?: number
}

export const listUsinas = ({ fonte, submercado, limit = 20, offset = 0 }: ListParams = {}) => {
  const q = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (fonte) q.set("fonte", fonte)
  if (submercado) q.set("submercado", submercado)
  return get<UsinaListOut>(`/usinas?${q}`)
}

export const getUsina = (id: string) => get<UsinaOut>(`/usinas/${id}`)

export const getResumo = (id: string, inicio: string, fim: string) =>
  get<UsinaResumoOut>(`/usinas/${id}/resumo?inicio=${inicio}&fim=${fim}`)

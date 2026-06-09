import { useQuery } from "@tanstack/react-query"
import { getResumo, getUsina, listUsinas } from "@/api/usinas"

interface UseUsinasParams {
  fonte?: string
  submercado?: string
  limit?: number
  offset?: number
}

const BULK_LIMIT = 200

export const useUsinas = (params: UseUsinasParams = {}) =>
  useQuery({
    queryKey: ["usinas", params],
    queryFn: () => listUsinas(params),
  })

export const useAllUsinas = (params: Omit<UseUsinasParams, "limit" | "offset"> = {}) =>
  useQuery({
    queryKey: ["usinas-all", params],
    queryFn: async () => {
      const first = await listUsinas({ ...params, limit: BULK_LIMIT, offset: 0 })
      const total = first.total_count ?? first.items.length
      if (total <= BULK_LIMIT) return first.items

      const pages: Promise<Awaited<ReturnType<typeof listUsinas>>>[] = []
      for (let offset = BULK_LIMIT; offset < total; offset += BULK_LIMIT) {
        pages.push(listUsinas({ ...params, limit: BULK_LIMIT, offset }))
      }
      const rest = await Promise.all(pages)
      return [first.items, ...rest.map((p) => p.items)].flat()
    },
  })

export const useUsina = (id: string) =>
  useQuery({
    queryKey: ["usina", id],
    queryFn: () => getUsina(id),
    enabled: !!id,
  })

export const useUsinaResumo = (id: string, inicio: string, fim: string, enabled = true) =>
  useQuery({
    queryKey: ["resumo", id, inicio, fim],
    queryFn: () => getResumo(id, inicio, fim),
    enabled: enabled && !!id && !!inicio && !!fim,
  })

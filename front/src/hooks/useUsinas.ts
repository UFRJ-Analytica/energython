import { useQuery } from "@tanstack/react-query"
import { getResumo, getUsina, listUsinas } from "@/api/usinas"

interface UseUsinasParams {
  fonte?: string
  submercado?: string
  limit?: number
  offset?: number
}

export const useUsinas = (params: UseUsinasParams = {}) =>
  useQuery({
    queryKey: ["usinas", params],
    queryFn: () => listUsinas(params),
  })

export const useUsina = (id: string) =>
  useQuery({
    queryKey: ["usina", id],
    queryFn: () => getUsina(id),
    enabled: !!id,
  })

export const useUsinaResumo = (id: string, inicio: string, fim: string) =>
  useQuery({
    queryKey: ["resumo", id, inicio, fim],
    queryFn: () => getResumo(id, inicio, fim),
    enabled: !!id && !!inicio && !!fim,
  })

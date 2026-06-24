import { useMutation, useQuery } from "@tanstack/react-query"
import { getExposicao, getPerda, postBessSimular } from "@/api/financeiro"
import type { BessRequest } from "@/types/financeiro"

export const usePerda = (id: string, inicio: string, fim: string, enabled = true) =>
  useQuery({
    queryKey: ["perda", id, inicio, fim],
    queryFn: () => getPerda(id, inicio, fim),
    enabled: enabled && !!id && !!inicio && !!fim,
  })

export const useExposicao = (id: string, horizonte = 48) =>
  useQuery({
    queryKey: ["exposicao", id, horizonte],
    queryFn: () => getExposicao(id, horizonte),
    enabled: !!id,
  })

export const useBessSimular = (id: string, inicio: string, fim: string) =>
  useMutation({
    mutationFn: (body: BessRequest) => postBessSimular(id, inicio, fim, body),
  })

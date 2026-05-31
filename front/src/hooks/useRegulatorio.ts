import { useMutation, useQuery } from "@tanstack/react-query"
import { getElegibilidade, postConsulta, postDossie, postDossieExport, postFluxoRessarcimento } from "@/api/regulatorio"
import type {
  ConsultaRequest,
  DossieExportRequest,
  DossieRequest,
  FluxoRessarcimentoRequest,
} from "@/types/regulatorio"

export const useElegibilidade = (id: string, inicio: string, fim: string) =>
  useQuery({
    queryKey: ["elegibilidade", id, inicio, fim],
    queryFn: () => getElegibilidade(id, inicio, fim),
    enabled: !!id && !!inicio && !!fim,
    staleTime: 30 * 60 * 1000,
  })

export const useDossie = (id: string) =>
  useMutation({
    mutationFn: (body: DossieRequest) => postDossie(id, body),
  })

export const useDossieExport = (id: string) =>
  useMutation({
    mutationFn: (body: DossieExportRequest) => postDossieExport(id, body),
  })

export const useFluxoRessarcimento = (id: string) =>
  useMutation({
    mutationFn: (body: FluxoRessarcimentoRequest) => postFluxoRessarcimento(id, body),
  })

export const useConsulta = () =>
  useMutation({
    mutationFn: (body: ConsultaRequest) => postConsulta(body),
  })

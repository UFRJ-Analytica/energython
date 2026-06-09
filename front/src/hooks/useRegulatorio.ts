import { useMutation, useQuery } from "@tanstack/react-query"
import {
  getElegibilidade,
  getEventosPleito,
  getFranquiaStatus,
  getPleitoExport,
  patchPleito,
  postConsulta,
  postDossie,
  postDossieExport,
  postFluxoRessarcimento,
  postPleito,
} from "@/api/regulatorio"
import type {
  ConsultaRequest,
  DossieExportRequest,
  DossieRequest,
  FluxoRessarcimentoRequest,
  PleitoCreateRequest,
  PleitoUpdateRequest,
} from "@/types/regulatorio"

export const useElegibilidade = (id: string, inicio: string, fim: string) =>
  useQuery({
    queryKey: ["elegibilidade", id, inicio, fim],
    queryFn: () => getElegibilidade(id, inicio, fim),
    enabled: !!id && !!inicio && !!fim,
    staleTime: 30 * 60 * 1000,
  })

export const useEventosPleito = (id: string, inicio: string, fim: string, enabled = true) =>
  useQuery({
    queryKey: ["eventos-pleito", id, inicio, fim],
    queryFn: () => getEventosPleito(id, inicio, fim),
    enabled: enabled && !!id && !!inicio && !!fim,
    staleTime: 5 * 60 * 1000,
  })

export const useFranquiaStatus = (id: string, ano: number) =>
  useQuery({
    queryKey: ["franquia-status", id, ano],
    queryFn: () => getFranquiaStatus(id, ano),
    enabled: !!id && !!ano,
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

export const useCriarPleito = (id: string) =>
  useMutation({
    mutationFn: (body: PleitoCreateRequest) => postPleito(id, body),
  })

export const useAtualizarPleito = (pleitoId: string) =>
  useMutation({
    mutationFn: (body: PleitoUpdateRequest) => patchPleito(pleitoId, body),
  })

export const useExportarPleito = () =>
  useMutation({
    mutationFn: ({ pleitoId, formato }: { pleitoId: string; formato: "docx" | "pdf" | "md" | "json" }) => getPleitoExport(pleitoId, formato),
  })

export const useConsulta = () =>
  useMutation({
    mutationFn: (body: ConsultaRequest) => postConsulta(body),
  })

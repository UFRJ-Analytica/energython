import { get, post } from "./client"
import type {
  ConsultaOut,
  ConsultaRequest,
  DossieExportOut,
  DossieExportRequest,
  DossieOut,
  DossieRequest,
  ElegibilidadeOut,
  FluxoRessarcimentoOut,
  FluxoRessarcimentoRequest,
} from "@/types/regulatorio"

export const getElegibilidade = (id: string, inicio: string, fim: string) =>
  get<ElegibilidadeOut>(`/usinas/${id}/elegibilidade?inicio=${inicio}&fim=${fim}`)

export const postDossie = (id: string, body: DossieRequest) =>
  post<DossieOut>(`/usinas/${id}/dossie`, body)

export const postDossieExport = (id: string, body: DossieExportRequest) =>
  post<DossieExportOut>(`/usinas/${id}/dossie/export`, body)

export const postFluxoRessarcimento = (id: string, body: FluxoRessarcimentoRequest) =>
  post<FluxoRessarcimentoOut>(`/usinas/${id}/ressarcimento`, body)

export const postConsulta = (body: ConsultaRequest) =>
  post<ConsultaOut>(`/regulatorio/consulta`, body)

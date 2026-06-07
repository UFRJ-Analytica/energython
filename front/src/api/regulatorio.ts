import { get, patch, post } from "./client"
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
  EventosPleitoOut,
  PleitoCreateRequest,
  PleitoOut,
  PleitoUpdateRequest,
  FranquiaStatusOut,
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

export const getEventosPleito = (id: string, inicio: string, fim: string) =>
  get<EventosPleitoOut>(`/usinas/${id}/eventos-pleito?inicio=${inicio}&fim=${fim}`)

export const getFranquiaStatus = (id: string, ano: number) =>
  get<FranquiaStatusOut>(`/usinas/${id}/franquia-status?ano=${ano}`)

export const postPleito = (id: string, body: PleitoCreateRequest) =>
  post<PleitoOut>(`/usinas/${id}/pleitos`, body)

export const getPleito = (pleitoId: string) => get<PleitoOut>(`/pleitos/${pleitoId}`)

export const patchPleito = (pleitoId: string, body: PleitoUpdateRequest) =>
  patch<PleitoOut>(`/pleitos/${pleitoId}`, body)

export const getPleitoExport = (pleitoId: string, formato: "docx" | "pdf" | "md" | "json" = "docx") =>
  get<{ pleito_id: string; formato: string; file_name: string; content_type: string; content: string; content_encoding?: "utf-8" | "base64" }>(`/pleitos/${pleitoId}/export?formato=${formato}`)

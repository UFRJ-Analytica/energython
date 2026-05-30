import { get, post } from "./client"
import type { ConsultaOut, ConsultaRequest, DossieOut, DossieRequest, ElegibilidadeOut } from "@/types/regulatorio"

export const getElegibilidade = (id: string, inicio: string, fim: string) =>
  get<ElegibilidadeOut>(`/usinas/${id}/elegibilidade?inicio=${inicio}&fim=${fim}`)

export const postDossie = (id: string, body: DossieRequest) =>
  post<DossieOut>(`/usinas/${id}/dossie`, body)

export const postConsulta = (body: ConsultaRequest) =>
  post<ConsultaOut>(`/regulatorio/consulta`, body)

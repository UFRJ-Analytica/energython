import { get, post } from "./client"
import type { BessOut, BessRequest, ExposicaoOut, PerdaOut } from "@/types/financeiro"

export const getPerda = (id: string, inicio: string, fim: string) =>
  get<PerdaOut>(`/usinas/${id}/perda?inicio=${inicio}&fim=${fim}`)

export const getExposicao = (id: string, horizonte = 48) =>
  get<ExposicaoOut>(`/usinas/${id}/exposicao?horizonte=${horizonte}`)

export const postBessSimular = (id: string, inicio: string, fim: string, body: BessRequest) =>
  post<BessOut>(`/usinas/${id}/bess/simular?inicio=${inicio}&fim=${fim}`, body)

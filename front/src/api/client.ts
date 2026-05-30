import { API_BASE } from "@/lib/constants"
import type { ApiError } from "@/types/regulatorio"

export class ApiException extends Error {
  code: string
  constructor(code: string, message: string) {
    super(message)
    this.code = code
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  })

  if (!res.ok) {
    const body: ApiError = await res.json().catch(() => ({ code: "erro_desconhecido", detail: res.statusText }))
    throw new ApiException(body.code, body.detail)
  }

  return res.json()
}

export const get = <T>(path: string) => request<T>(path)
export const post = <T>(path: string, body: unknown) => request<T>(path, { method: "POST", body: JSON.stringify(body) })

import { useQuery } from "@tanstack/react-query"
import {
  getDebugAnomalias,
  getDebugControlTower,
  getDebugForecast,
  getDebugHealthDados,
  getDebugNoticias,
  getDebugRanking,
  getDebugUnidades,
  getDebugUsina,
} from "@/api/debug"

export const useDebugHealthDados = (limit = 5) =>
  useQuery({
    queryKey: ["debug", "health-dados", limit],
    queryFn: () => getDebugHealthDados(limit),
  })

export const useDebugControlTower = (limit = 20, dias = 90) =>
  useQuery({
    queryKey: ["debug", "control-tower", limit, dias],
    queryFn: () => getDebugControlTower(limit, dias),
  })

export const useDebugRanking = (limit = 30, dias = 90) =>
  useQuery({
    queryKey: ["debug", "ranking", limit, dias],
    queryFn: () => getDebugRanking(limit, dias),
  })

export const useDebugUnidades = (limit = 30, dias = 90) =>
  useQuery({
    queryKey: ["debug", "unidades", limit, dias],
    queryFn: () => getDebugUnidades(limit, dias),
  })

export const useDebugUsina = (id: string, dias = 90, limitSerie = 200) =>
  useQuery({
    queryKey: ["debug", "usina", id, dias, limitSerie],
    queryFn: () => getDebugUsina(id, dias, limitSerie),
    enabled: !!id,
  })

export const useDebugAnomalias = (id: string, dias = 90, limit = 30) =>
  useQuery({
    queryKey: ["debug", "anomalias", id, dias, limit],
    queryFn: () => getDebugAnomalias(id, dias, limit),
    enabled: !!id,
  })

export const useDebugForecast = (id: string, horizonte = 48, dias = 120) =>
  useQuery({
    queryKey: ["debug", "forecast", id, horizonte, dias],
    queryFn: () => getDebugForecast(id, horizonte, dias),
    enabled: !!id,
  })

export const useDebugNoticias = (id: string, termosExtra = "", maxItens = 12) =>
  useQuery({
    queryKey: ["debug", "noticias", id, termosExtra, maxItens],
    queryFn: () => getDebugNoticias(id, termosExtra, maxItens),
    enabled: !!id,
  })

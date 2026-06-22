import { useEffect, useMemo, useState } from "react"
import { Navigate, useNavigate } from "react-router-dom"
import { ArrowLeft, Bug, ExternalLink, RefreshCw } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { AnomalyTimeSeriesChart } from "@/components/charts/AnomalyTimeSeriesChart"
import { ForecastTimeSeriesChart } from "@/components/charts/ForecastTimeSeriesChart"
import { Skeleton } from "@/components/ui/skeleton"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import {
  useDebugAnomalias,
  useDebugControlTower,
  useDebugForecast,
  useDebugHealthDados,
  useDebugNoticias,
  useDebugRanking,
  useDebugUnidades,
  useDebugUsina,
} from "@/hooks/useDebug"
import { fmtBRL, fmtMWh, fmtPct } from "@/lib/formatters"
import type { DebugUsinaScoreOut } from "@/types/debug"

const ACCESS_KEY = "energython.debugAccess"
const pctFraction = (value: number) => fmtPct(value * 100)

function Kpi({ label, value, unit }: { label: string; value: number | string; unit?: string | null }) {
  return (
    <Card className="border-sky-500/20 bg-sky-500/5 text-white">
      <CardContent className="p-4">
        <p className="text-xs uppercase tracking-widest text-sky-300/70">{label}</p>
        <p className="mt-2 text-2xl font-bold text-foreground text-white">{String(value)}</p>
        {unit && <p className="text-xs text-slate-400">{unit}</p>}
      </CardContent>
    </Card>
  )
}

function RankingTable({ rows, onSelect }: { rows: DebugUsinaScoreOut[]; onSelect: (id: string) => void }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="border-b border-white/10 text-xs uppercase text-slate-500">
          <tr>
            <th className="py-2 pr-3">Usina</th>
            <th className="py-2 pr-3">Score</th>
            <th className="py-2 pr-3">Corte</th>
            <th className="py-2 pr-3">Perda</th>
            <th className="py-2">Ação</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.usina_id} className="border-b border-white/5">
              <td className="py-3 pr-3">
                <p className="font-medium">{row.nome}</p>
                <p className="text-xs text-slate-500">{row.fonte} · {row.submercado}</p>
              </td>
              <td className="py-3 pr-3 text-cyan-300">{row.health_score.toFixed(1)}</td>
              <td className="py-3 pr-3">{fmtMWh(row.total_corte_mwh)}</td>
              <td className="py-3 pr-3">{fmtBRL(row.total_perda_reais)}</td>
              <td className="py-3">
                <Button size="sm" variant="outline" onClick={() => onSelect(row.usina_id)}>
                  Selecionar
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default function DebugPage() {
  const navigate = useNavigate()
  const [allowed, setAllowed] = useState<boolean | null>(null)
  const [selectedId, setSelectedId] = useState("")

  useEffect(() => {
    setAllowed(sessionStorage.getItem(ACCESS_KEY) === "true")
  }, [])

  const health = useDebugHealthDados(5)
  const tower = useDebugControlTower(30, 90)
  const ranking = useDebugRanking(30, 90)
  const unidades = useDebugUnidades(30, 90)
  const defaultId = tower.data?.ranking?.[0]?.usina_id ?? ""
  const activeId = selectedId || defaultId
  const detalhe = useDebugUsina(activeId, 90, 220)
  const anomalias = useDebugAnomalias(activeId, 90, 30)
  const forecast = useDebugForecast(activeId, 48, 120)
  const noticias = useDebugNoticias(activeId, "curtailment energia", 12)

  const kpis = useMemo(() => tower.data?.kpis ?? [], [tower.data])

  if (allowed === null) {
    return <div className="min-h-screen bg-background p-8 text-foreground">Carregando DEBUG...</div>
  }

  if (!allowed) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="min-h-screen bg-[#05070b] text-white">
      <header className="sticky top-0 z-30 border-b border-white/10 bg-black/50 backdrop-blur">
        <div className="container mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <Bug className="h-5 w-5 text-cyan-300" />
            <div>
              <h1 className="font-heading text-lg font-semibold">DEBUG CurtailIQ Energython</h1>
              <p className="text-xs text-slate-400">Telas de teste adaptadas do Streamlit — isoladas do fluxo principal</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={() => window.location.reload()}>
              <RefreshCw className="mr-2 h-4 w-4" /> Atualizar
            </Button>
            <Button variant="ghost" size="sm" onClick={() => navigate("/")}>
              <ArrowLeft className="mr-2 h-4 w-4" /> Home
            </Button>
          </div>
        </div>
      </header>

      <main className="container mx-auto max-w-7xl space-y-8 px-6 py-8">
        <section className="grid gap-4 md:grid-cols-4">
          {tower.isLoading ? (
            Array.from({ length: 4 }).map((_, idx) => <Skeleton key={idx} className="h-28 bg-white/10" />)
          ) : (
            kpis.map((kpi) => <Kpi key={kpi.label} label={kpi.label} value={kpi.value} unit={kpi.unit} />)
          )}
        </section>

        <Tabs defaultValue="tower" className="space-y-5">
          <TabsList className="flex h-auto w-full flex-wrap justify-start bg-white/10 p-1 text-white">
            <TabsTrigger value="tower">1. Control Tower</TabsTrigger>
            <TabsTrigger value="detalhe">2. Detalhe & Previsão</TabsTrigger>
            <TabsTrigger value="anomalias">3. Anomalias</TabsTrigger>
            <TabsTrigger value="noticias">4. Notícias</TabsTrigger>
            <TabsTrigger value="ranking">5. Ranking</TabsTrigger>
            <TabsTrigger value="unidades">6. Unidades</TabsTrigger>
          </TabsList>

          <TabsContent value="tower">
            <Card className="border-white/10 bg-white/[0.04] text-white">
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  Control Tower DEBUG
                  <Badge variant="outline">{health.data?.repository ?? "repo"}</Badge>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {health.data && (
                  <div className="rounded-lg border border-white/10 bg-black/20 p-3 text-sm text-slate-300">
                    Status dados: <span className="font-semibold text-cyan-300">{health.data.status}</span>
                    {health.data.observacoes.length > 0 && (
                      <ul className="mt-2 list-disc pl-5 text-xs text-amber-200">
                        {health.data.observacoes.map((obs) => <li key={obs}>{obs}</li>)}
                      </ul>
                    )}
                  </div>
                )}
                <RankingTable rows={tower.data?.ranking ?? []} onSelect={setSelectedId} />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="detalhe">
            <section className="space-y-6">
              <Card className="border-white/10 bg-white/[0.04] text-white">
                <CardHeader><CardTitle>Ficha da usina</CardTitle></CardHeader>
                <CardContent>
                  {detalhe.data ? (
                    <div className="flex flex-wrap items-end justify-between gap-4">
                      <div>
                        <p className="text-xs uppercase tracking-widest text-slate-500">Selecionada</p>
                        <p className="text-xl font-semibold">{String(detalhe.data.usina.nome ?? activeId)}</p>
                        <p className="text-xs text-slate-500">{activeId}</p>
                      </div>
                      <div className="grid flex-1 grid-cols-2 gap-3 sm:max-w-2xl sm:grid-cols-4">
                        <Kpi label="Score" value={detalhe.data.score.health_score.toFixed(1)} unit="0-100" />
                        <Kpi label="% Corte" value={pctFraction(detalhe.data.score.percentual_corte)} />
                        <Kpi label="Corte" value={fmtMWh(detalhe.data.score.total_corte_mwh)} />
                        <Kpi label="Perda" value={fmtBRL(detalhe.data.score.total_perda_reais)} />
                      </div>
                    </div>
                  ) : <Skeleton className="h-24 bg-white/10" />}
                </CardContent>
              </Card>

              {/* DESTAQUE: retângulo em evidência, largura total, plot maior */}
              <div className="rounded-2xl border-2 border-violet-500/60 bg-gradient-to-br from-violet-600/15 via-[#0b1220] to-[#0b1220] p-4 shadow-[0_0_40px_rgba(139,92,246,0.25)] ring-1 ring-violet-400/30">
                <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-violet-400/20 pb-3">
                  <div>
                    <h3 className="font-heading text-lg font-semibold text-white">Previsão de geração (MW)</h3>
                    <p className="text-xs text-slate-400">
                      Modelo: {forecast.data?.modelo ?? "—"} · ganho {forecast.data?.ganho_pct?.toFixed(1) ?? "—"}% · MAE híbrido {forecast.data?.mae_hibrido?.toFixed(2) ?? "—"} · MAE baseline {forecast.data?.mae_baseline?.toFixed(2) ?? "—"}
                    </p>
                  </div>
                  <div className="rounded-lg border border-emerald-400/30 bg-emerald-500/10 px-3 py-1.5 text-right">
                    <p className="text-[10px] uppercase tracking-widest text-emerald-300/80">Fator da usina</p>
                    <p className="text-lg font-bold text-emerald-300">
                      {detalhe.data?.score.fator_capacidade != null
                        ? `${(detalhe.data.score.fator_capacidade * 100).toFixed(0)}%`
                        : "n/d"}
                    </p>
                  </div>
                </div>
                {forecast.isLoading ? (
                  <Skeleton className="h-[520px] bg-white/10" />
                ) : (
                  <ForecastTimeSeriesChart
                    pontos={forecast.data?.pontos ?? []}
                    fatorCapacidade={detalhe.data?.score.fator_capacidade ?? null}
                    height={520}
                  />
                )}
              </div>
            </section>
          </TabsContent>

          <TabsContent value="anomalias">
            <Card className="border-white/10 bg-white/[0.04] text-white">
              <CardHeader><CardTitle>🚨 Detecção de Anomalias de Corte</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-slate-400">
                  IsolationForest sobre o gap geração × referência. Marcadores vermelhos = comportamento anômalo.
                  Método: {anomalias.data?.metodo ?? "—"} · anomalias: {anomalias.data?.total_anomalias ?? 0} de {anomalias.data?.total_pontos ?? detalhe.data?.serie_amostra.length ?? 0} pontos.
                </p>
                {detalhe.isLoading || anomalias.isLoading ? (
                  <Skeleton className="h-[460px] bg-white/10" />
                ) : (
                  <AnomalyTimeSeriesChart
                    serie={detalhe.data?.serie_amostra ?? []}
                    anomalias={anomalias.data?.anomalias ?? []}
                  />
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="noticias">
            <Card className="border-white/10 bg-white/[0.04] text-white">
              <CardHeader><CardTitle>Inteligência de notícias</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <p className="text-sm text-slate-400">Consulta: {noticias.data?.consulta ?? "—"}</p>
                {noticias.data?.erro && <p className="text-sm text-amber-300">Erro RSS: {noticias.data.erro}</p>}
                {noticias.data?.itens.map((item) => (
                  <a key={item.link} href={item.link} target="_blank" rel="noreferrer" className="block rounded-lg border border-white/10 bg-black/20 p-4 transition hover:bg-white/10">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <p className="font-medium text-cyan-200">{item.titulo}</p>
                        <p className="mt-1 text-xs text-slate-500">{item.fonte} · relevância {item.relevancia}</p>
                        {item.resumo && <p className="mt-2 text-sm text-slate-400">{item.resumo}</p>}
                      </div>
                      <ExternalLink className="h-4 w-4 text-slate-500" />
                    </div>
                  </a>
                ))}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ranking">
            <div className="grid gap-6 lg:grid-cols-2">
              <Card className="border-emerald-500/20 bg-emerald-500/5 text-white">
                <CardHeader><CardTitle>Melhores usinas</CardTitle></CardHeader>
                <CardContent><RankingTable rows={ranking.data?.melhores ?? []} onSelect={setSelectedId} /></CardContent>
              </Card>
              <Card className="border-red-500/20 bg-red-500/5 text-white">
                <CardHeader><CardTitle>Piores usinas</CardTitle></CardHeader>
                <CardContent><RankingTable rows={ranking.data?.piores ?? []} onSelect={setSelectedId} /></CardContent>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="unidades">
            <Card className="border-white/10 bg-white/[0.04] text-white">
              <CardHeader>
                <CardTitle>Unidades individuais · granularidade única</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-sm text-slate-400">
                  {String(
                    unidades.data?.metadata?.observacao ??
                      "Cada linha é uma usina no grão único de 30 min (dw.mart_eolica + dw.mart_solar, chave nom_usina), unificando eólica e solar — sem agrupamento por complexo.",
                  )}
                </p>
                <RankingTable rows={unidades.data?.unidades ?? []} onSelect={setSelectedId} />
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}

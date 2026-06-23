import { useEffect, useMemo, useRef, useState } from "react"
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import { BatteryCharging, Pause, Play, RotateCcw, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Slider } from "@/components/ui/slider"
import { fmtBRL, fmtMWh } from "@/lib/formatters"
import type { PrevisaoPerdasSerieItem } from "@/types/financeiro"

interface Props {
  serie: PrevisaoPerdasSerieItem[]
  isLoading?: boolean
  potenciaMw: number
  duracaoHoras: number
  eficienciaPct: number
  nome?: string
  metodo?: string
}

interface SimPoint {
  timestamp: string
  curtailment: number
  pld: number
  perda: number
  carga: number
  excessoNaoCapturado: number
  soc: number
  socPct: number
}

const fmtTs = (iso: string) => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return (
    d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) +
    " " +
    d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
  )
}

const round = (v: number) => Math.round(v * 10000) / 10000

function socColor(pct: number) {
  if (pct < 20) return { fill: "#ef4444", glow: "rgba(239,68,68,0.45)", text: "text-red-400" }
  if (pct < 50) return { fill: "#f59e0b", glow: "rgba(245,158,11,0.45)", text: "text-amber-400" }
  if (pct < 80) return { fill: "#34d399", glow: "rgba(52,211,153,0.45)", text: "text-emerald-400" }
  return { fill: "#22d3ee", glow: "rgba(34,211,238,0.5)", text: "text-cyan-300" }
}

function BatteryGauge({ pct, charging }: { pct: number; charging: boolean }) {
  const c = socColor(pct)
  const clamped = Math.max(0, Math.min(100, pct))
  return (
    <div className="flex flex-col items-center gap-4">
      <div className="relative flex flex-col items-center">
        <div className="h-3 w-10 rounded-t-md border border-white/30 border-b-0 bg-white/20" />
        <div
          className="relative h-72 w-36 overflow-hidden rounded-xl border-4 border-white/25 bg-black/50"
          style={{ boxShadow: `0 0 32px ${c.glow}` }}
        >
          <div
            className="absolute bottom-0 left-0 right-0 transition-all duration-500 ease-out"
            style={{
              height: `${clamped}%`,
              background: `linear-gradient(to top, ${c.fill}, ${c.fill}cc)`,
              boxShadow: `0 0 24px ${c.glow}`,
            }}
          >
            <div className="absolute left-0 right-0 top-0 h-2 bg-white/40" />
          </div>

          {[25, 50, 75].map((m) => (
            <div
              key={m}
              className="absolute left-0 right-0 border-t border-dashed border-white/15"
              style={{ bottom: `${m}%` }}
            />
          ))}

          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={`text-4xl font-extrabold drop-shadow ${c.text}`}>{clamped.toFixed(0)}%</span>
            {charging && (
              <span className="mt-1 flex items-center gap-1 text-[10px] font-semibold uppercase tracking-widest text-emerald-300">
                <BatteryCharging className="h-3 w-3 animate-pulse" /> carregando
              </span>
            )}
          </div>
        </div>
      </div>
      <p className="text-xs uppercase tracking-widest text-slate-400">Estado de carga previsto</p>
    </div>
  )
}

export function BessCurtailmentBatteryChart({
  serie,
  isLoading,
  potenciaMw,
  duracaoHoras,
  eficienciaPct,
  nome,
  metodo,
}: Props) {
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const sim = useMemo<SimPoint[]>(() => {
    const capacidade = Math.max(potenciaMw * duracaoHoras, 0.0001)
    const eficiencia = Math.max(0, Math.min(1, eficienciaPct / 100))
    return serie.reduce<{ soc: number; rows: SimPoint[] }>(
      (acc, p) => {
        const curtailment = Math.max(0, Number(p.energia_mwh) || 0)
        const pld = Math.max(0, Number(p.pld_reais_mwh) || 0)
        const perda = Math.max(0, Number(p.perda_reais) || curtailment * pld)
        const limitePotencia = Math.max(0, potenciaMw)
        const energiaEntrada = Math.min(curtailment, limitePotencia)
        const espacoDisponivelEntrada = Math.max(0, capacidade - acc.soc) / Math.max(eficiencia, 0.0001)
        const energiaCapturadaAntesEficiencia = Math.min(energiaEntrada, espacoDisponivelEntrada)
        const carga = energiaCapturadaAntesEficiencia * eficiencia
        const nextSoc = Math.max(0, Math.min(capacidade, acc.soc + carga))
        const excessoNaoCapturado = Math.max(0, curtailment - energiaCapturadaAntesEficiencia)

        return {
          soc: nextSoc,
          rows: [
            ...acc.rows,
            {
              timestamp: p.timestamp,
              curtailment: round(curtailment),
              pld: round(pld),
              perda: round(perda),
              carga: round(carga),
              excessoNaoCapturado: round(excessoNaoCapturado),
              soc: round(nextSoc),
              socPct: round((nextSoc / capacidade) * 100),
            },
          ],
        }
      },
      { soc: 0, rows: [] },
    ).rows
  }, [serie, potenciaMw, duracaoHoras, eficienciaPct])

  useEffect(() => {
    if (!playing || sim.length === 0) return
    timerRef.current = setInterval(() => {
      setIdx((prev) => (prev >= sim.length - 1 ? 0 : prev + 1))
    }, 120)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [playing, sim.length])

  const stats = useMemo(() => {
    if (!sim.length) return null
    const capacidade = potenciaMw * duracaoHoras
    const totalCurtailment = sim.reduce((a, s) => a + s.curtailment, 0)
    const totalCarga = sim.reduce((a, s) => a + s.carga, 0)
    const naoCapturado = sim.reduce((a, s) => a + s.excessoNaoCapturado, 0)
    const perdaPrevista = sim.reduce((a, s) => a + s.perda, 0)
    const mitigacaoPct = totalCurtailment > 0 ? (totalCarga / totalCurtailment) * 100 : 0
    return { capacidade, totalCurtailment, totalCarga, naoCapturado, perdaPrevista, mitigacaoPct }
  }, [sim, potenciaMw, duracaoHoras])

  if (isLoading) {
    return <Skeleton className="h-[680px] w-full rounded-2xl bg-white/10" />
  }

  if (!sim.length) {
    return (
      <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-8 text-center text-sm text-slate-400">
        Previsão futura de curtailment indisponível para montar a simulação animada da bateria.
      </div>
    )
  }

  const atual = sim[Math.min(idx, sim.length - 1)]
  const carregando = playing && atual.carga > 0

  return (
    <div className="rounded-3xl border border-cyan-400/30 bg-gradient-to-br from-cyan-500/10 via-[#07111f] to-violet-950/20 p-5 shadow-[0_0_55px_rgba(34,211,238,0.16)] ring-1 ring-cyan-300/15">
      <div className="mb-5 flex flex-wrap items-start justify-between gap-4 border-b border-white/10 pb-4">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-cyan-300">Destaque · dimensionamento visual BESS</p>
          <h3 className="mt-1 font-heading text-2xl font-semibold text-white">
            Bateria carregando com o curtailment futuro previsto{nome ? ` · ${nome}` : ""}
          </h3>
          <p className="mt-1 max-w-3xl text-sm text-slate-400">
            A linha roxa é a energia restringida prevista hora a hora. A bateria carrega quando há curtailment e o SoC mostra se a potência/duração escolhidas conseguem absorver a janela futura.
          </p>
        </div>
        {metodo && <div className="rounded-lg border border-white/10 bg-black/30 px-3 py-2 text-xs text-slate-400">Método: <span className="text-slate-200">{metodo}</span></div>}
      </div>

      {stats && (
        <div className="mb-5 grid gap-3 md:grid-cols-4">
          <div className="rounded-xl border border-white/10 bg-black/25 p-3">
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Capacidade BESS</p>
            <p className="mt-1 text-lg font-bold text-cyan-300">{fmtMWh(stats.capacidade)}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/25 p-3">
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Curtailment previsto</p>
            <p className="mt-1 text-lg font-bold text-violet-300">{fmtMWh(stats.totalCurtailment)}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/25 p-3">
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Energia armazenada</p>
            <p className="mt-1 text-lg font-bold text-emerald-300">{fmtMWh(stats.totalCarga)}</p>
          </div>
          <div className="rounded-xl border border-white/10 bg-black/25 p-3">
            <p className="text-[10px] uppercase tracking-widest text-slate-500">Perda prevista</p>
            <p className="mt-1 text-lg font-bold text-amber-300">{fmtBRL(stats.perdaPrevista)}</p>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="flex flex-col items-center justify-center gap-5 rounded-2xl border border-white/10 bg-black/30 p-6">
          <BatteryGauge pct={atual.socPct} charging={carregando} />

          <div className="flex items-center gap-2">
            <Button size="sm" variant="outline" onClick={() => setPlaying((p) => !p)}>
              {playing ? <Pause className="mr-1 h-4 w-4" /> : <Play className="mr-1 h-4 w-4" />}
              {playing ? "Pausar" : "Animar"}
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => {
                setPlaying(false)
                setIdx(0)
              }}
            >
              <RotateCcw className="mr-1 h-4 w-4" /> Início
            </Button>
          </div>

          <div className="w-full space-y-1 text-center text-xs text-slate-400">
            <p className="font-mono text-slate-300">{fmtTs(atual.timestamp)}</p>
            <p>Curtailment previsto: <span className="text-violet-200">{fmtMWh(atual.curtailment)}</span></p>
            <p>
              {atual.carga > 0 ? (
                <span className="text-emerald-300">+{fmtMWh(atual.carga)} armazenados</span>
              ) : (
                <span className="text-slate-500">sem carga neste passo</span>
              )}
            </p>
            {atual.excessoNaoCapturado > 0 && (
              <p className="text-amber-300">{fmtMWh(atual.excessoNaoCapturado)} não capturados</p>
            )}
          </div>

          <div className="w-full px-1">
            <Slider
              min={0}
              max={sim.length - 1}
              step={1}
              value={[Math.min(idx, sim.length - 1)]}
              onValueChange={([v]) => {
                setPlaying(false)
                setIdx(v)
              }}
            />
            <div className="mt-1 flex justify-between text-[10px] text-slate-500">
              <span>{fmtTs(sim[0].timestamp)}</span>
              <span>{fmtTs(sim[sim.length - 1].timestamp)}</span>
            </div>
          </div>
        </div>

        <div className="rounded-2xl border border-white/10 bg-black/40 p-4 lg:col-span-2">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-slate-200">Curva futura de curtailment × carga da bateria</p>
            {stats && (
              <div className="flex flex-wrap gap-3 text-[11px] text-slate-400">
                <span>Mitigação visual: <span className="text-slate-200">{stats.mitigacaoPct.toFixed(1)}%</span></span>
                <span>Não capturado: <span className="text-slate-200">{fmtMWh(stats.naoCapturado)}</span></span>
              </div>
            )}
          </div>
          <ResponsiveContainer width="100%" height={460}>
            <ComposedChart data={sim} margin={{ top: 16, right: 16, bottom: 8, left: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="timestamp" tickFormatter={fmtTs} tick={{ fontSize: 10, fill: "#94a3b8" }} minTickGap={48} />
              <YAxis
                yAxisId="mwh"
                tick={{ fontSize: 10, fill: "#94a3b8" }}
                label={{ value: "MWh", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
              />
              <YAxis
                yAxisId="soc"
                orientation="right"
                domain={[0, 100]}
                tick={{ fontSize: 10, fill: "#22d3ee" }}
                label={{ value: "SoC %", angle: 90, position: "insideRight", fill: "#22d3ee", fontSize: 11 }}
              />
              <Tooltip
                contentStyle={{ background: "#0b1220", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#e2e8f0", fontSize: 12 }}
                labelFormatter={(l) => fmtTs(String(l))}
                formatter={(v, name) => {
                  const num = typeof v === "number" ? v : Number(v)
                  if (name === "SoC %") return [`${num.toFixed(0)}%`, name]
                  if (name === "Perda prevista") return [fmtBRL(num), name]
                  return [fmtMWh(num), name]
                }}
              />
              <Legend wrapperStyle={{ fontSize: 12 }} />
              <Area
                yAxisId="soc"
                type="monotone"
                dataKey="socPct"
                name="SoC %"
                stroke="#22d3ee"
                strokeWidth={2.5}
                fill="#22d3ee"
                fillOpacity={0.15}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                yAxisId="mwh"
                type="monotone"
                dataKey="curtailment"
                name="Curtailment previsto"
                stroke="#a78bfa"
                strokeWidth={2.5}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                yAxisId="mwh"
                type="monotone"
                dataKey="carga"
                name="Carga absorvida"
                stroke="#34d399"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <ReferenceLine
                yAxisId="soc"
                x={atual.timestamp}
                stroke="#e2e8f0"
                strokeDasharray="3 3"
                label={{ value: `${atual.socPct.toFixed(0)}%`, position: "top", fill: "#e2e8f0", fontSize: 11 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
          <p className="mt-3 flex items-center gap-2 text-xs text-slate-500">
            <Zap className="h-3.5 w-3.5 text-cyan-300" />
            MVP de dimensionamento: usa previsão futura de energia restringida; degradação, arbitragem e despacho ótimo ficam fora deste primeiro destaque visual.
          </p>
        </div>
      </div>
    </div>
  )
}

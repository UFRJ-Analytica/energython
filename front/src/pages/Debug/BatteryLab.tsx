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
import { BatteryCharging, Pause, Play, RotateCcw } from "lucide-react"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import type { DebugForecastPointOut } from "@/types/debug"
import { fmtMW, fmtMWh } from "@/lib/formatters"

interface Props {
  pontos: DebugForecastPointOut[]
  nome?: string
  isLoading?: boolean
}

interface SimPoint {
  timestamp: string
  geracao: number
  limite: number
  excedente: number
  carga: number
  descarga: number
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

const median = (arr: number[]) => {
  if (!arr.length) return 0
  const s = [...arr].sort((a, b) => a - b)
  const mid = Math.floor(s.length / 2)
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2
}

/** Cor da bateria conforme o nível de carga. */
function socColor(pct: number) {
  if (pct < 20) return { fill: "#ef4444", glow: "rgba(239,68,68,0.45)", text: "text-red-400" }
  if (pct < 50) return { fill: "#f59e0b", glow: "rgba(245,158,11,0.45)", text: "text-amber-400" }
  if (pct < 80) return { fill: "#34d399", glow: "rgba(52,211,153,0.45)", text: "text-emerald-400" }
  return { fill: "#22d3ee", glow: "rgba(34,211,238,0.5)", text: "text-cyan-300" }
}

/** Bateria animada vertical que mostra a porcentagem de carga (SoC). */
function BatteryGauge({ pct, charging }: { pct: number; charging: boolean }) {
  const c = socColor(pct)
  const clamped = Math.max(0, Math.min(100, pct))
  return (
    <div className="flex flex-col items-center gap-4">
      {/* Terminal + corpo da bateria */}
      <div className="relative flex flex-col items-center">
        <div className="h-3 w-10 rounded-t-md border border-white/30 border-b-0 bg-white/20" />
        <div
          className="relative h-72 w-36 overflow-hidden rounded-xl border-4 border-white/25 bg-black/50"
          style={{ boxShadow: `0 0 32px ${c.glow}` }}
        >
          {/* Preenchimento animado */}
          <div
            className="absolute bottom-0 left-0 right-0 transition-all duration-500 ease-out"
            style={{
              height: `${clamped}%`,
              background: `linear-gradient(to top, ${c.fill}, ${c.fill}cc)`,
              boxShadow: `0 0 24px ${c.glow}`,
            }}
          >
            {/* Brilho de "líquido" no topo */}
            <div className="absolute left-0 right-0 top-0 h-2 bg-white/40" />
          </div>

          {/* Marcas de nível */}
          {[25, 50, 75].map((m) => (
            <div
              key={m}
              className="absolute left-0 right-0 border-t border-dashed border-white/15"
              style={{ bottom: `${m}%` }}
            />
          ))}

          {/* Porcentagem central */}
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
      <p className="text-xs uppercase tracking-widest text-slate-400">Estado de carga (SoC)</p>
    </div>
  )
}

export function BatteryLab({ pontos, nome, isLoading }: Props) {
  const [potencia, setPotencia] = useState(30)
  const [duracao, setDuracao] = useState(4)
  const [eficiencia, setEficiencia] = useState(90)
  const [limite, setLimite] = useState<number | null>(null)
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(false)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // Limite de entrega padrão = mediana da geração prevista (rede "satura" acima disso).
  const limiteDefault = useMemo(() => {
    const gens = pontos.map((p) => p.forecast_mwh).filter((v) => Number.isFinite(v))
    return Math.round(median(gens))
  }, [pontos])

  const limiteAtivo = limite ?? limiteDefault

  // Simulação do estado de carga a partir da PREVISÃO (lógica do predict):
  // excedente acima do limite de entrega -> carrega a bateria (com eficiência);
  // déficit abaixo do limite -> bateria descarrega para complementar a entrega.
  const sim = useMemo<SimPoint[]>(() => {
    if (!pontos.length) return []
    const capacidade = Math.max(potencia * duracao, 0.0001)
    const efic = eficiencia / 100
    let soc = capacidade * 0.5 // começa em 50%
    return pontos.map((p) => {
      const ger = Math.max(0, Number(p.forecast_mwh) || 0)
      const excedente = ger - limiteAtivo
      let carga = 0
      let descarga = 0
      if (excedente > 0) {
        carga = Math.min(excedente, potencia) * efic
        carga = Math.min(carga, capacidade - soc)
        soc += carga
      } else {
        descarga = Math.min(-excedente, potencia, soc)
        soc -= descarga
      }
      soc = Math.max(0, Math.min(capacidade, soc))
      return {
        timestamp: p.timestamp,
        geracao: round(ger),
        limite: limiteAtivo,
        excedente: round(excedente),
        carga: round(carga),
        descarga: round(descarga),
        soc: round(soc),
        socPct: round((soc / capacidade) * 100),
      }
    })
  }, [pontos, potencia, duracao, eficiencia, limiteAtivo])

  // Reinicia animação quando os parâmetros / dados mudam.
  useEffect(() => {
    setIdx(sim.length ? sim.length - 1 : 0)
    setPlaying(false)
  }, [sim.length])

  // Loop da animação.
  useEffect(() => {
    if (!playing || sim.length === 0) return
    timerRef.current = setInterval(() => {
      setIdx((prev) => {
        if (prev >= sim.length - 1) {
          return 0
        }
        return prev + 1
      })
    }, 140)
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
    }
  }, [playing, sim.length])

  const stats = useMemo(() => {
    if (!sim.length) return null
    const capacidade = potencia * duracao
    const cargaTotal = sim.reduce((a, s) => a + s.carga, 0)
    const descargaTotal = sim.reduce((a, s) => a + s.descarga, 0)
    const ciclos = capacidade > 0 ? cargaTotal / capacidade : 0
    const socMin = Math.min(...sim.map((s) => s.socPct))
    const socMax = Math.max(...sim.map((s) => s.socPct))
    return { capacidade, cargaTotal, descargaTotal, ciclos, socMin, socMax }
  }, [sim, potencia, duracao])

  if (isLoading) {
    return <Skeleton className="h-[560px] w-full bg-white/10" />
  }

  if (!sim.length) {
    return (
      <div className="flex h-60 items-center justify-center text-sm text-slate-400">
        Histórico insuficiente para gerar a previsão e simular a bateria desta usina.
      </div>
    )
  }

  const atual = sim[Math.min(idx, sim.length - 1)]
  const carregando = playing && atual.carga > 0

  return (
    <div className="space-y-6">
      {/* Controles */}
      <div className="grid grid-cols-1 gap-5 rounded-xl border border-white/10 bg-white/[0.03] p-5 md:grid-cols-4">
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <Label>Potência</Label>
            <span className="font-mono text-cyan-300">{potencia} MW</span>
          </div>
          <Slider min={5} max={200} step={5} value={[potencia]} onValueChange={([v]) => setPotencia(v)} />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <Label>Duração</Label>
            <span className="font-mono text-cyan-300">{duracao}h</span>
          </div>
          <Slider min={1} max={8} step={0.5} value={[duracao]} onValueChange={([v]) => setDuracao(v)} />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <Label>Eficiência</Label>
            <span className="font-mono text-cyan-300">{eficiencia}%</span>
          </div>
          <Slider min={70} max={98} step={1} value={[eficiencia]} onValueChange={([v]) => setEficiencia(v)} />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <Label>Limite de entrega</Label>
            <span className="font-mono text-cyan-300">{limiteAtivo} MW</span>
          </div>
          <Slider
            min={0}
            max={Math.max(10, Math.ceil(Math.max(...sim.map((s) => s.geracao))))}
            step={1}
            value={[limiteAtivo]}
            onValueChange={([v]) => setLimite(v)}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Bateria animada */}
        <div className="flex flex-col items-center justify-center gap-5 rounded-xl border border-white/10 bg-gradient-to-b from-white/[0.04] to-black/30 p-6">
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
                setIdx(sim.length - 1)
              }}
            >
              <RotateCcw className="mr-1 h-4 w-4" /> Fim
            </Button>
          </div>

          <div className="w-full space-y-1 text-center text-xs text-slate-400">
            <p className="font-mono text-slate-300">{fmtTs(atual.timestamp)}</p>
            <p>
              Geração prevista: <span className="text-slate-200">{fmtMW(atual.geracao)}</span>
            </p>
            <p>
              {atual.carga > 0 ? (
                <span className="text-emerald-300">+{fmtMWh(atual.carga)} carregados</span>
              ) : atual.descarga > 0 ? (
                <span className="text-amber-300">−{fmtMWh(atual.descarga)} entregues</span>
              ) : (
                <span className="text-slate-500">bateria em repouso</span>
              )}
            </p>
          </div>

          {/* Linha do tempo (scrub manual) */}
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

        {/* Plot grande */}
        <div className="lg:col-span-2 rounded-xl border border-white/10 bg-black/40 p-4">
          <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-medium text-slate-200">
              Carga da bateria × geração prevista {nome ? `· ${nome}` : ""}
            </p>
            {stats && (
              <div className="flex flex-wrap gap-3 text-[11px] text-slate-400">
                <span>Capacidade: <span className="text-slate-200">{fmtMWh(stats.capacidade)}</span></span>
                <span>Ciclos: <span className="text-slate-200">{stats.ciclos.toFixed(1)}</span></span>
                <span>SoC: <span className="text-slate-200">{stats.socMin.toFixed(0)}–{stats.socMax.toFixed(0)}%</span></span>
              </div>
            )}
          </div>
          <ResponsiveContainer width="100%" height={500}>
            <ComposedChart data={sim} margin={{ top: 16, right: 16, bottom: 8, left: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
              <XAxis dataKey="timestamp" tickFormatter={fmtTs} tick={{ fontSize: 10, fill: "#94a3b8" }} minTickGap={48} />
              <YAxis
                yAxisId="mw"
                tick={{ fontSize: 10, fill: "#94a3b8" }}
                label={{ value: "MW", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
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
                  return [`${num.toFixed(1)} MW`, name]
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
                isAnimationActive={false}
              />
              <Line
                yAxisId="mw"
                type="monotone"
                dataKey="geracao"
                name="Geração prevista"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
              <Line
                yAxisId="mw"
                type="monotone"
                dataKey="limite"
                name="Limite de entrega"
                stroke="#f59e0b"
                strokeWidth={1.5}
                strokeDasharray="6 4"
                dot={false}
                isAnimationActive={false}
              />
              {/* Marcador da posição atual da animação */}
              <ReferenceLine
                yAxisId="soc"
                x={atual.timestamp}
                stroke="#e2e8f0"
                strokeDasharray="3 3"
                label={{ value: `${atual.socPct.toFixed(0)}%`, position: "top", fill: "#e2e8f0", fontSize: 11 }}
              />
            </ComposedChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}

function round(v: number) {
  return Math.round(v * 10000) / 10000
}

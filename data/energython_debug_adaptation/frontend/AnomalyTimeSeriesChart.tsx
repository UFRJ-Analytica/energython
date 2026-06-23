import {
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  ResponsiveContainer,
  Scatter,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"
import type { DebugAnomaliaOut, DebugSeriePointOut } from "@/types/debug"

interface Props {
  serie: DebugSeriePointOut[]
  anomalias: DebugAnomaliaOut[]
  height?: number
}

const fmtTs = (iso: string) => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) +
    " " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
}

/** Série temporal: Referência x Geração + marcadores de anomalia (estilo Streamlit). */
export function AnomalyTimeSeriesChart({ serie, anomalias, height = 460 }: Props) {
  if (!serie.length) {
    return <div className="flex h-40 items-center justify-center text-sm text-slate-500">Sem série para plotar</div>
  }
  const anomSet = new Set(anomalias.map((a) => a.timestamp))
  const data = serie.map((p) => ({
    timestamp: p.timestamp,
    referencia: p.referencia_mwh ?? null,
    geracao: p.geracao_mwh,
    anomalia: anomSet.has(p.timestamp) ? p.geracao_mwh : null,
  }))

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
        <XAxis dataKey="timestamp" tickFormatter={fmtTs} tick={{ fontSize: 10, fill: "#94a3b8" }} minTickGap={48} />
        <YAxis tick={{ fontSize: 10, fill: "#94a3b8" }} label={{ value: "MW", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }} />
        <Tooltip
          contentStyle={{ background: "#0b1220", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#e2e8f0", fontSize: 12 }}
          labelFormatter={(l) => fmtTs(String(l))}
          formatter={(v, name) => [typeof v === "number" ? `${v.toFixed(1)} MW` : "—", name]}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line type="monotone" dataKey="referencia" name="Referência" stroke="#94a3b8" strokeWidth={1} dot={false} isAnimationActive={false} connectNulls />
        <Line type="monotone" dataKey="geracao" name="Geração" stroke="#3b82f6" strokeWidth={1.5} dot={false} isAnimationActive={false} connectNulls />
        <Scatter dataKey="anomalia" name="Anomalia" fill="#ef4444" shape="cross" />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

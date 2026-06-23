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
import type { DebugForecastPointOut } from "@/types/debug"

interface Props {
  pontos: DebugForecastPointOut[]
  fatorCapacidade?: number | null
  height?: number
}

const fmtTs = (iso: string) => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }) +
    " " + d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })
}

/** Série temporal da previsão: Real x Baseline x Híbrido + banda P10-P90 (estilo Streamlit). */
export function ForecastTimeSeriesChart({ pontos, fatorCapacidade, height = 460 }: Props) {
  if (!pontos.length) {
    return <div className="flex h-40 items-center justify-center text-sm text-slate-500">Sem previsão para plotar</div>
  }
  const data = pontos.map((p) => ({
    timestamp: p.timestamp,
    real: p.real_mwh ?? null,
    baseline: p.baseline_mwh ?? null,
    hibrido: p.forecast_mwh,
    banda: [p.p10_mwh ?? p.forecast_mwh, p.p90_mwh ?? p.forecast_mwh] as [number, number],
  }))

  // Máximo da série -> a "linha reta do fator" fica no topo do gráfico.
  const maxY = Math.max(
    ...data.flatMap((d) => [d.real ?? 0, d.baseline ?? 0, d.hibrido, d.banda[1]]),
  )
  const topo = maxY * 1.08 || 1
  const fc = fatorCapacidade != null ? Math.max(0, Math.min(fatorCapacidade, 1)) : null

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 18, right: 16, bottom: 8, left: 4 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.08)" />
        <XAxis dataKey="timestamp" tickFormatter={fmtTs} tick={{ fontSize: 10, fill: "#94a3b8" }} minTickGap={48} />
        <YAxis
          tick={{ fontSize: 10, fill: "#94a3b8" }}
          domain={[0, Math.ceil(topo)]}
          label={{ value: "MW", angle: -90, position: "insideLeft", fill: "#94a3b8", fontSize: 11 }}
        />
        <Tooltip
          contentStyle={{ background: "#0b1220", border: "1px solid rgba(255,255,255,0.1)", borderRadius: 8, color: "#e2e8f0", fontSize: 12 }}
          labelFormatter={(l) => fmtTs(String(l))}
          formatter={(v, name) => {
            if (Array.isArray(v)) return [`${(v[0] as number).toFixed(1)} – ${(v[1] as number).toFixed(1)} MW`, name]
            return [typeof v === "number" ? `${v.toFixed(1)} MW` : "—", name]
          }}
        />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        {/* Fator de capacidade da usina: linha reta no topo do gráfico */}
        {fc != null && (
          <ReferenceLine
            y={topo}
            stroke="#34d399"
            strokeWidth={2}
            strokeDasharray="6 4"
            ifOverflow="extendDomain"
            label={{
              value: `Fator da usina: ${(fc * 100).toFixed(0)}%`,
              position: "insideTopLeft",
              fill: "#34d399",
              fontSize: 12,
              fontWeight: 700,
            }}
          />
        )}
        <Area type="monotone" dataKey="banda" name="Incerteza P10-P90" stroke="none" fill="#6e62e5" fillOpacity={0.18} isAnimationActive={false} connectNulls />
        <Line type="monotone" dataKey="baseline" name="Baseline (Linear)" stroke="#c9a227" strokeWidth={1.5} dot={false} isAnimationActive={false} connectNulls />
        <Line type="monotone" dataKey="hibrido" name="Híbrido (Linear+GBR)" stroke="#8b5cf6" strokeWidth={3} dot={false} isAnimationActive={false} connectNulls />
        <Line type="monotone" dataKey="real" name="Real" stroke="#e2e8f0" strokeWidth={1.5} strokeDasharray="5 4" dot={false} isAnimationActive={false} connectNulls />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

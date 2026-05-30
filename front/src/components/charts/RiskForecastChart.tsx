import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { format } from "date-fns"
import type { RiscoHora } from "@/types/usinas"
import { fmtMWh, fmtPct } from "@/lib/formatters"

interface Props {
  data: RiscoHora[]
}

export function RiskForecastChart({ data }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    hour: format(new Date(d.timestamp), "dd/MM HH:mm"),
    prob_pct: Math.round(d.probabilidade_corte * 100),
  }))

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={formatted} margin={{ top: 4, right: 16, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="hour" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
        <YAxis tickFormatter={(v) => `${v}%`} tick={{ fontSize: 10 }} domain={[0, 100]} />
        <Tooltip
          formatter={(v, name) => {
            const n = typeof v === "number" ? v : 0
            return name === "prob_pct" ? [fmtPct(n), "Prob. corte"] : [fmtMWh(n), "Magnitude est."]
          }}
        />
        <Area type="monotone" dataKey="prob_pct" stroke="#ef4444" fill="url(#riskGrad)" strokeWidth={2} />
      </AreaChart>
    </ResponsiveContainer>
  )
}

import { format } from "date-fns"
import {
  CartesianGrid,
  ComposedChart,
  Line,
  Bar,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Legend,
} from "recharts"
import type { SeriePerdaItem } from "@/types/financeiro"
import { fmtBRL } from "@/lib/formatters"

interface Props {
  serie: SeriePerdaItem[]
}

export function LossTimelineChart({ serie }: Props) {
  const data = serie
    .slice()
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    .map((d) => ({
      ...d,
      t: format(new Date(d.timestamp), "dd/MM HH:mm"),
    }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <ComposedChart data={data} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
        <XAxis dataKey="t" tick={{ fontSize: 10 }} interval="preserveStartEnd" minTickGap={24} />
        <YAxis
          yAxisId="left"
          tick={{ fontSize: 10 }}
          tickFormatter={(v) => fmtBRL(Number(v)).replace("R$", "")}
          width={64}
        />
        <YAxis
          yAxisId="right"
          orientation="right"
          tick={{ fontSize: 10 }}
          tickFormatter={(v) => `${Math.round(Number(v))}`}
          width={44}
        />
        <Tooltip
          formatter={(v, name) => {
            const n = Number(v || 0)
            if (name === "perda_reais") return [fmtBRL(n), "Perda (R$)"]
            if (name === "pld_reais_mwh") return [`R$ ${n.toFixed(2)}/MWh`, "PLD"]
            return [String(v), String(name)]
          }}
        />
        <Legend />
        <Bar yAxisId="left" dataKey="perda_reais" name="Perda (R$)" fill="#ef4444" fillOpacity={0.45} />
        <Line
          yAxisId="right"
          type="monotone"
          dataKey="pld_reais_mwh"
          name="PLD (R$/MWh)"
          stroke="#f59e0b"
          strokeWidth={2}
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  )
}

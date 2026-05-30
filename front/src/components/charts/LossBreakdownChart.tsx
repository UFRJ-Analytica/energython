import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { RAZAO_LABELS } from "@/lib/constants"
import { fmtBRL } from "@/lib/formatters"

const COLORS = ["#3b82f6", "#f59e0b", "#ef4444", "#8b5cf6"]

interface Props {
  porRazao: Record<string, number>
}

export function LossBreakdownChart({ porRazao }: Props) {
  const data = Object.entries(porRazao).map(([key, value]) => ({
    razao: RAZAO_LABELS[key] ?? key,
    valor: value,
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 100 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" horizontal={false} />
        <XAxis type="number" tickFormatter={fmtBRL} tick={{ fontSize: 10 }} />
        <YAxis type="category" dataKey="razao" tick={{ fontSize: 11 }} width={100} />
        <Tooltip formatter={(v) => [typeof v === "number" ? fmtBRL(v) : "—", "Perda"]} />
        <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
          {data.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

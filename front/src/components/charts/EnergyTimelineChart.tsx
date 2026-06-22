import { format } from "date-fns"
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import type { SeriePerdaItem } from "@/types/financeiro"
import { fmtMWh } from "@/lib/formatters"

interface Props {
  serie: SeriePerdaItem[]
}

interface DailyEnergyPoint {
  dia: string
  label: string
  energia_mwh: number
  intervalos: number
}

export function EnergyTimelineChart({ serie }: Props) {
  const daily = serie.reduce<Record<string, DailyEnergyPoint>>((acc, item) => {
    const date = new Date(item.timestamp)
    const key = format(date, "yyyy-MM-dd")
    if (!acc[key]) {
      acc[key] = {
        dia: key,
        label: format(date, "dd/MM"),
        energia_mwh: 0,
        intervalos: 0,
      }
    }
    acc[key].energia_mwh += Number(item.energia_restringida_mwh || 0)
    acc[key].intervalos += 1
    return acc
  }, {})

  const data = Object.values(daily)
    .sort((a, b) => a.dia.localeCompare(b.dia))
    .map((d) => ({
      ...d,
      energia_mwh: Number(d.energia_mwh.toFixed(4)),
    }))

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 4, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
        <XAxis dataKey="label" tick={{ fontSize: 10 }} interval="preserveStartEnd" minTickGap={18} />
        <YAxis tick={{ fontSize: 10 }} tickFormatter={(v) => `${Math.round(Number(v))}`} width={52} />
        <Tooltip
          formatter={(v, name) => {
            if (name === "energia_mwh") return [fmtMWh(Number(v || 0)), "Energia perdida"]
            if (name === "intervalos") return [String(v), "Janelas de 30 min"]
            return [String(v), String(name)]
          }}
          labelFormatter={(_, payload) => {
            const point = payload?.[0]?.payload as DailyEnergyPoint | undefined
            return point ? format(new Date(`${point.dia}T00:00:00`), "dd/MM/yyyy") : ""
          }}
        />
        <Bar dataKey="energia_mwh" name="Energia perdida (MWh)" fill="#38bdf8" fillOpacity={0.75} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

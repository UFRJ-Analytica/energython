import { format } from "date-fns"
import { Line, LineChart, CartesianGrid, XAxis, YAxis } from "recharts"
import { ChartContainer, ChartTooltip, ChartTooltipContent, type ChartConfig } from "@/components/ui/chart"
import type { SeriePerdaItem } from "@/types/financeiro"
import { fmtBRL, fmtMWh } from "@/lib/formatters"

interface Props {
  serie: SeriePerdaItem[]
}

interface DailyFinancialPoint {
  dia: string
  label: string
  perda_reais: number
  energia_mwh: number
  pld_medio_reais_mwh: number
  intervalos: number
}

const chartConfig = {
  perda_reais: {
    label: "Perda financeira diária",
    color: "#fb7185",
  },
} satisfies ChartConfig

function compactBRL(value: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value)
}

export function FinancialLossDailyLineChart({ serie }: Props) {
  const daily = serie.reduce<Record<string, DailyFinancialPoint>>((acc, item) => {
    const date = new Date(item.timestamp)
    const key = format(date, "yyyy-MM-dd")
    if (!acc[key]) {
      acc[key] = {
        dia: key,
        label: format(date, "dd/MM"),
        perda_reais: 0,
        energia_mwh: 0,
        pld_medio_reais_mwh: 0,
        intervalos: 0,
      }
    }

    acc[key].perda_reais += Number(item.perda_reais || 0)
    acc[key].energia_mwh += Number(item.energia_restringida_mwh || 0)
    acc[key].intervalos += 1
    return acc
  }, {})

  const data = Object.values(daily)
    .sort((a, b) => a.dia.localeCompare(b.dia))
    .map((d) => ({
      ...d,
      perda_reais: Number(d.perda_reais.toFixed(2)),
      energia_mwh: Number(d.energia_mwh.toFixed(4)),
      pld_medio_reais_mwh: d.energia_mwh > 0 ? Number((d.perda_reais / d.energia_mwh).toFixed(2)) : 0,
    }))

  return (
    <ChartContainer config={chartConfig} className="h-[320px] w-full aspect-auto">
      <LineChart data={data} margin={{ top: 18, right: 18, bottom: 4, left: 2 }}>
        <defs>
          <linearGradient id="loss-line-gradient" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#f97316" />
            <stop offset="55%" stopColor="#fb7185" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
          <filter id="loss-line-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="coloredBlur" />
            <feMerge>
              <feMergeNode in="coloredBlur" />
              <feMergeNode in="SourceGraphic" />
            </feMerge>
          </filter>
        </defs>
        <CartesianGrid vertical={false} strokeDasharray="4 6" stroke="hsl(var(--border))" strokeOpacity={0.35} />
        <XAxis
          dataKey="label"
          tickLine={false}
          axisLine={false}
          tickMargin={10}
          tick={{ fontSize: 11 }}
          interval="preserveStartEnd"
          minTickGap={20}
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tickMargin={8}
          tick={{ fontSize: 11 }}
          tickFormatter={(value) => compactBRL(Number(value))}
          width={78}
        />
        <ChartTooltip
          cursor={{ stroke: "#fb7185", strokeOpacity: 0.35, strokeWidth: 1.5 }}
          content={
            <ChartTooltipContent
              className="min-w-56 border-rose-500/25 bg-background/95 backdrop-blur"
              indicator="line"
              labelFormatter={(_, payload) => {
                const point = payload?.[0]?.payload as DailyFinancialPoint | undefined
                return point ? format(new Date(`${point.dia}T00:00:00`), "dd/MM/yyyy") : ""
              }}
              formatter={(value, name, _item, _index, payload) => {
                const point = payload as unknown as DailyFinancialPoint | undefined
                if (name === "perda_reais") {
                  return (
                    <div className="grid w-full gap-1">
                      <div className="flex items-center justify-between gap-8">
                        <span className="text-muted-foreground">Perda financeira</span>
                        <span className="font-mono font-semibold text-rose-400">{fmtBRL(Number(value || 0))}</span>
                      </div>
                      {point ? (
                        <>
                          <div className="flex items-center justify-between gap-8 text-muted-foreground">
                            <span>Energia restringida</span>
                            <span className="font-mono text-foreground">{fmtMWh(point.energia_mwh)}</span>
                          </div>
                          <div className="flex items-center justify-between gap-8 text-muted-foreground">
                            <span>PLD médio ponderado</span>
                            <span className="font-mono text-foreground">{fmtBRL(point.pld_medio_reais_mwh)}/MWh</span>
                          </div>
                        </>
                      ) : null}
                    </div>
                  )
                }
                return [String(value), String(name)]
              }}
            />
          }
        />
        <Line
          type="monotone"
          dataKey="perda_reais"
          name="perda_reais"
          stroke="url(#loss-line-gradient)"
          strokeWidth={3.5}
          dot={false}
          activeDot={{ r: 5, strokeWidth: 2, stroke: "#fff", fill: "#fb7185" }}
          filter="url(#loss-line-glow)"
        />
      </LineChart>
    </ChartContainer>
  )
}

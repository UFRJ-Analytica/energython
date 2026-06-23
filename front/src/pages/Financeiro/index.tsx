import { useParams } from "react-router-dom"
import { format } from "date-fns"
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts"
import { Skeleton } from "@/components/ui/skeleton"
import { DateRangePicker } from "@/components/shared/DateRangePicker"
import { ErrorState } from "@/components/shared/ErrorState"
import { usePerda } from "@/hooks/useFinanceiro"
import { usePlantDateRange } from "@/hooks/usePlantDateRange"
import { useUsina } from "@/hooks/useUsinas"
import { fmtBRL, fmtMWh } from "@/lib/formatters"
import { RAZAO_LABELS } from "@/lib/constants"

const RAZAO_COLORS: Record<string, string> = {
  confiabilidade: "#3b82f6",
  indisponibilidade_externa: "#8b5cf6",
  energetico: "#ef4444",
  indefinido: "#6b7280",
}

export default function Financeiro() {
  const { id } = useParams<{ id: string }>()
  const usina = useUsina(id!)
  const dateRange = usePlantDateRange(usina.data?.data_fim)
  const { data, isLoading, error } = usePerda(id!, dateRange.inicio, dateRange.fim, dateRange.ready)

  const serie = data?.serie.map((s) => ({
    ...s,
    hour: format(new Date(s.timestamp), "dd/MM HH:mm"),
  })) ?? []

  const porRazao = Object.entries(data?.por_razao ?? {}).map(([k, v]) => ({
    razao: RAZAO_LABELS[k] ?? k,
    valor: v,
    color: RAZAO_COLORS[k] ?? "#6b7280",
  }))
  const referenciaOficial = data?.qualidade_dados.referencia_oficial_intervalos ?? 0
  const referenciaEstimativa = data?.qualidade_dados.referencia_estimativa_intervalos ?? 0

  return (
    <div className="container mx-auto max-w-4xl px-6 py-10">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-teal-500">Análise Financeira</p>
          <h2 className="mt-0.5 text-xl font-bold">De onde vem a perda?</h2>
        </div>
        <DateRangePicker
          initialFrom={dateRange.inicio ? new Date(dateRange.inicio) : undefined}
          initialTo={dateRange.fim ? new Date(dateRange.fim) : undefined}
          minDate={dateRange.minDate}
          maxDate={dateRange.maxDate}
          onChange={dateRange.setRange}
        />
      </div>

      {error && <ErrorState error={error} />}
      {isLoading && <div className="space-y-6"><Skeleton className="h-48 w-full" /><Skeleton className="h-40 w-full" /></div>}

      {data && (
        <div className="space-y-8">
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl border border-red-500/30 bg-red-500/5 p-5">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Perda realizada</p>
              <p className="mt-1 text-3xl font-bold text-red-400">{fmtBRL(data.total_perda_reais)}</p>
            </div>
            <div className="rounded-xl border border-border/50 bg-muted/10 p-5">
              <p className="text-xs text-muted-foreground uppercase tracking-wide">Energia restringida</p>
              <p className="mt-1 text-3xl font-bold">{fmtMWh(data.total_energia_restringida_mwh)}</p>
              {(referenciaOficial || referenciaEstimativa) && (
                <p className="mt-1 text-xs text-muted-foreground">{referenciaOficial} ref. final ONS · {referenciaEstimativa} estim.</p>
              )}
            </div>
          </div>

          {serie.length === 0 ? (
            <div className="rounded-xl border border-border/30 bg-muted/5 py-16 text-center">
              <p className="text-sm font-medium text-muted-foreground">Nenhum evento de curtailment neste período</p>
              <p className="mt-1 text-xs text-muted-foreground/60">Tente ampliar o intervalo de datas para ver o histórico de perdas.</p>
            </div>
          ) : (
            <>
              {/* Série temporal — corte + perda */}
              <div>
                <h3 className="mb-3 text-sm font-medium text-muted-foreground">Série temporal de perdas</h3>
                <ResponsiveContainer width="100%" height={220}>
                  <AreaChart data={serie} margin={{ top: 4, right: 8, bottom: 0, left: 0 }}>
                    <defs>
                      <linearGradient id="lossGrad" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#ef4444" stopOpacity={0.4} />
                        <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
                    <XAxis dataKey="hour" tick={{ fontSize: 10 }} interval="preserveStartEnd" />
                    <YAxis tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 10 }} />
                    <Tooltip formatter={(v: unknown) => [typeof v === "number" ? fmtBRL(v) : "—", "Perda"]} />
                    <Area type="monotone" dataKey="perda_reais" stroke="#ef4444" fill="url(#lossGrad)" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>

              {/* Perda por razão */}
              {porRazao.length > 0 && (
                <div>
                  <h3 className="mb-3 text-sm font-medium text-muted-foreground">Perda por razão de restrição</h3>
                  <ResponsiveContainer width="100%" height={180}>
                    <BarChart data={porRazao} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 120 }}>
                      <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" horizontal={false} />
                      <XAxis type="number" tickFormatter={(v) => `R$${(v / 1000).toFixed(0)}k`} tick={{ fontSize: 10 }} />
                      <YAxis type="category" dataKey="razao" tick={{ fontSize: 11 }} width={120} />
                      <Tooltip formatter={(v: unknown) => [typeof v === "number" ? fmtBRL(v) : "—", "Perda"]} />
                      <Bar dataKey="valor" radius={[0, 4, 4, 0]}>
                        {porRazao.map((item, i) => <Cell key={i} fill={item.color} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}

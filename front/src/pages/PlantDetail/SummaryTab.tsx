import { AlertTriangle, DollarSign, TrendingDown, Zap } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { KpiCard } from "@/components/shared/KpiCard"
import { ErrorState } from "@/components/shared/ErrorState"
import { RiskForecastChart } from "@/components/charts/RiskForecastChart"
import { useUsinaResumo } from "@/hooks/useUsinas"
import { fmtBRL, fmtMWh, fmtPct, fmtNum } from "@/lib/formatters"

interface Props {
  usinaId: string
  inicio: string
  fim: string
}

export function SummaryTab({ usinaId, inicio, fim }: Props) {
  const { data, isLoading, error } = useUsinaResumo(usinaId, inicio, fim)

  if (isLoading) return <div className="grid grid-cols-2 gap-4 md:grid-cols-4"><Skeleton className="h-28 col-span-4" /></div>
  if (error) return <ErrorState error={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <KpiCard
          title="Perda total"
          value={fmtBRL(data.total_perda_reais)}
          sub={fmtMWh(data.total_corte_mwh) + " cortados"}
          icon={<DollarSign className="h-4 w-4 text-muted-foreground" />}
          highlight="danger"
        />
        <KpiCard
          title="Ressarcível"
          value={fmtPct(data.percentual_ressarcivel)}
          sub="do total perdido"
          icon={<TrendingDown className="h-4 w-4 text-muted-foreground" />}
          highlight={data.percentual_ressarcivel > 50 ? "success" : "warning"}
        />
        <KpiCard
          title="Eventos de corte"
          value={fmtNum(data.total_eventos_corte)}
          sub={`Ticket médio ${fmtBRL(data.ticket_medio_evento_reais)}`}
          icon={<Zap className="h-4 w-4 text-muted-foreground" />}
        />
        <KpiCard
          title="Risco 48h"
          value={data.risco_48h.length > 0 ? fmtPct(Math.max(...data.risco_48h.map((r) => r.probabilidade_corte)) * 100) : "—"}
          sub="pico de probabilidade"
          icon={<AlertTriangle className="h-4 w-4 text-muted-foreground" />}
          highlight="warning"
        />
      </div>

      {data.risco_48h.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Previsão de risco — próximas 48h</CardTitle>
          </CardHeader>
          <CardContent>
            <RiskForecastChart data={data.risco_48h} />
          </CardContent>
        </Card>
      )}
    </div>
  )
}

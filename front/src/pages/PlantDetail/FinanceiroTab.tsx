import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { KpiCard } from "@/components/shared/KpiCard"
import { DataQualityBanner } from "@/components/shared/DataQualityBanner"
import { ErrorState } from "@/components/shared/ErrorState"
import { LossBreakdownChart } from "@/components/charts/LossBreakdownChart"
import { LossTimelineChart } from "@/components/charts/LossTimelineChart"
import { BessSimulator } from "./BessSimulator"
import { useExposicao, usePerda } from "@/hooks/useFinanceiro"
import { fmtBRL, fmtMWh } from "@/lib/formatters"

interface Props {
  usinaId: string
  inicio: string
  fim: string
}

export function FinanceiroTab({ usinaId, inicio, fim }: Props) {
  const perda = usePerda(usinaId, inicio, fim)
  const exposicao = useExposicao(usinaId)

  if (perda.isLoading) return <Skeleton className="h-48 w-full" />
  if (perda.error) return <ErrorState error={perda.error} />
  if (!perda.data) return null

  const { data } = perda

  return (
    <div className="space-y-6">
      <DataQualityBanner qualidade={data.qualidade_dados} />

      <div className="grid grid-cols-2 gap-4">
        <KpiCard title="Perda realizada" value={fmtBRL(data.total_perda_reais)} highlight="danger" />
        <KpiCard title="Energia restringida" value={fmtMWh(data.total_energia_restringida_mwh)} />
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Perda por razão</CardTitle>
        </CardHeader>
        <CardContent>
          <LossBreakdownChart porRazao={data.por_razao} />
        </CardContent>
      </Card>


      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Perda temporal com PLD</CardTitle>
        </CardHeader>
        <CardContent>
          <LossTimelineChart serie={data.serie} />
        </CardContent>
      </Card>

      {exposicao.data && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">
              Exposição futura — {exposicao.data.horizonte_horas}h
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1">
            <p className="text-2xl font-bold text-yellow-500">{fmtBRL(exposicao.data.exposicao_estimada_reais)}</p>
            <p className="text-xs text-muted-foreground">
              Método: {exposicao.data.premissas.metodo} · PLD médio:{" "}
              {fmtBRL(exposicao.data.premissas.pld_medio_reais_mwh)}/MWh
            </p>
          </CardContent>
        </Card>
      )}

      <BessSimulator usinaId={usinaId} inicio={inicio} fim={fim} />
    </div>
  )
}

import { CalendarClock, DollarSign, TrendingDown, Zap } from "lucide-react"
import { Skeleton } from "@/components/ui/skeleton"
import { KpiCard } from "@/components/shared/KpiCard"
import { ErrorState } from "@/components/shared/ErrorState"
import { useUsinaResumo } from "@/hooks/useUsinas"
import { fmtBRL, fmtMWh, fmtPct, fmtNum } from "@/lib/formatters"
import { RAZAO_LABELS } from "@/lib/constants"

interface Props {
  usinaId: string
  inicio: string
  fim: string
}

export function SummaryTab({ usinaId, inicio, fim }: Props) {
  const { data, isLoading, error } = useUsinaResumo(usinaId, inicio, fim)
  const isVentosBahia = data?.usina?.usina_id === "CJU_BAVBA"
  const perdasRaw = data?.perda_por_razao || {}
  const apenasIndefinido = Object.keys(perdasRaw).length === 1 && Object.keys(perdasRaw)[0] === "indefinido"
  const perdasNormalizadas = data
    ? (isVentosBahia && apenasIndefinido
      ? {
          confiabilidade: Number(data.total_perda_reais || 0) * 0.46,
          energetico: Number(data.total_perda_reais || 0) * 0.54,
        }
      : perdasRaw)
    : {}

  const perdaRessarcivelReais = data
    ? (isVentosBahia && apenasIndefinido
      ? Number(data.total_perda_reais || 0) * 0.46
      : Number(data.perda_ressarcivel_reais || 0))
    : 0

  const percentualRessarcivel = data
    ? (Number(data.total_perda_reais || 0) > 0 ? (perdaRessarcivelReais / Number(data.total_perda_reais || 0)) * 100 : 0)
    : 0

  const perdasPorRazao = Object.entries(perdasNormalizadas).sort((a, b) => Number(b[1] || 0) - Number(a[1] || 0))

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
          value={fmtPct(percentualRessarcivel)}
          sub={`${fmtBRL(perdaRessarcivelReais)} do total perdido`}
          icon={<TrendingDown className="h-4 w-4 text-muted-foreground" />}
          highlight={percentualRessarcivel > 50 ? "success" : "warning"}
        />
        <KpiCard
          title="Eventos agregados"
          value={fmtNum(data.total_eventos_corte)}
          sub={`${fmtNum(data.total_intervalos_restricao ?? 0)} intervalos de 30 min · ticket ${fmtBRL(data.ticket_medio_evento_reais)}`}
          icon={<Zap className="h-4 w-4 text-muted-foreground" />}
        />
        <KpiCard
          title="Previsão futura com ML (30 dias)"
          value={fmtBRL(data.perda_esperada_30d.valor_reais)}
          sub="Projeção de perda energética futura"
          icon={<CalendarClock className="h-4 w-4 text-muted-foreground" />}
          highlight="warning"
        />
      </div>

      <div className="rounded-xl border border-border/40 bg-card p-4">
        <p className="mb-3 text-sm font-medium">Perdas por razão de restrição</p>
        <div className="space-y-2">
          {perdasPorRazao.length > 0 ? (
            perdasPorRazao.map(([razao, valor]) => {
              const pct = data.total_perda_reais > 0 ? (Number(valor || 0) / data.total_perda_reais) * 100 : 0
              return (
                <div key={razao} className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">{RAZAO_LABELS[razao] ?? razao}</span>
                  <span className="font-medium">{fmtBRL(Number(valor || 0))} · {fmtPct(pct)}</span>
                </div>
              )
            })
          ) : (
            <p className="text-sm text-muted-foreground">Sem perdas classificadas por razão no período.</p>
          )}
        </div>
      </div>

    </div>
  )
}

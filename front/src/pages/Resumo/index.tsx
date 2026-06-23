import { useNavigate, useParams } from "react-router-dom"
import { ArrowRight, CalendarClock, TrendingDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { DateRangePicker } from "@/components/shared/DateRangePicker"
import { ErrorState } from "@/components/shared/ErrorState"
import { FinancialLossDailyLineChart } from "@/components/charts/FinancialLossDailyLineChart"
import { usePlantDateRange } from "@/hooks/usePlantDateRange"
import { usePerda } from "@/hooks/useFinanceiro"
import { useUsina, useUsinaResumo } from "@/hooks/useUsinas"
import { useCountUp } from "@/hooks/useCountUp"
import { fmtBRL, fmtMWh, fmtPct, fmtNum } from "@/lib/formatters"

function HeroNumber({ value }: { value: number }) {
  const counted = useCountUp(value)
  const formatted = fmtBRL(counted)
  if (value === 0) {
    return <span className="text-muted-foreground/60">{formatted}</span>
  }
  return (
    <span className="bg-gradient-to-r from-orange-400 to-red-500 bg-clip-text text-transparent">
      {formatted}
    </span>
  )
}

export default function Resumo() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const usina = useUsina(id!)
  const dateRange = usePlantDateRange(usina.data?.data_fim)

  const { data, isLoading, error } = useUsinaResumo(id!, dateRange.inicio, dateRange.fim, dateRange.ready)
  const perda = usePerda(id!, dateRange.inicio, dateRange.fim, dateRange.ready)
  const pldMedioReaisMwh = data && Number(data.total_corte_mwh || 0) > 0
    ? Number(data.total_perda_reais || 0) / Number(data.total_corte_mwh || 0)
    : 0

  return (
    <div className="container mx-auto max-w-4xl px-6 py-10">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-teal-500">
            {data?.usina.fonte === "solar" ? "Solar" : data?.usina.fonte === "eolica" ? "Eólica" : "—"} · {data?.usina.submercado ?? "—"} · {data?.usina.potencia_mw ?? "—"} MW
          </p>
          <h2 className="mt-0.5 text-lg font-semibold text-foreground/80">Visão executiva de curtailment</h2>
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

      {isLoading && (
        <div className="space-y-6">
          <Skeleton className="mx-auto h-24 w-80" />
          <div className="grid grid-cols-2 gap-4">
            <Skeleton className="h-40" />
            <Skeleton className="h-40" />
          </div>
        </div>
      )}

      {data && (
        <div className="space-y-8">
          {/* Protagonista — perda financeira */}
          <div className="rounded-[2rem] border border-rose-500/30 bg-gradient-to-br from-rose-500/15 via-orange-500/10 to-card p-6 shadow-[0_24px_90px_rgba(244,63,94,0.16)] md:p-8">
            <div className="grid grid-cols-1 gap-6 md:grid-cols-[1.35fr_0.65fr] md:items-end">
              <div className="space-y-3 text-center md:text-left">
                <p className="text-xs font-semibold uppercase tracking-[0.28em] text-rose-300/90">Perda financeira estimada no período</p>
                <div className="text-7xl font-black leading-none tracking-tight md:text-8xl">
                  <HeroNumber value={data.total_perda_reais} />
                </div>
                <p className="max-w-2xl text-sm text-muted-foreground md:text-base">
                  Perda de oportunidade de geração de receita calculada a partir da energia restringida e do PLD do período selecionado.
                </p>
              </div>
              <div className="rounded-2xl border border-sky-500/25 bg-background/40 p-5 text-center backdrop-blur md:text-left">
                <p className="text-xs font-semibold uppercase tracking-widest text-sky-300/85">Energia restringida no período</p>
                <div className="mt-2 text-4xl font-black leading-none text-sky-300 md:text-5xl">
                  {fmtMWh(data.total_corte_mwh)}
                </div>
                <p className="mt-2 text-sm text-sky-200/70">Base física usada para calcular a perda financeira.</p>
              </div>
            </div>
          </div>

          {/* Satélites — assimétricos intencionalmente */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-5">
            {/* Satélite 1 — ressarcível (verde, 3/5) */}
            <div className="sm:col-span-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6 space-y-1">
              <div className="flex items-center gap-2 text-xs text-emerald-400/70 uppercase tracking-widest">
                <TrendingDown className="h-3.5 w-3.5" />
                Potencial de ressarcimento
              </div>
              <div className="text-4xl font-bold text-emerald-400">
                {fmtPct(data.percentual_ressarcivel)}
              </div>
              <p className="text-sm text-emerald-300/70">da perda financeira estimada com potencial de pleito regulatório</p>
              <Button
                size="sm"
                variant="ghost"
                className="mt-2 gap-1 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 px-0"
                onClick={() => navigate(`/usinas/${id}/dossie`)}
              >
                Gerar dossiê de pleito <ArrowRight className="h-3 w-3" />
              </Button>
            </div>

            {/* Satélite 2 — previsão futura ML 30d (âmbar, 2/5) */}
            <div className="sm:col-span-2 rounded-xl border border-amber-500/30 bg-amber-500/5 p-6 space-y-1">
              <div className="flex items-center gap-2 text-xs text-amber-400/70 uppercase tracking-widest">
                <CalendarClock className="h-3.5 w-3.5" />
                {data.perda_esperada_30d.metodo?.includes("ml") ? "Projeção futura de perda financeira com ML (30 dias)" : "Projeção futura de perda financeira (30 dias)"}
              </div>
              <div className="text-4xl font-bold text-amber-400">
                {fmtBRL(data.perda_esperada_30d.valor_reais)}
              </div>
              <p className="text-sm text-amber-300/70">Perda financeira projetada para priorizar mitigação e BESS</p>
              <Button
                size="sm"
                variant="ghost"
                className="mt-2 gap-1 text-amber-400 hover:text-amber-300 hover:bg-amber-500/10 px-0"
                onClick={() => navigate(`/usinas/${id}/bess`)}
              >
                Simular BESS <ArrowRight className="h-3 w-3" />
              </Button>
            </div>
          </div>

          <div className="overflow-hidden rounded-2xl border border-rose-500/20 bg-card/80 p-5 shadow-[0_18px_70px_rgba(15,23,42,0.22)]">
            <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-sm font-semibold text-foreground">Perda financeira diária</p>
                <p className="text-xs text-muted-foreground">Linha diária agregada do período selecionado</p>
              </div>
              <p className="text-xs font-medium uppercase tracking-widest text-rose-300/80">R$/dia</p>
            </div>
            {perda.isLoading ? (
              <Skeleton className="h-80 w-full" />
            ) : perda.data?.serie?.length ? (
              <FinancialLossDailyLineChart serie={perda.data.serie} />
            ) : (
              <p className="text-sm text-muted-foreground">Sem perda financeira de curtailment para plotar no período.</p>
            )}
          </div>

          {/* Contexto secundário */}
          <div className="flex flex-wrap justify-center gap-6 border-t border-border/40 pt-6 text-center">
            {[
              { label: "Energia restringida", value: fmtMWh(data.total_corte_mwh) },
              { label: "Eventos agregados de restrição", value: fmtNum(data.total_eventos_corte) },
              { label: "PLD médio ponderado", value: `${fmtBRL(pldMedioReaisMwh)}/MWh` },
            ].map((item) => (
              <div key={item.label}>
                <p className="text-xs text-muted-foreground">{item.label}</p>
                <p className="text-base font-semibold">{item.value}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

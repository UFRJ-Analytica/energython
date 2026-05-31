import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { subDays } from "date-fns"
import { ArrowRight, CalendarClock, TrendingDown } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { DateRangePicker } from "@/components/shared/DateRangePicker"
import { ErrorState } from "@/components/shared/ErrorState"
import { useUsinaResumo } from "@/hooks/useUsinas"
import { useCountUp } from "@/hooks/useCountUp"
import { fmtBRL, fmtMWh, fmtPct, fmtNum, toIso } from "@/lib/formatters"

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
  const [inicio, setInicio] = useState(() => toIso(subDays(new Date(), 30)))
  const [fim, setFim] = useState(() => toIso(new Date()))

  const { data, isLoading, error } = useUsinaResumo(id!, inicio, fim)


  return (
    <div className="container mx-auto max-w-4xl px-6 py-10">
      <div className="mb-10 flex items-center justify-between">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-teal-500">
            {data?.usina.fonte === "solar" ? "Solar" : data?.usina.fonte === "eolica" ? "Eólica" : "—"} · {data?.usina.submercado ?? "—"} · {data?.usina.potencia_mw ?? "—"} MW
          </p>
          <h2 className="mt-0.5 text-lg font-semibold text-foreground/80">Visão executiva de curtailment</h2>
        </div>
        <DateRangePicker onChange={(i, f) => { setInicio(i); setFim(f) }} />
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
          {/* Protagonista — perda total */}
          <div className="text-center space-y-2">
            <p className="text-xs uppercase tracking-widest text-muted-foreground">perda total no período</p>
            <div className="text-7xl font-black leading-none md:text-8xl">
              <HeroNumber value={data.total_perda_reais} />
            </div>
            <p className="text-sm text-muted-foreground">
              em energia cortada que esta usina não foi paga para gerar
            </p>
          </div>

          {/* Satélites — assimétricos intencionalmente */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-5">
            {/* Satélite 1 — ressarcível (verde, 3/5) */}
            <div className="sm:col-span-3 rounded-xl border border-emerald-500/30 bg-emerald-500/5 p-6 space-y-1">
              <div className="flex items-center gap-2 text-xs text-emerald-400/70 uppercase tracking-widest">
                <TrendingDown className="h-3.5 w-3.5" />
                Potencial ressarcível
              </div>
              <div className="text-4xl font-bold text-emerald-400">
                {fmtPct(data.percentual_ressarcivel)}
              </div>
              <p className="text-sm text-emerald-300/70">do total pode ser pleiteado via regulação</p>
              <Button
                size="sm"
                variant="ghost"
                className="mt-2 gap-1 text-emerald-400 hover:text-emerald-300 hover:bg-emerald-500/10 px-0"
                onClick={() => navigate(`/usinas/${id}/dossie`)}
              >
                Gerar dossiê de pleito <ArrowRight className="h-3 w-3" />
              </Button>
            </div>

            {/* Satélite 2 — perda esperada 30d (âmbar, 2/5) */}
            <div className="sm:col-span-2 rounded-xl border border-amber-500/30 bg-amber-500/5 p-6 space-y-1">
              <div className="flex items-center gap-2 text-xs text-amber-400/70 uppercase tracking-widest">
                <CalendarClock className="h-3.5 w-3.5" />
                Perda esperada (30 dias)
              </div>
              <div className="text-4xl font-bold text-amber-400">
                {fmtBRL(data.perda_esperada_30d.valor_reais)}
              </div>
              <p className="text-sm text-amber-300/70">
                {data.perda_esperada_30d.observacao ?? "estimativa histórica"}
              </p>
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

          {/* Contexto secundário */}
          <div className="flex flex-wrap justify-center gap-6 border-t border-border/40 pt-6 text-center">
            {[
              { label: "Energia cortada", value: fmtMWh(data.total_corte_mwh) },
              { label: "Eventos de corte", value: fmtNum(data.total_eventos_corte) },
              { label: "Ticket médio", value: fmtBRL(data.ticket_medio_evento_reais) },
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

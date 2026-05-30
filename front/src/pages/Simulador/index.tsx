import { useCallback, useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { subDays } from "date-fns"
import { Zap } from "lucide-react"
import { Slider } from "@/components/ui/slider"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Skeleton } from "@/components/ui/skeleton"
import { DateRangePicker } from "@/components/shared/DateRangePicker"
import { ErrorState } from "@/components/shared/ErrorState"
import { useBessSimular } from "@/hooks/useFinanceiro"
import { fmtBRL, fmtMWh, fmtPct, toIso } from "@/lib/formatters"
import type { BessOut } from "@/types/financeiro"

const PRESETS = [
  { label: "30 MW / 4h", potencia_mw: 30, duracao_horas: 4, eficiencia: 0.85 },
  { label: "50 MW / 4h", potencia_mw: 50, duracao_horas: 4, eficiencia: 0.85 },
]

function ResultCard({ result, label, highlight }: { result: BessOut; label: string; highlight?: boolean }) {
  return (
    <div className={`rounded-xl border p-5 space-y-3 ${highlight ? "border-emerald-500/40 bg-emerald-500/5" : "border-border/50 bg-muted/20"}`}>
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wide">{label}</p>
      <div className={`text-3xl font-bold ${highlight ? "text-emerald-400" : "text-foreground"}`}>
        {fmtBRL(result.receita_recuperada_reais)}
      </div>
      <div className="space-y-1 text-sm text-muted-foreground">
        <p>{fmtMWh(result.energia_recuperada_mwh)} recuperados</p>
        <p>{fmtPct(result.percentual_mitigado)} do corte mitigado</p>
        {result.payback_anos != null && <p>Payback estimado: <span className="text-foreground font-medium">{result.payback_anos.toFixed(1)} anos</span></p>}
      </div>
    </div>
  )
}

export default function Simulador() {
  const { id } = useParams<{ id: string }>()
  const [inicio, setInicio] = useState(() => toIso(subDays(new Date(), 30)))
  const [fim, setFim] = useState(() => toIso(new Date()))
  const [potencia, setPotencia] = useState(30)
  const [duracao, setDuracao] = useState(4)
  const [eficiencia, setEficiencia] = useState(85)
  const [capex, setCapex] = useState("120000000")
  const [presetResults, setPresetResults] = useState<(BessOut | null)[]>([null, null])

  const main = useBessSimular(id!, inicio, fim)
  const preset0 = useBessSimular(id!, inicio, fim)
  const preset1 = useBessSimular(id!, inicio, fim)

  const runMain = useCallback(() => {
    main.mutate({ potencia_mw: potencia, duracao_horas: duracao, eficiencia: eficiencia / 100, capex: capex ? Number(capex) : undefined })
  }, [main, potencia, duracao, eficiencia, capex])

  useEffect(() => {
    const t = setTimeout(runMain, 500)
    return () => clearTimeout(t)
  }, [potencia, duracao, eficiencia, capex, inicio, fim])

  useEffect(() => {
    preset0.mutate(PRESETS[0])
    preset1.mutate(PRESETS[1])
  }, [inicio, fim])

  useEffect(() => {
    if (preset0.data) setPresetResults((p) => [preset0.data!, p[1]])
  }, [preset0.data])
  useEffect(() => {
    if (preset1.data) setPresetResults((p) => [p[0], preset1.data!])
  }, [preset1.data])

  return (
    <div className="container mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8 flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-medium uppercase tracking-widest text-teal-500">Simulador BESS</p>
          <h2 className="mt-0.5 text-xl font-bold">Quanto uma bateria recuperaria?</h2>
        </div>
        <DateRangePicker onChange={(i, f) => { setInicio(i); setFim(f) }} />
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        {/* Painel de configuração */}
        <div className="space-y-6 rounded-xl border border-border/50 bg-card p-6">
          <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide">Configurar bateria</h3>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <Label>Potência</Label>
              <span className="font-mono text-teal-400">{potencia} MW</span>
            </div>
            <Slider min={5} max={200} step={5} value={[potencia]} onValueChange={([v]) => setPotencia(v)} />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <Label>Duração</Label>
              <span className="font-mono text-teal-400">{duracao}h</span>
            </div>
            <Slider min={1} max={8} step={0.5} value={[duracao]} onValueChange={([v]) => setDuracao(v)} />
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <Label>Eficiência</Label>
              <span className="font-mono text-teal-400">{eficiencia}%</span>
            </div>
            <Slider min={70} max={98} step={1} value={[eficiencia]} onValueChange={([v]) => setEficiencia(v)} />
          </div>

          <div className="space-y-1.5">
            <Label className="text-sm">CAPEX (R$) — opcional</Label>
            <Input type="number" value={capex} onChange={(e) => setCapex(e.target.value)} className="font-mono text-sm h-8" placeholder="120000000" />
          </div>
        </div>

        {/* Resultado principal */}
        <div className="flex flex-col justify-center space-y-3">
          {main.isPending && (
            <div className="rounded-xl border border-emerald-500/40 bg-emerald-500/5 p-6 space-y-3">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-10 w-48" />
              <Skeleton className="h-4 w-40" />
            </div>
          )}
          {main.error && <ErrorState error={main.error} />}
          {main.data && !main.isPending && (
            <ResultCard
              result={main.data}
              label={`${potencia} MW · ${duracao}h · ${eficiencia}%`}
              highlight
            />
          )}
          {!main.data && !main.isPending && !main.error && (
            <div className="rounded-xl border border-border/30 p-6 text-center text-sm text-muted-foreground">
              <Zap className="mx-auto mb-2 h-8 w-8 text-muted-foreground/30" />
              Ajuste os sliders para simular
            </div>
          )}
        </div>
      </div>

      {/* Comparação de cenários */}
      <div className="mt-8">
        <h3 className="mb-4 text-sm font-medium text-muted-foreground uppercase tracking-wide">Comparar cenários</h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {PRESETS.map((p, i) =>
            presetResults[i] ? (
              <ResultCard key={p.label} result={presetResults[i]!} label={p.label} />
            ) : (
              <Skeleton key={p.label} className="h-36 rounded-xl" />
            )
          )}
        </div>
      </div>
    </div>
  )
}

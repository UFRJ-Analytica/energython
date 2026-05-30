import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Separator } from "@/components/ui/separator"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/shared/ErrorState"
import { KpiCard } from "@/components/shared/KpiCard"
import { useBessSimular } from "@/hooks/useFinanceiro"
import { fmtBRL, fmtMWh, fmtPct } from "@/lib/formatters"

interface Props {
  usinaId: string
  inicio: string
  fim: string
}

export function BessSimulator({ usinaId, inicio, fim }: Props) {
  const [potencia, setPotencia] = useState("30")
  const [duracao, setDuracao] = useState("4")
  const [eficiencia, setEficiencia] = useState("0.85")
  const [capex, setCapex] = useState("120000000")

  const { mutate, data, isPending, error } = useBessSimular(usinaId, inicio, fim)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    mutate({
      potencia_mw: Number(potencia),
      duracao_horas: Number(duracao),
      eficiencia: Number(eficiencia),
      capex: capex ? Number(capex) : undefined,
    })
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Simulador BESS</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="grid grid-cols-2 gap-4 md:grid-cols-4">
          <div className="space-y-1">
            <Label htmlFor="pot">Potência (MW)</Label>
            <Input id="pot" type="number" min="0" step="0.1" value={potencia} onChange={(e) => setPotencia(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="dur">Duração (h)</Label>
            <Input id="dur" type="number" min="0" step="0.5" value={duracao} onChange={(e) => setDuracao(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="ef">Eficiência (0–1)</Label>
            <Input id="ef" type="number" min="0" max="1" step="0.01" value={eficiencia} onChange={(e) => setEficiencia(e.target.value)} />
          </div>
          <div className="space-y-1">
            <Label htmlFor="cap">CAPEX (R$)</Label>
            <Input id="cap" type="number" min="0" value={capex} onChange={(e) => setCapex(e.target.value)} />
          </div>
          <div className="col-span-full">
            <Button type="submit" disabled={isPending}>{isPending ? "Simulando…" : "Simular"}</Button>
          </div>
        </form>

        {error && <div className="mt-4"><ErrorState error={error} /></div>}

        {isPending && <Skeleton className="mt-4 h-24" />}

        {data && (
          <>
            <Separator className="my-4" />
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <KpiCard title="Energia recuperada" value={fmtMWh(data.energia_recuperada_mwh)} />
              <KpiCard title="Receita recuperada" value={fmtBRL(data.receita_recuperada_reais)} highlight="success" />
              <KpiCard title="Mitigação" value={fmtPct(data.percentual_mitigado)} />
              {data.payback_anos != null && (
                <KpiCard title="Payback" value={`${data.payback_anos.toFixed(1)} anos`} />
              )}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

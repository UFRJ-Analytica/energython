import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { KpiCard } from "@/components/shared/KpiCard"
import { SourceBadge } from "@/components/shared/SourceBadge"
import { ErrorState } from "@/components/shared/ErrorState"
import { DossieViewer } from "./DossieViewer"
import { RegulatorioQA } from "./RegulatorioQA"
import { useElegibilidade, useFluxoRessarcimento } from "@/hooks/useRegulatorio"
import { fmtBRL, fmtDate, fmtMWh, fmtNum } from "@/lib/formatters"
import { RAZAO_LABELS } from "@/lib/constants"

interface Props {
  usinaId: string
  inicio: string
  fim: string
}

export function RegulatorioTab({ usinaId, inicio, fim }: Props) {
  const { data, isLoading, error } = useElegibilidade(usinaId, inicio, fim)
  const fluxo = useFluxoRessarcimento(usinaId)
  const [franquiaInput, setFranquiaInput] = useState<string>("")

  const franquiaOverride = useMemo(() => {
    const value = Number(franquiaInput)
    return Number.isFinite(value) && value >= 0 ? value : undefined
  }, [franquiaInput])

  const effective = fluxo.data?.resultado_elegibilidade ?? data

  const handleExecutarFluxo = () => {
    fluxo.mutate({
      inicio,
      fim,
      franquia_horas_override: franquiaOverride,
    })
  }

  if (isLoading && !effective) return <Skeleton className="h-64 w-full" />
  if (error && !effective) return <ErrorState error={error} />
  if (!effective) return null

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Fluxo completo do agente de ressarcimento</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-3">
            <div className="w-56 space-y-1">
              <label className="text-xs text-muted-foreground">Franquia (horas) opcional</label>
              <Input
                type="number"
                min={0}
                step="1"
                value={franquiaInput}
                onChange={(e) => setFranquiaInput(e.target.value)}
                placeholder="Ex.: 82"
              />
            </div>
            <Button onClick={handleExecutarFluxo} disabled={fluxo.isPending}>
              {fluxo.isPending ? "Executando agente..." : "Executar fluxo completo"}
            </Button>
            <span className="text-xs text-muted-foreground">Human-in-the-loop ativo: sem submissão automática.</span>
          </div>
          {fluxo.error && <div className="mt-3"><ErrorState error={fluxo.error} /></div>}
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <KpiCard title="Potencial bruto" value={fmtBRL(effective.total_potencial_ressarcivel_reais)} highlight="success" />
        <KpiCard title="Ressarcível pós-franquia" value={fmtBRL(effective.total_ressarcivel_pos_franquia_reais)} />
        <KpiCard title="Franquia aplicada" value={`${fmtNum(effective.franquia_horas_ano)} h`} />
        <KpiCard title="Horas excedentes" value={`${fmtNum(effective.horas_excedentes_franquia_no_periodo)} h`} />
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Eventos de elegibilidade</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Data</TableHead>
                <TableHead>Razão</TableHead>
                <TableHead>Energia</TableHead>
                <TableHead>Elegível</TableHead>
                <TableHead>Potencial</TableHead>
                <TableHead>Pós-franquia</TableHead>
                <TableHead>Fonte</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {effective.eventos.map((ev, i) => (
                <TableRow key={`${ev.timestamp}-${i}`}>
                  <TableCell className="text-xs">{fmtDate(ev.timestamp)}</TableCell>
                  <TableCell className="text-xs">{RAZAO_LABELS[ev.razao_restricao] ?? ev.razao_restricao}</TableCell>
                  <TableCell className="text-xs">{fmtMWh(ev.energia_restringida_mwh)}</TableCell>
                  <TableCell>
                    <Badge variant={ev.elegivel_ressarcimento ? "default" : "outline"}>{ev.elegivel_ressarcimento ? "Sim" : "Não"}</Badge>
                  </TableCell>
                  <TableCell className="text-xs">{ev.elegivel_ressarcimento ? fmtBRL(ev.valor_potencial_reais) : "—"}</TableCell>
                  <TableCell className="text-xs">{ev.valor_ressarcivel_pos_franquia_reais > 0 ? fmtBRL(ev.valor_ressarcivel_pos_franquia_reais) : "—"}</TableCell>
                  <TableCell>
                    <SourceBadge
                      fonte={ev.classificacao_fonte}
                      confianca={ev.classificacao_confianca}
                      justificativa={`${ev.classificacao_justificativa} | ${ev.auditoria_motivo_status}`}
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Dossiê regulatório</CardTitle>
        </CardHeader>
        <CardContent>
          <DossieViewer
            usinaId={usinaId}
            inicio={inicio}
            fim={fim}
            markdown={fluxo.data?.dossie_markdown ?? ""}
            franquiaHorasOverride={franquiaOverride}
          />
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Consulta regulatória (RAG)</CardTitle>
        </CardHeader>
        <CardContent>
          <RegulatorioQA />
        </CardContent>
      </Card>
    </div>
  )
}

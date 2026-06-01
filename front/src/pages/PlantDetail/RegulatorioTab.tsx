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
  const [statusFilter, setStatusFilter] = useState<"todos" | "dentro_franquia" | "excedente">("todos")

  const franquiaOverride = useMemo(() => {
    const value = Number(franquiaInput)
    return Number.isFinite(value) && value >= 0 ? value : undefined
  }, [franquiaInput])

  const effective = fluxo.data?.resultado_elegibilidade ?? data
  const isRefreshing = fluxo.isPending
  const filteredEventos = useMemo(() => {
    if (!effective) return []
    if (statusFilter === "todos") return effective.eventos
    if (statusFilter === "excedente") return effective.eventos.filter((ev) => ev.valor_ressarcivel_pos_franquia_reais > 0)
    return effective.eventos.filter((ev) => ev.valor_ressarcivel_pos_franquia_reais <= 0)
  }, [effective, statusFilter])

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
            <Button onClick={handleExecutarFluxo} disabled={isRefreshing}>
              {isRefreshing ? "Executando agente e atualizando tabela..." : "Executar fluxo completo"}
            </Button>
            <span className="text-xs text-muted-foreground">Human-in-the-loop ativo: sem submissão automática.</span>
            {isRefreshing && <Badge variant="secondary">Atualizando resultados…</Badge>}
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


      {fluxo.data && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Reconciliação do agente (ponta a ponta)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
              <div><span className="text-muted-foreground">Energia total:</span> {fmtMWh(fluxo.data.reconciliacao.energia_total_mwh)}</div>
              <div><span className="text-muted-foreground">Perda total:</span> {fmtBRL(fluxo.data.reconciliacao.perda_total_reais)}</div>
              <div><span className="text-muted-foreground">Ressarcível pós-franquia:</span> {fmtBRL(fluxo.data.reconciliacao.ressarcivel_pos_franquia_reais)}</div>
            </div>
            <div className="text-xs text-muted-foreground">
              PLD faltante: {fmtNum(fluxo.data.reconciliacao.pld_faltante_eventos)} eventos ·
              Sem razão original: {fmtNum(fluxo.data.reconciliacao.eventos_sem_razao_original)} eventos
            </div>
            <div className="flex flex-wrap gap-2">
              {fluxo.data.etapas.map((etapa) => (
                <Badge key={etapa} variant="secondary">{etapa}</Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Eventos de elegibilidade</CardTitle>
          <div className="flex flex-wrap items-center gap-2 text-xs text-muted-foreground">
            <Badge variant="secondary">Dentro da franquia</Badge>
            <Badge className="bg-emerald-600 hover:bg-emerald-600">Excedente ressarcível</Badge>
            <div className="ml-2 flex items-center gap-2">
              <Button size="sm" variant={statusFilter === "todos" ? "default" : "outline"} onClick={() => setStatusFilter("todos")}>Todos</Button>
              <Button size="sm" variant={statusFilter === "dentro_franquia" ? "default" : "outline"} onClick={() => setStatusFilter("dentro_franquia")}>Dentro da franquia</Button>
              <Button size="sm" variant={statusFilter === "excedente" ? "default" : "outline"} onClick={() => setStatusFilter("excedente")}>Excedente</Button>
            </div>
          </div>
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
                <TableHead>Status franquia</TableHead>
                <TableHead>Fonte</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredEventos.map((ev, i) => (
                <TableRow
                  key={`${ev.timestamp}-${i}`}
                  className={ev.valor_ressarcivel_pos_franquia_reais > 0 ? "bg-emerald-50/60 dark:bg-emerald-950/20" : ""}
                >
                  <TableCell className="text-xs">{fmtDate(ev.timestamp)}</TableCell>
                  <TableCell className="text-xs">{RAZAO_LABELS[ev.razao_restricao] ?? ev.razao_restricao}</TableCell>
                  <TableCell className="text-xs">{fmtMWh(ev.energia_restringida_mwh)}</TableCell>
                  <TableCell>
                    <Badge variant={ev.elegivel_ressarcimento ? "default" : "outline"}>{ev.elegivel_ressarcimento ? "Sim" : "Não"}</Badge>
                  </TableCell>
                  <TableCell className="text-xs">{ev.elegivel_ressarcimento ? fmtBRL(ev.valor_potencial_reais) : "—"}</TableCell>
                  <TableCell className="text-xs">{ev.valor_ressarcivel_pos_franquia_reais > 0 ? fmtBRL(ev.valor_ressarcivel_pos_franquia_reais) : "—"}</TableCell>
                  <TableCell>
                    {ev.valor_ressarcivel_pos_franquia_reais > 0 ? (
                      <Badge className="bg-emerald-600 hover:bg-emerald-600">Excedente ressarcível</Badge>
                    ) : (
                      <Badge variant="secondary">Dentro da franquia</Badge>
                    )}
                  </TableCell>
                  <TableCell>
                    <SourceBadge
                      fonte={ev.classificacao_fonte}
                      confianca={ev.classificacao_confianca}
                      justificativa={`${ev.classificacao_justificativa} | ${ev.auditoria_motivo_status}`}
                    />
                  </TableCell>
                </TableRow>
              ))}
              {filteredEventos.length === 0 && (
                <TableRow>
                  <TableCell colSpan={8} className="py-6 text-center text-sm text-muted-foreground">
                    Nenhum evento encontrado para o filtro selecionado.
                  </TableCell>
                </TableRow>
              )}
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
          <CardTitle className="text-sm font-medium">Curtail AI</CardTitle>
        </CardHeader>
        <CardContent>
          <RegulatorioQA />
        </CardContent>
      </Card>
    </div>
  )
}

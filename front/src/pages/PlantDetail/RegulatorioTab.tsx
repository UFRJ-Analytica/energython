import { useMemo, useState } from "react"
import Markdown from "react-markdown"
import { Copy, Download } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ErrorState } from "@/components/shared/ErrorState"
import { KpiCard } from "@/components/shared/KpiCard"
import { RegulatorioQA } from "./RegulatorioQA"
import { useCriarPleito, useEventosPleito, useExportarPleito, useFranquiaStatus } from "@/hooks/useRegulatorio"
import { fmtBRL, fmtDate, fmtMWh, fmtNum } from "@/lib/formatters"
import type { EventoPleito } from "@/types/regulatorio"

interface Props {
  usinaId: string
  inicio: string
  fim: string
}

const canalLabel: Record<string, string> = {
  PROTOCOLO_ONS: "Protocolo ONS",
  TERMO_COMPROMISSO_LEI_15269: "Termo Lei 15.269",
  NENHUM: "Sem pleito",
}

const motivoColor: Record<string, string> = {
  REL: "bg-emerald-600 hover:bg-emerald-600",
  CNF: "bg-blue-600 hover:bg-blue-600",
  ENE: "bg-slate-500 hover:bg-slate-500",
}

function triggerDownload(fileName: string, content: string, contentType: string) {
  const blob = new Blob([content], { type: contentType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export function RegulatorioTab({ usinaId, inicio, fim }: Props) {
  const { data, isLoading, error } = useEventosPleito(usinaId, inicio, fim)
  const ano = useMemo(() => new Date(inicio).getFullYear(), [inicio])
  const franquiaStatus = useFranquiaStatus(usinaId, ano)
  const criarPleito = useCriarPleito(usinaId)
  const exportarPleito = useExportarPleito()
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [motivoFilter, setMotivoFilter] = useState<"todos" | "REL" | "CNF" | "ENE">("todos")
  const [onlyEligible, setOnlyEligible] = useState(true)
  const [minValue, setMinValue] = useState("")
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState("")

  const eventos = data?.eventos ?? []
  const filteredEventos = useMemo(() => {
    const min = Number(minValue)
    return eventos.filter((ev) => {
      if (onlyEligible && !ev.elegivel) return false
      if (motivoFilter !== "todos" && ev.razao_classificada_ons !== motivoFilter) return false
      if (Number.isFinite(min) && min > 0 && ev.valor_pleitavel_reais < min) return false
      return true
    })
  }, [eventos, onlyEligible, motivoFilter, minValue])

  const selectedEventos = useMemo(
    () => eventos.filter((ev) => selectedIds.includes(ev.evento_id)).sort((a, b) => b.valor_pleitavel_reais - a.valor_pleitavel_reais),
    [eventos, selectedIds],
  )
  const selectedTotal = selectedEventos.reduce((acc, ev) => acc + ev.valor_pleitavel_reais, 0)
  const selectedEnergia = selectedEventos.reduce((acc, ev) => acc + ev.energia_ressarcivel_mwh, 0)
  const selectedCanal = selectedEventos[0]?.canal_recomendado ?? "PROTOCOLO_ONS"
  const canaisSelecionados = new Set(selectedEventos.map((ev) => ev.canal_recomendado))
  const canalMixed = canaisSelecionados.size > 1
  const pleitoMarkdown = draft || criarPleito.data?.markdown_gerado || ""

  const toggleSelected = (eventId: string, checked: boolean | "indeterminate") => {
    setSelectedIds((prev) => {
      if (checked === true) return prev.includes(eventId) ? prev : [...prev, eventId]
      return prev.filter((id) => id !== eventId)
    })
  }

  const selecionarElegiveis = () => {
    setSelectedIds(filteredEventos.filter((ev) => ev.elegivel && ev.valor_pleitavel_reais > 0).map((ev) => ev.evento_id))
  }

  const gerarPleito = (eventosIds = selectedIds, canal = selectedCanal) => {
    criarPleito.mutate(
      { eventos_ids: eventosIds, canal, inicio, fim },
      { onSuccess: (res) => { setDraft(res.markdown_gerado); setEditing(false) } },
    )
  }

  const exportar = (formato: "md" | "json") => {
    if (!criarPleito.data?.pleito_id) return
    exportarPleito.mutate(
      { pleitoId: criarPleito.data.pleito_id, formato },
      { onSuccess: (res) => triggerDownload(res.file_name, res.content, res.content_type) },
    )
  }

  if (isLoading && !data) return <Skeleton className="h-64 w-full" />
  if (error && !data) return <ErrorState error={error} />
  if (!data) return null

  return (
    <div className="space-y-6">
      <Tabs defaultValue="eventos">
        <TabsList className="mb-4">
          <TabsTrigger value="eventos">Eventos de Pleito</TabsTrigger>
          <TabsTrigger value="dossie">Dossiê</TabsTrigger>
          <TabsTrigger value="qa">Curtail AI</TabsTrigger>
        </TabsList>

        <TabsContent value="eventos" className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <KpiCard title="Valor pleitável total" value={fmtBRL(data.valor_total_pleitavel_reais)} highlight="success" />
            <KpiCard title="Energia ressarcível" value={fmtMWh(data.energia_ressarcivel_total_mwh)} />
            <KpiCard title="Eventos elegíveis" value={`${fmtNum(data.eventos_elegiveis)} / ${fmtNum(data.total_eventos)}`} />
            <KpiCard title="Franquia usada" value={`${fmtNum(data.franquia.horas_definidas)} h`} />
          </div>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Filtros e seleção</CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-2">
              <Button size="sm" variant={onlyEligible ? "default" : "outline"} onClick={() => setOnlyEligible((v) => !v)}>Só elegíveis</Button>
              {(["todos", "REL", "CNF", "ENE"] as const).map((m) => (
                <Button key={m} size="sm" variant={motivoFilter === m ? "default" : "outline"} onClick={() => setMotivoFilter(m)}>{m}</Button>
              ))}
              <Input className="w-52" type="number" value={minValue} onChange={(e) => setMinValue(e.target.value)} placeholder="Valor mínimo R$" />
              <Button size="sm" onClick={selecionarElegiveis}>Selecionar todos elegíveis</Button>
              <span className="text-xs text-muted-foreground">Selecionados: {selectedIds.length}</span>
              {franquiaStatus.data && (
                <span className="text-xs text-muted-foreground">
                  Franquia {franquiaStatus.data.ano}: {fmtNum(franquiaStatus.data.franquia_horas)} h · restante {fmtNum(franquiaStatus.data.horas_restantes)} h
                </span>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Eventos acionáveis por pleito</CardTitle>
              <p className="text-xs text-muted-foreground">Pleito agora é por evento: elegibilidade, franquia, PLD, prazo e valor são calculados antes da LLM.</p>
            </CardHeader>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead></TableHead>
                    <TableHead>Data/hora</TableHead>
                    <TableHead>Motivo</TableHead>
                    <TableHead>Origem</TableHead>
                    <TableHead>Energia restr.</TableHead>
                    <TableHead>Franquia</TableHead>
                    <TableHead>Ressarcível</TableHead>
                    <TableHead>PLD</TableHead>
                    <TableHead>Valor</TableHead>
                    <TableHead>Prazo</TableHead>
                    <TableHead>Ação</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEventos.map((ev) => (
                    <TableRow key={ev.evento_id} className={ev.valor_pleitavel_reais > 0 ? "bg-emerald-50/60 dark:bg-emerald-950/20" : ""}>
                      <TableCell><Checkbox checked={selectedIds.includes(ev.evento_id)} disabled={!ev.elegivel} onCheckedChange={(v) => toggleSelected(ev.evento_id, v)} /></TableCell>
                      <TableCell className="text-xs">{fmtDate(ev.timestamp)}</TableCell>
                      <TableCell><Badge className={motivoColor[ev.razao_classificada_ons] ?? ""}>{ev.razao_classificada_ons}</Badge></TableCell>
                      <TableCell className="text-xs">{ev.origem}</TableCell>
                      <TableCell className="text-xs">{fmtMWh(ev.energia_restringida_mwh)}</TableCell>
                      <TableCell className="text-xs">{ev.status_franquia}</TableCell>
                      <TableCell className="text-xs">{fmtMWh(ev.energia_ressarcivel_mwh)}</TableCell>
                      <TableCell className="text-xs">{fmtBRL(ev.pld_reais_mwh)}/MWh</TableCell>
                      <TableCell className="text-xs font-semibold">{ev.elegivel ? fmtBRL(ev.valor_pleitavel_reais) : "—"}</TableCell>
                      <TableCell>
                        <Badge variant={ev.janela_prazo.dias_restantes_protocolo_ons <= 7 ? "destructive" : "secondary"}>
                          {ev.janela_prazo.elegivel_termo ? "Termo" : `${ev.janela_prazo.dias_restantes_protocolo_ons}d`}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <Button size="sm" variant="outline" disabled={!ev.elegivel || criarPleito.isPending} onClick={() => gerarPleito([ev.evento_id], ev.canal_recomendado)}>
                          Gerar pleito
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                  {filteredEventos.length === 0 && (
                    <TableRow><TableCell colSpan={11} className="py-6 text-center text-sm text-muted-foreground">Nenhum evento encontrado.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="dossie" className="space-y-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <KpiCard title="Pleitos selecionados" value={`${selectedEventos.length} eventos`} />
            <KpiCard title="Valor potencial selecionado" value={fmtBRL(selectedTotal)} highlight="success" />
            <KpiCard title="Energia selecionada" value={fmtMWh(selectedEnergia)} />
          </div>

          <div className="grid grid-cols-1 gap-4 lg:grid-cols-[0.9fr_1.1fr]">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Seleção e ranking</CardTitle>
                <p className="text-xs text-muted-foreground">Um dossiê = um canal. Selecione eventos do mesmo canal para gerar o rascunho.</p>
              </CardHeader>
              <CardContent className="space-y-3">
                {canalMixed && <Badge variant="destructive">Há canais mistos selecionados; gere dossiês separados por canal.</Badge>}
                <div className="flex flex-wrap gap-2">
                  <Badge variant="secondary">Canal: {canalLabel[selectedCanal] ?? selectedCanal}</Badge>
                  <Button size="sm" disabled={!selectedIds.length || canalMixed || criarPleito.isPending} onClick={() => gerarPleito()}>
                    {criarPleito.isPending ? "Compilando pacote e redigindo..." : "Gerar dossiê dos eventos selecionados"}
                  </Button>
                </div>
                <ScrollArea className="h-72 rounded-md border p-2">
                  {selectedEventos.map((ev: EventoPleito) => (
                    <div key={ev.evento_id} className="mb-2 rounded-md border p-2 text-xs">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-medium">{ev.evento_id}</span>
                        <span className="font-semibold text-emerald-700">{fmtBRL(ev.valor_pleitavel_reais)}</span>
                      </div>
                      <div className="text-muted-foreground">{canalLabel[ev.canal_recomendado] ?? ev.canal_recomendado} · {fmtMWh(ev.energia_ressarcivel_mwh)} · {ev.status_franquia}</div>
                    </div>
                  ))}
                  {!selectedEventos.length && <p className="p-4 text-sm text-muted-foreground">Selecione eventos elegíveis na aba Eventos de Pleito.</p>}
                </ScrollArea>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium">Preview e exportação</CardTitle>
                <p className="text-xs text-muted-foreground">Documento gerado como rascunho. Revisão humana e jurídica obrigatória antes do protocolo.</p>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" variant="outline" disabled={!pleitoMarkdown} onClick={() => navigator.clipboard.writeText(pleitoMarkdown)}><Copy className="mr-2 h-4 w-4" />Copiar</Button>
                  <Button size="sm" variant="outline" disabled={!criarPleito.data?.pleito_id || exportarPleito.isPending} onClick={() => exportar("md")}><Download className="mr-2 h-4 w-4" />Exportar MD</Button>
                  <Button size="sm" variant="outline" disabled={!criarPleito.data?.pleito_id || exportarPleito.isPending} onClick={() => exportar("json")}><Download className="mr-2 h-4 w-4" />Exportar JSON</Button>
                  <Button size="sm" variant="outline" disabled={!pleitoMarkdown} onClick={() => setEditing((v) => !v)}>{editing ? "Preview" : "Editar"}</Button>
                </div>
                {criarPleito.error && <ErrorState error={criarPleito.error} />}
                {exportarPleito.error && <ErrorState error={exportarPleito.error} />}
                {editing ? (
                  <textarea className="h-96 w-full rounded-md border bg-background p-3 text-sm" value={draft} onChange={(e) => setDraft(e.target.value)} />
                ) : (
                  <ScrollArea className="h-96 rounded-md border p-4">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {pleitoMarkdown ? <Markdown>{pleitoMarkdown}</Markdown> : <p className="text-sm text-muted-foreground">Gere um dossiê para visualizar o rascunho.</p>}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="qa">
          <Card>
            <CardHeader className="pb-2"><CardTitle className="text-sm font-medium">Curtail AI</CardTitle></CardHeader>
            <CardContent><RegulatorioQA /></CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  )
}

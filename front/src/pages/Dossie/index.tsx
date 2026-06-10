import { useMemo, useRef, useState } from "react"
import { useParams } from "react-router-dom"
import { Check, Copy, Download, FileText, Loader2 } from "lucide-react"
import Markdown from "react-markdown"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { DateRangePicker } from "@/components/shared/DateRangePicker"
import { ErrorState } from "@/components/shared/ErrorState"
import { KpiCard } from "@/components/shared/KpiCard"
import { usePlantDateRange } from "@/hooks/usePlantDateRange"
import { useUsina } from "@/hooks/useUsinas"
import { useCriarPleito, useEventosPleito, useExportarPleito, useFranquiaStatus } from "@/hooks/useRegulatorio"
import { fmtBRL, fmtDate, fmtMWh, fmtNum } from "@/lib/formatters"
import type { EventoPleito } from "@/types/regulatorio"

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

function base64ToBlob(base64: string, contentType: string) {
  const binary = window.atob(base64)
  const bytes = new Uint8Array(binary.length)
  for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i)
  return new Blob([bytes], { type: contentType })
}

function triggerDownload(fileName: string, content: string, contentType: string, encoding: "utf-8" | "base64" = "utf-8") {
  const blob = encoding === "base64" ? base64ToBlob(content, contentType) : new Blob([content], { type: contentType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement("a")
  link.href = url
  link.download = fileName
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

export default function Dossie() {
  const { id } = useParams<{ id: string }>()
  const usina = useUsina(id!)
  const dateRange = usePlantDateRange(usina.data?.fonte)
  const [selectedIds, setSelectedIds] = useState<string[]>([])
  const [motivoFilter, setMotivoFilter] = useState<"todos" | "REL" | "CNF" | "ENE">("todos")
  const [onlyEligible, setOnlyEligible] = useState(true)
  const [minValue, setMinValue] = useState("")
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState("")
  const [copied, setCopied] = useState(false)
  const [generationFeedback, setGenerationFeedback] = useState<{ visible: boolean; message: string; cacheHit?: boolean }>({
    visible: false,
    message: "",
  })
  const pleitoRef = useRef<HTMLDivElement | null>(null)

  const { data, isLoading, error } = useEventosPleito(id!, dateRange.inicio, dateRange.fim, dateRange.ready)
  const ano = useMemo(() => dateRange.inicio ? new Date(dateRange.inicio).getFullYear() : new Date().getFullYear(), [dateRange.inicio])
  const franquiaStatus = useFranquiaStatus(id!, ano)
  const criarPleito = useCriarPleito(id!)
  const exportarPleito = useExportarPleito()

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
  const canalMixed = new Set(selectedEventos.map((ev) => ev.canal_recomendado)).size > 1
  const pleitoMarkdown = draft || criarPleito.data?.markdown_gerado || ""
  const isGeneratingPleito = criarPleito.isPending || generationFeedback.visible

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
    const startedAt = Date.now()
    setDraft("")
    setEditing(false)
    setGenerationFeedback({
      visible: true,
      message: "Estruturando o pleito com os eventos selecionados…",
    })
    window.setTimeout(() => pleitoRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50)

    criarPleito.mutate(
      { eventos_ids: eventosIds, canal, inicio: dateRange.inicio, fim: dateRange.fim },
      {
        onSuccess: (res) => {
          const cacheHit = Boolean((res.metadados_json?.cache_ia as { hit?: boolean } | undefined)?.hit)
          const elapsed = Date.now() - startedAt
          const minVisibleMs = cacheHit ? 900 : 1200
          const maxCachedMs = 5000
          const delayMs = cacheHit ? Math.max(0, Math.min(minVisibleMs - elapsed, maxCachedMs - elapsed)) : Math.max(0, minVisibleMs - elapsed)
          if (cacheHit) {
            setGenerationFeedback({
              visible: true,
              cacheHit: true,
              message: "Pleito encontrado em cache. Preparando visualização…",
            })
          }
          window.setTimeout(() => {
            setDraft(res.markdown_gerado)
            setEditing(false)
            setGenerationFeedback({ visible: false, message: "", cacheHit })
            window.setTimeout(() => pleitoRef.current?.scrollIntoView({ behavior: "smooth", block: "start" }), 50)
          }, delayMs)
        },
        onError: () => {
          setGenerationFeedback({ visible: false, message: "" })
        },
      },
    )
  }

  const exportar = (formato: "docx" | "pdf" | "md" | "json") => {
    if (!criarPleito.data?.pleito_id) return
    exportarPleito.mutate(
      { pleitoId: criarPleito.data.pleito_id, formato },
      { onSuccess: (res) => triggerDownload(res.file_name, res.content, res.content_type, res.content_encoding ?? "utf-8") },
    )
  }

  const copiar = () => {
    navigator.clipboard.writeText(pleitoMarkdown)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="container mx-auto max-w-6xl px-6 py-10">
      <div className="mb-8">
        <p className="text-xs font-medium uppercase tracking-widest text-teal-500">Ressarcimento</p>
        <h2 className="mt-0.5 text-xl font-bold">Pleito de ressarcimento por evento</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Selecione eventos elegíveis, valide franquia/PLD/prazo e gere o pleito de ressarcimento para revisão humana.
        </p>
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-4">
        <DateRangePicker
          initialFrom={dateRange.inicio ? new Date(dateRange.inicio) : undefined}
          initialTo={dateRange.fim ? new Date(dateRange.fim) : undefined}
          minDate={dateRange.minDate}
          maxDate={dateRange.maxDate}
          onChange={(i, f) => { dateRange.setRange(i, f); setSelectedIds([]); setDraft("") }}
        />
        {franquiaStatus.data && (
          <Badge variant="secondary">
            Franquia {franquiaStatus.data.ano}: {fmtNum(franquiaStatus.data.franquia_horas)} h · restante {fmtNum(franquiaStatus.data.horas_restantes)} h
          </Badge>
        )}
      </div>

      {isLoading && !data && <Skeleton className="h-64 w-full" />}
      {error && !data && <ErrorState error={error} />}

      {data && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
            <KpiCard title="Valor pleitável total" value={fmtBRL(data.valor_total_pleitavel_reais)} highlight="success" />
            <KpiCard title="Energia ressarcível" value={fmtMWh(data.energia_ressarcivel_total_mwh)} />
            <KpiCard title="Eventos elegíveis" value={`${fmtNum(data.eventos_elegiveis)} / ${fmtNum(data.total_eventos)}`} />
            <KpiCard title="Franquia usada" value={`${fmtNum(data.franquia.horas_definidas)} h`} />
          </div>

          {(pleitoMarkdown || isGeneratingPleito || criarPleito.error || exportarPleito.error) && (
            <Card ref={pleitoRef} className="border-teal-500/30 bg-teal-500/5 scroll-mt-20">
              <CardHeader className="pb-2">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <CardTitle className="text-base font-semibold">Pleito de ressarcimento</CardTitle>
                    <p className="mt-1 text-xs leading-relaxed text-muted-foreground">
                      Estruturação feita a partir dos dados reais do evento, com elegibilidade, franquia, PLD, prazo e canal calculados conforme Lei 15.269/2025, REN ANEEL nº 1.030/2022 e Procedimentos de Rede do ONS — Submódulo 5.13. Revisão humana e jurídica continua obrigatória antes do protocolo.
                    </p>
                  </div>
                  {criarPleito.data?.canal && <Badge variant="secondary">{canalLabel[criarPleito.data.canal] ?? criarPleito.data.canal}</Badge>}
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex flex-wrap gap-2">
                  <Button size="sm" variant="outline" disabled={!pleitoMarkdown} onClick={copiar}>{copied ? <Check className="mr-2 h-4 w-4" /> : <Copy className="mr-2 h-4 w-4" />}{copied ? "Copiado" : "Copiar"}</Button>
                  <Button size="sm" variant="outline" disabled={!criarPleito.data?.pleito_id || exportarPleito.isPending} onClick={() => exportar("docx")}><Download className="mr-2 h-4 w-4" />Exportar DOCX</Button>
                  <Button size="sm" variant="outline" disabled={!criarPleito.data?.pleito_id || exportarPleito.isPending} onClick={() => exportar("pdf")}><Download className="mr-2 h-4 w-4" />Exportar PDF</Button>
                  <Button size="sm" variant="ghost" disabled={!criarPleito.data?.pleito_id || exportarPleito.isPending} onClick={() => exportar("json")}><Download className="mr-2 h-4 w-4" />JSON técnico</Button>
                  <Button size="sm" variant="outline" disabled={!pleitoMarkdown} onClick={() => setEditing((v) => !v)}>{editing ? "Preview" : "Editar"}</Button>
                </div>
                {criarPleito.error && <ErrorState error={criarPleito.error} />}
                {exportarPleito.error && <ErrorState error={exportarPleito.error} />}
                {isGeneratingPleito ? (
                  <div className="relative overflow-hidden rounded-md border border-teal-500/30 bg-gradient-to-br from-teal-500/10 via-background to-blue-500/10 p-6">
                    <div className="absolute inset-x-0 top-0 h-1 bg-gradient-to-r from-teal-400 via-cyan-400 to-blue-500" />
                    <div className="flex min-h-64 flex-col items-center justify-center text-center">
                      <div className="mb-4 rounded-full border border-teal-500/30 bg-teal-500/10 p-4 shadow-[0_0_40px_rgba(20,184,166,0.22)]">
                        <Loader2 className="h-8 w-8 animate-spin text-teal-500" />
                      </div>
                      <h3 className="text-lg font-semibold">Gerando pleito de ressarcimento</h3>
                      <p className="mt-2 max-w-xl text-sm text-muted-foreground">
                        {generationFeedback.message || "Calculando elegibilidade, franquia, PLD, prazos e preparando a redação para revisão humana."}
                      </p>
                      <div className="mt-5 grid w-full max-w-2xl grid-cols-1 gap-2 text-left text-xs text-muted-foreground sm:grid-cols-3">
                        <div className="rounded-md border bg-background/70 p-3">Eventos e franquia validados</div>
                        <div className="rounded-md border bg-background/70 p-3">Canal regulatório definido</div>
                        <div className="rounded-md border bg-background/70 p-3">{generationFeedback.cacheHit ? "Contexto da usina reaproveitado em até 5s" : "IA usando o contexto da usina para redigir"}</div>
                      </div>
                    </div>
                  </div>
                ) : editing ? (
                  <textarea className="h-[420px] w-full rounded-md border bg-background p-3 text-sm" value={draft} onChange={(e) => setDraft(e.target.value)} />
                ) : (
                  <ScrollArea className="h-[420px] rounded-md border bg-background p-4">
                    <div className="prose prose-sm dark:prose-invert max-w-none">
                      {pleitoMarkdown ? <Markdown>{pleitoMarkdown}</Markdown> : <p className="text-sm text-muted-foreground">Gere um pleito para visualizar o documento.</p>}
                    </div>
                  </ScrollArea>
                )}
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Eventos de Pleito</CardTitle>
              <p className="text-xs text-muted-foreground">Elegibilidade, franquia, PLD, prazo e canal são calculados antes da redação por IA.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                <Button size="sm" variant={onlyEligible ? "default" : "outline"} onClick={() => setOnlyEligible((v) => !v)}>Só elegíveis</Button>
                {(["todos", "REL", "CNF", "ENE"] as const).map((m) => (
                  <Button key={m} size="sm" variant={motivoFilter === m ? "default" : "outline"} onClick={() => setMotivoFilter(m)}>{m}</Button>
                ))}
                <Input className="w-52" type="number" value={minValue} onChange={(e) => setMinValue(e.target.value)} placeholder="Valor mínimo R$" />
                <Button size="sm" onClick={selecionarElegiveis}>Selecionar todos elegíveis</Button>
                <span className="text-xs text-muted-foreground">Selecionados: {selectedIds.length}</span>
              </div>

              <div className="overflow-x-auto rounded-md border">
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
                        <TableCell className="whitespace-nowrap text-xs">{fmtDate(ev.timestamp)}</TableCell>
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
                          <Button size="sm" variant="outline" disabled={!ev.elegivel || isGeneratingPleito} onClick={() => gerarPleito([ev.evento_id], ev.canal_recomendado)}>
                            Gerar
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                    {filteredEventos.length === 0 && (
                      <TableRow><TableCell colSpan={11} className="py-6 text-center text-sm text-muted-foreground">Nenhum evento encontrado.</TableCell></TableRow>
                    )}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium">Seleção para o pleito</CardTitle>
              <p className="text-xs text-muted-foreground">Um pleito de ressarcimento = um canal. Separe Protocolo ONS e Termo Lei 15.269 em documentos diferentes.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <KpiCard title="Eventos" value={`${selectedEventos.length}`} />
                <KpiCard title="Valor" value={fmtBRL(selectedTotal)} highlight="success" />
                <KpiCard title="Energia" value={fmtMWh(selectedEnergia)} />
              </div>
              {canalMixed && <Badge variant="destructive">Há canais mistos selecionados; gere pleitos separados por canal.</Badge>}
              <div className="flex flex-wrap gap-2">
                <Badge variant="secondary">Canal: {canalLabel[selectedCanal] ?? selectedCanal}</Badge>
                <Button size="sm" className="gap-2 bg-teal-600 hover:bg-teal-700 text-white" disabled={!selectedIds.length || canalMixed || isGeneratingPleito} onClick={() => gerarPleito()}>
                  <FileText className="h-4 w-4" />
                  {isGeneratingPleito ? "Gerando…" : "Gerar pleito selecionado"}
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
                {!selectedEventos.length && <p className="p-4 text-sm text-muted-foreground">Selecione eventos elegíveis acima.</p>}
              </ScrollArea>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}

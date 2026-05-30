import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { KpiCard } from "@/components/shared/KpiCard"
import { SourceBadge } from "@/components/shared/SourceBadge"
import { ErrorState } from "@/components/shared/ErrorState"
import { DossieViewer } from "./DossieViewer"
import { RegulatorioQA } from "./RegulatorioQA"
import { useElegibilidade } from "@/hooks/useRegulatorio"
import { fmtBRL, fmtDate, fmtMWh } from "@/lib/formatters"
import { RAZAO_LABELS } from "@/lib/constants"

interface Props {
  usinaId: string
  inicio: string
  fim: string
}

export function RegulatorioTab({ usinaId, inicio, fim }: Props) {
  const { data, isLoading, error } = useElegibilidade(usinaId, inicio, fim)

  if (isLoading) return <Skeleton className="h-64 w-full" />
  if (error) return <ErrorState error={error} />
  if (!data) return null

  const { qualidade_classificacao: qc } = data

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <KpiCard title="Potencial ressarcível" value={fmtBRL(data.total_potencial_ressarcivel_reais)} highlight="success" />
        <KpiCard
          title="Classificados por IA"
          value={`${qc.eventos_classificados_por_ia} / ${qc.eventos_totais}`}
          sub={`${qc.eventos_com_razao_gold} com dado gold`}
        />
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
                <TableHead>Valor</TableHead>
                <TableHead>Fonte</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.eventos.map((ev, i) => (
                <TableRow key={i}>
                  <TableCell className="text-xs">{fmtDate(ev.timestamp)}</TableCell>
                  <TableCell className="text-xs">{RAZAO_LABELS[ev.razao_restricao] ?? ev.razao_restricao}</TableCell>
                  <TableCell className="text-xs">{fmtMWh(ev.energia_restringida_mwh)}</TableCell>
                  <TableCell>
                    <Badge variant={ev.elegivel_ressarcimento ? "default" : "outline"}>
                      {ev.elegivel_ressarcimento ? "Sim" : "Não"}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-xs">{ev.elegivel_ressarcimento ? fmtBRL(ev.valor_potencial_reais) : "—"}</TableCell>
                  <TableCell>
                    <SourceBadge
                      fonte={ev.classificacao_fonte}
                      confianca={ev.classificacao_confianca}
                      justificativa={ev.classificacao_justificativa}
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
          <DossieViewer usinaId={usinaId} inicio={inicio} fim={fim} />
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

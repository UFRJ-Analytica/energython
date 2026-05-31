import Markdown from "react-markdown"
import { Download } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { ErrorState } from "@/components/shared/ErrorState"
import { useDossieExport } from "@/hooks/useRegulatorio"

interface Props {
  usinaId: string
  inicio: string
  fim: string
  markdown: string
  franquiaHorasOverride?: number
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

export function DossieViewer({ usinaId, inicio, fim, markdown, franquiaHorasOverride }: Props) {
  const exportMutation = useDossieExport(usinaId)

  const handleExport = (formato: "markdown" | "json") => {
    exportMutation.mutate(
      {
        inicio,
        fim,
        formato,
        franquia_horas_override: Number.isFinite(franquiaHorasOverride) ? franquiaHorasOverride : undefined,
      },
      {
        onSuccess: (res) => triggerDownload(res.file_name, res.content, res.content_type),
      },
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleExport("markdown")}
          disabled={exportMutation.isPending || !markdown}
          className="gap-2"
        >
          <Download className="h-4 w-4" />
          Exportar MD
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => handleExport("json")}
          disabled={exportMutation.isPending || !markdown}
          className="gap-2"
        >
          <Download className="h-4 w-4" />
          Exportar JSON
        </Button>
      </div>

      {exportMutation.error && <ErrorState error={exportMutation.error} />}

      <ScrollArea className="h-96 rounded-md border p-4">
        <div className="prose prose-sm dark:prose-invert max-w-none">
          {markdown ? <Markdown>{markdown}</Markdown> : <p className="text-sm text-muted-foreground">Execute o fluxo para gerar o dossiê.</p>}
        </div>
      </ScrollArea>
    </div>
  )
}

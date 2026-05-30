import { useState } from "react"
import Markdown from "react-markdown"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/shared/ErrorState"
import { useDossie } from "@/hooks/useRegulatorio"
import { FileText } from "lucide-react"

interface Props {
  usinaId: string
  inicio: string
  fim: string
}

export function DossieViewer({ usinaId, inicio, fim }: Props) {
  const { mutate, data, isPending, error } = useDossie(usinaId)
  const [generated, setGenerated] = useState(false)

  const handleGenerate = () => {
    setGenerated(true)
    mutate({ inicio, fim })
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" onClick={handleGenerate} disabled={isPending} className="gap-2">
          <FileText className="h-4 w-4" />
          {isPending ? "Gerando dossiê…" : "Gerar rascunho de dossiê"}
        </Button>
        {generated && !isPending && !error && <span className="text-xs text-muted-foreground">Gerado pelo agente IA</span>}
      </div>

      {error && <ErrorState error={error} />}

      {isPending && <Skeleton className="h-48 w-full" />}

      {data && (
        <ScrollArea className="h-96 rounded-md border p-4">
          <div className="prose prose-sm dark:prose-invert max-w-none">
            <Markdown>{data.dossie_markdown}</Markdown>
          </div>
        </ScrollArea>
      )}
    </div>
  )
}

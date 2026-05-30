import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Skeleton } from "@/components/ui/skeleton"
import { Badge } from "@/components/ui/badge"
import { ErrorState } from "@/components/shared/ErrorState"
import { useConsulta } from "@/hooks/useRegulatorio"
import { BookOpen, SendHorizontal } from "lucide-react"

export function RegulatorioQA() {
  const [pergunta, setPergunta] = useState("")
  const { mutate, data, isPending, error } = useConsulta()

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (pergunta.trim()) mutate({ pergunta: pergunta.trim() })
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <Textarea
          placeholder="Ex: Cortes por razão energética são elegíveis a ressarcimento?"
          value={pergunta}
          onChange={(e) => setPergunta(e.target.value)}
          className="min-h-0 resize-none"
          rows={2}
        />
        <Button type="submit" size="icon" disabled={isPending || !pergunta.trim()}>
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </form>

      {error && <ErrorState error={error} />}
      {isPending && <Skeleton className="h-24 w-full" />}

      {data && (
        <div className="space-y-2 rounded-md border p-4">
          <p className="text-sm">{data.resposta}</p>
          {data.fontes.length > 0 && (
            <div className="flex flex-wrap gap-2 pt-1">
              <BookOpen className="h-4 w-4 text-muted-foreground self-center" />
              {data.fontes.map((f) => (
                <Badge key={f} variant="outline" className="font-mono text-xs">{f}</Badge>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

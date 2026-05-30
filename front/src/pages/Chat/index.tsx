import { useState } from "react"
import { SendHorizontal, BookOpen } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { ErrorState } from "@/components/shared/ErrorState"
import { useConsulta } from "@/hooks/useRegulatorio"

const SUGESTOES = [
  "Cortes por razão energética são elegíveis a ressarcimento?",
  "O que diz a Lei 15.269/2025 sobre geração distribuída?",
  "Quais são os prazos para protocolar um pleito na CCEE?",
]

export default function Chat() {
  const [pergunta, setPergunta] = useState("")
  const { mutate, data, isPending, error } = useConsulta()

  const enviar = (q: string) => {
    if (!q.trim()) return
    setPergunta(q)
    mutate({ pergunta: q.trim() })
  }

  return (
    <div className="container mx-auto max-w-2xl px-6 py-10">
      <div className="mb-8">
        <p className="text-xs font-medium uppercase tracking-widest text-teal-500">Consulta Regulatória</p>
        <h2 className="mt-0.5 text-xl font-bold">Assistente de Normas</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Tire dúvidas sobre REN 1.030/2022 e Lei 15.269/2025 com fontes citadas.
        </p>
      </div>

      {/* Sugestões */}
      {!data && !isPending && (
        <div className="mb-6 flex flex-col gap-2">
          {SUGESTOES.map((s) => (
            <button
              key={s}
              onClick={() => enviar(s)}
              className="rounded-lg border border-border/40 bg-muted/20 px-4 py-2.5 text-left text-sm text-muted-foreground transition-colors hover:border-teal-500/40 hover:text-foreground"
            >
              {s}
            </button>
          ))}
        </div>
      )}

      {/* Resposta */}
      {isPending && <Skeleton className="mb-6 h-32 w-full rounded-xl" />}
      {error && <div className="mb-6"><ErrorState error={error} /></div>}
      {data && (
        <div className="mb-6 space-y-3 rounded-xl border border-teal-500/20 bg-teal-500/5 p-5">
          <p className="text-sm leading-relaxed">{data.resposta}</p>
          {data.fontes.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 border-t border-border/30 pt-3">
              <BookOpen className="h-3.5 w-3.5 text-muted-foreground" />
              {data.fontes.map((f) => (
                <Badge key={f} variant="outline" className="font-mono text-xs">{f}</Badge>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Input */}
      <form
        onSubmit={(e) => { e.preventDefault(); enviar(pergunta) }}
        className="flex gap-2"
      >
        <Textarea
          placeholder="Faça uma pergunta sobre as normas regulatórias…"
          value={pergunta}
          onChange={(e) => setPergunta(e.target.value)}
          rows={2}
          className="resize-none text-sm"
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); enviar(pergunta) } }}
        />
        <Button type="submit" size="icon" className="shrink-0 self-end bg-teal-600 hover:bg-teal-700" disabled={isPending || !pergunta.trim()}>
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </form>
    </div>
  )
}

import { useEffect, useState } from "react"
import { useParams } from "react-router-dom"
import { subDays } from "date-fns"
import { Check, Copy, Download, FileText } from "lucide-react"
import Markdown from "react-markdown"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { DateRangePicker } from "@/components/shared/DateRangePicker"
import { ErrorState } from "@/components/shared/ErrorState"
import { useDossie } from "@/hooks/useRegulatorio"
import { useTypewriter } from "@/hooks/useTypewriter"
import { toIso } from "@/lib/formatters"

const STEPS = [
  "Buscando eventos do período…",
  "Classificando elegibilidade regulatória…",
  "Calculando valor total do pleito…",
  "Redigindo dossiê com base na REN 1.030/2022 e Lei 15.269/2025…",
]

function LoadingSteps({ active }: { active: boolean }) {
  const [step, setStep] = useState(0)

  useEffect(() => {
    if (!active) return
    setStep(0)
    const t = setInterval(() => setStep((s) => Math.min(s + 1, STEPS.length - 1)), 1200)
    return () => clearInterval(t)
  }, [active])

  if (!active) return null

  return (
    <div className="space-y-2 rounded-xl border border-border/40 bg-muted/20 p-6">
      {STEPS.map((s, i) => (
        <div key={s} className={`flex items-center gap-3 text-sm transition-opacity duration-300 ${i <= step ? "opacity-100" : "opacity-25"}`}>
          <div className={`h-1.5 w-1.5 rounded-full ${i < step ? "bg-teal-400" : i === step ? "bg-teal-400 animate-pulse" : "bg-muted-foreground/30"}`} />
          <span className={i < step ? "text-muted-foreground line-through" : i === step ? "text-foreground" : "text-muted-foreground"}>
            {s}
          </span>
          {i < step && <Check className="ml-auto h-3 w-3 text-teal-400" />}
        </div>
      ))}
    </div>
  )
}

function DossieContent({ markdown }: { markdown: string }) {
  const text = useTypewriter(markdown, 200)
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(markdown)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleExport = () => {
    const blob = new Blob([markdown], { type: "text/markdown" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "dossie-curtailiq.md"
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <p className="text-xs text-teal-400 font-medium uppercase tracking-widest">Dossiê gerado pela IA</p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" className="gap-1.5 h-7 text-xs" onClick={handleCopy}>
            {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
            {copied ? "Copiado" : "Copiar"}
          </Button>
          <Button variant="outline" size="sm" className="gap-1.5 h-7 text-xs" onClick={handleExport}>
            <Download className="h-3 w-3" />
            Exportar .md
          </Button>
        </div>
      </div>
      <ScrollArea className="h-[500px] rounded-xl border border-border/40 bg-muted/10 p-6">
        <div className="prose prose-sm dark:prose-invert max-w-none prose-headings:text-foreground prose-p:text-muted-foreground">
          <Markdown>{text}</Markdown>
        </div>
        {text.length < markdown.length && (
          <span className="inline-block h-4 w-0.5 animate-pulse bg-teal-400" />
        )}
      </ScrollArea>
    </div>
  )
}

export default function Dossie() {
  const { id } = useParams<{ id: string }>()
  const [inicio, setInicio] = useState(() => toIso(subDays(new Date(), 30)))
  const [fim, setFim] = useState(() => toIso(new Date()))
  const { mutate, data, isPending, error } = useDossie(id!)

  return (
    <div className="container mx-auto max-w-3xl px-6 py-10">
      <div className="mb-8">
        <p className="text-xs font-medium uppercase tracking-widest text-teal-500">Elo Regulatório</p>
        <h2 className="mt-0.5 text-xl font-bold">Gerar Dossiê de Pleito</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          A IA classifica os eventos elegíveis e redige o rascunho de pleito regulatório.
        </p>
      </div>

      <div className="mb-6 flex flex-wrap items-center gap-4">
        <DateRangePicker onChange={(i, f) => { setInicio(i); setFim(f) }} />
        <Button
          size="lg"
          className="gap-2 bg-teal-600 hover:bg-teal-700 text-white"
          disabled={isPending}
          onClick={() => mutate({ inicio, fim })}
        >
          <FileText className="h-4 w-4" />
          {isPending ? "Gerando dossiê…" : "Gerar dossiê de pleito"}
        </Button>
      </div>

      {error && <ErrorState error={error} />}
      <LoadingSteps active={isPending} />

      {data && !isPending && <DossieContent markdown={data.dossie_markdown} />}
    </div>
  )
}

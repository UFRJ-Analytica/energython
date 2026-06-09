import { useBuildInfo } from "@/hooks/useBuildInfo"
import { format, parseISO } from "date-fns"
import { ptBR } from "date-fns/locale"

function fmtDate(iso: string) {
  try {
    return format(parseISO(iso), "dd/MM/yyyy HH:mm:ss", { locale: ptBR })
  } catch {
    return iso
  }
}

function BuildCard({ label, gitHash, buildTime }: { label: string; gitHash: string; buildTime: string }) {
  return (
    <div className="rounded-lg border border-border/60 bg-card p-6 space-y-3">
      <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">{label}</h2>
      <div className="space-y-2 font-mono text-sm">
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground w-24 shrink-0">commit</span>
          <span className="text-teal-400">{gitHash}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-muted-foreground w-24 shrink-0">build</span>
          <span>{fmtDate(buildTime)}</span>
        </div>
      </div>
    </div>
  )
}

export default function Build() {
  const { front, back } = useBuildInfo()

  return (
    <div className="min-h-screen bg-background text-foreground flex items-center justify-center p-8">
      <div className="w-full max-w-md space-y-4">
        <h1 className="text-lg font-bold mb-6">Build Info</h1>

        <BuildCard label="Frontend" gitHash={front.gitHash} buildTime={front.buildTime} />

        {back ? (
          <BuildCard label="Backend" gitHash={back.git_hash} buildTime={back.build_time} />
        ) : (
          <div className="rounded-lg border border-border/60 bg-card p-6">
            <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-3">Backend</h2>
            <span className="text-sm text-muted-foreground font-mono">carregando...</span>
          </div>
        )}
      </div>
    </div>
  )
}

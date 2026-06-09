import { format, parseISO } from "date-fns"
import { ptBR } from "date-fns/locale"
import { useBuildInfo } from "@/hooks/useBuildInfo"

function fmtBuild(iso: string) {
  try {
    return format(parseISO(iso), "dd/MM/yy HH:mm", { locale: ptBR })
  } catch {
    return iso
  }
}

export function BuildFooter() {
  const { front, back } = useBuildInfo()

  return (
    <footer className="mt-auto border-t border-border/30 py-2 px-6">
      <div className="container mx-auto max-w-6xl flex items-center gap-4 text-[10px] text-muted-foreground/50 font-mono">
        <span>
          front <span className="text-muted-foreground/70">{front.gitHash}</span>
          {" · "}
          {fmtBuild(front.buildTime)}
        </span>
        {back && (
          <>
            <span className="text-border">·</span>
            <span>
              back <span className="text-muted-foreground/70">{back.git_hash}</span>
              {" · "}
              {fmtBuild(back.build_time)}
            </span>
          </>
        )}
      </div>
    </footer>
  )
}

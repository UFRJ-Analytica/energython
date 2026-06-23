import { Moon, Sun, Zap } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useTheme } from "@/components/theme-provider"
import { useAllUsinas } from "@/hooks/useUsinas"
import { fmtBRL, fmtMWh } from "@/lib/formatters"
import { PlantMap } from "./PlantMap"
import { BuildFooter } from "@/components/shared/BuildFooter"

function LoadingMapSkeleton() {
  return (
    <div className="space-y-4">
      <div className="grid gap-3 sm:grid-cols-3">
        <Skeleton className="h-20 rounded-2xl" />
        <Skeleton className="h-20 rounded-2xl" />
        <Skeleton className="h-20 rounded-2xl" />
      </div>
      <Skeleton className="h-[620px] rounded-[2rem]" />
    </div>
  )
}

export default function Portfolio() {
  const { theme, setTheme } = useTheme()
  const { data: usinas, isLoading, isError, error } = useAllUsinas({ submercado: "NE" })

  const totalPerda = (usinas ?? []).reduce((acc, u) => acc + Number(u.total_perda_reais || 0), 0)
  const totalCorte = (usinas ?? []).reduce((acc, u) => acc + Number(u.total_corte_mwh || 0), 0)
  const totalSolar = (usinas ?? []).filter((u) => u.fonte === "solar").length
  const totalEolica = (usinas ?? []).filter((u) => u.fonte === "eolica").length

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="flex items-center justify-between border-b border-border/50 px-4 py-3 sm:px-6">
        <img src="/logo.png" alt="CurtailIQ" className="h-7 w-auto object-contain" />
        <Button variant="ghost" size="icon" className="h-8 w-8"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </header>

      <main className="container mx-auto w-full max-w-7xl flex-1 px-4 py-8 sm:px-6 sm:py-10">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="max-w-3xl">
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/10 px-3 py-1 text-xs font-medium text-emerald-300">
              <Zap className="h-3.5 w-3.5" />
              Ranking geográfico por perda financeira nos últimos 2 meses disponíveis
            </div>
            <h1 className="text-3xl font-black tracking-tight sm:text-4xl">Mapa de usinas com curtailment relevante</h1>
            <p className="mt-2 text-sm text-muted-foreground sm:text-base">
              Seleção por mapa: clique em uma usina para abrir a análise. O backend força a presença de solares quando elas têm perda financeira relevante.
            </p>
          </div>

          <div className="grid grid-cols-3 gap-2 text-right sm:min-w-[520px]">
            <div className="rounded-2xl border border-rose-500/20 bg-rose-500/10 p-4">
              <p className="text-[10px] uppercase tracking-widest text-rose-200/70">Perda financeira</p>
              <p className="mt-1 text-lg font-black text-rose-200">{fmtBRL(totalPerda)}</p>
            </div>
            <div className="rounded-2xl border border-sky-500/20 bg-sky-500/10 p-4">
              <p className="text-[10px] uppercase tracking-widest text-sky-200/70">Energia</p>
              <p className="mt-1 text-lg font-black text-sky-200">{fmtMWh(totalCorte)}</p>
            </div>
            <div className="rounded-2xl border border-amber-500/20 bg-amber-500/10 p-4">
              <p className="text-[10px] uppercase tracking-widest text-amber-200/70">Mix</p>
              <p className="mt-1 text-lg font-black text-amber-200">{totalSolar} solar · {totalEolica} eólica</p>
            </div>
          </div>
        </div>

        {isLoading ? (
          <LoadingMapSkeleton />
        ) : isError ? (
          <div className="rounded-2xl border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            Falha ao carregar usinas individuais do backend: {error instanceof Error ? error.message : "erro desconhecido"}
          </div>
        ) : usinas && usinas.length > 0 ? (
          <PlantMap usinas={usinas} />
        ) : (
          <div className="rounded-2xl border border-border/60 bg-card p-8 text-sm text-muted-foreground">
            Nenhuma usina com curtailment relevante encontrada para o recorte NE.
          </div>
        )}
      </main>

      <BuildFooter />
    </div>
  )
}

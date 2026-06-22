import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { Moon, Sun, Sun as SunIcon, Wind } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { useTheme } from "@/components/theme-provider"
import { useAllUsinas, useUsinas } from "@/hooks/useUsinas"
import { usePersistedState } from "@/hooks/usePersistedState"
import { fmtBRL, fmtMWh, fmtMW } from "@/lib/formatters"
import { FONTES, SUBMERCADOS } from "@/lib/constants"
import type { UsinaOut } from "@/types/usinas"
import { PlantMap } from "./PlantMap"
import { BuildFooter } from "@/components/shared/BuildFooter"

function PlantCard({ usina }: { usina: UsinaOut }) {
  const navigate = useNavigate()
  return (
    <div
      className="flex items-center justify-between rounded-lg border border-border/40 p-4 cursor-pointer transition-colors hover:bg-muted/30 active:bg-muted/50"
      onClick={() => navigate(`/usinas/${usina.usina_id}`)}
    >
      <div className="flex items-center gap-3">
        {usina.fonte === "solar"
          ? <SunIcon className="h-4 w-4 shrink-0 text-amber-400" />
          : <Wind className="h-4 w-4 shrink-0 text-sky-400" />}
        <div>
          <p className="font-medium text-sm">{usina.nome}</p>
          <p className="text-xs text-muted-foreground capitalize">{usina.fonte} · {fmtMW(usina.potencia_mw)}</p>
          {typeof usina.total_perda_reais === "number" && (
            <p className="text-xs text-muted-foreground">Perda financeira: {fmtBRL(usina.total_perda_reais)}</p>
          )}
          {typeof usina.total_corte_mwh === "number" && (
            <p className="text-xs text-muted-foreground">Perda energética: {fmtMWh(usina.total_corte_mwh)}</p>
          )}
        </div>
      </div>
      <Badge variant="outline" className="text-xs shrink-0">{usina.submercado}</Badge>
    </div>
  )
}

function PlantRow({ usina }: { usina: UsinaOut }) {
  const navigate = useNavigate()
  return (
    <tr
      className="cursor-pointer border-b border-border/40 transition-colors hover:bg-muted/30"
      onClick={() => navigate(`/usinas/${usina.usina_id}`)}
    >
      <td className="py-3 pr-4">
        <div className="flex items-center gap-2">
          {usina.fonte === "solar"
            ? <SunIcon className="h-4 w-4 shrink-0 text-amber-400" />
            : <Wind className="h-4 w-4 shrink-0 text-sky-400" />}
          <span className="font-medium text-sm">{usina.nome}</span>
        </div>
      </td>
      <td className="py-3 pr-4 text-sm text-muted-foreground capitalize">{usina.fonte}</td>
      <td className="py-3 pr-4 text-sm text-muted-foreground">{fmtMW(usina.potencia_mw)}</td>
      <td className="py-3 pr-4 text-sm text-muted-foreground">{typeof usina.total_perda_reais === "number" ? fmtBRL(usina.total_perda_reais) : "—"}</td>
      <td className="py-3 pr-4 text-sm text-muted-foreground">{typeof usina.total_corte_mwh === "number" ? fmtMWh(usina.total_corte_mwh) : "—"}</td>
      <td className="py-3 pr-4 text-xs text-muted-foreground">{usina.id_ons ?? "—"}</td>
      <td className="py-3">
        <Badge variant="outline" className="text-xs">{usina.submercado}</Badge>
      </td>
    </tr>
  )
}

function LoadingSkeleton() {
  const widths = ["w-48", "w-36", "w-52", "w-40", "w-44", "w-56", "w-36", "w-48"]
  return (
    <div className="space-y-px">
      {widths.map((w, i) => (
        <div key={i} className="flex items-center gap-3 border-b border-border/40 py-3">
          <Skeleton className="h-4 w-4 shrink-0 rounded-full" />
          <Skeleton className={`h-4 ${w}`} />
          <Skeleton className="ml-auto h-4 w-12" />
        </div>
      ))}
    </div>
  )
}

export default function Portfolio() {
  const { theme, setTheme } = useTheme()
  const [fonte, setFonte] = usePersistedState("portfolio.fonte", "all")
  const [submercado, setSubmercado] = usePersistedState("portfolio.submercado", "NE")
  const [offset, setOffset] = useState(0)
  const LIMIT = 15

  const filters = {
    fonte: fonte !== "all" ? fonte : undefined,
    submercado: submercado !== "all" ? submercado : undefined,
  }

  const { data, isLoading, isError, error } = useUsinas({ ...filters, limit: LIMIT, offset })
  const { data: allUsinas, isError: isAllUsinasError, error: allUsinasError } = useAllUsinas(filters)

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="flex items-center justify-between border-b border-border/50 px-4 py-3 sm:px-6">
        <img src="/logo.png" alt="CurtailIQ" className="h-7 w-auto object-contain" />
        <Button variant="ghost" size="icon" className="h-8 w-8"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </header>

      <main className="container mx-auto w-full max-w-4xl flex-1 px-4 py-8 sm:px-6 sm:py-10">
        <div className="mb-6 sm:mb-8">
          <h1 className="text-xl font-bold sm:text-2xl">Portfólio de Usinas</h1>
          <p className="mt-1 text-sm text-muted-foreground">Top usinas individuais do NE com maior perda financeira e energética nos últimos 2 meses disponíveis</p>
        </div>

        <div className="mb-4 flex flex-wrap gap-2 sm:gap-3">
          <Select value={fonte} onValueChange={(v) => { setFonte(v); setOffset(0) }}>
            <SelectTrigger className="w-36 h-8 text-xs">
              <SelectValue placeholder="Fonte" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todas as fontes</SelectItem>
              {FONTES.map((f) => <SelectItem key={f} value={f} className="capitalize">{f}</SelectItem>)}
            </SelectContent>
          </Select>
          <Select value={submercado} onValueChange={(v) => { setSubmercado(v); setOffset(0) }}>
            <SelectTrigger className="w-36 h-8 text-xs">
              <SelectValue placeholder="Submercado" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {SUBMERCADOS.map((s) => <SelectItem key={s} value={s}>{s}</SelectItem>)}
            </SelectContent>
          </Select>
        </div>

        {isLoading ? (
          <LoadingSkeleton />
        ) : isError ? (
          <div className="rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
            Falha ao carregar usinas individuais do backend: {error instanceof Error ? error.message : "erro desconhecido"}
          </div>
        ) : (
          <>
            {isAllUsinasError && (
              <div className="mb-4 rounded-lg border border-destructive/40 bg-destructive/10 p-4 text-sm text-destructive">
                Falha ao carregar coordenadas para o mapa: {allUsinasError instanceof Error ? allUsinasError.message : "erro desconhecido"}
              </div>
            )}
            {allUsinas && allUsinas.length > 0 && (
              <div className="mb-4"><PlantMap usinas={allUsinas} /></div>
            )}

            <div className="flex flex-col gap-2 sm:hidden">
              {data?.items.map((u) => <PlantCard key={u.usina_id} usina={u} />)}
            </div>

            <table className="hidden w-full sm:table">
              <thead>
                <tr className="border-b border-border/60 text-left text-xs text-muted-foreground">
                  <th className="pb-2 pr-4 font-medium">Usina</th>
                  <th className="pb-2 pr-4 font-medium">Fonte</th>
                  <th className="pb-2 pr-4 font-medium">Capacidade</th>
                  <th className="pb-2 pr-4 font-medium">Perda financeira</th>
                  <th className="pb-2 pr-4 font-medium">Perda energética</th>
                  <th className="pb-2 pr-4 font-medium">ONS</th>
                  <th className="pb-2 font-medium">Submercado</th>
                </tr>
              </thead>
              <tbody>
                {data?.items.map((u) => <PlantRow key={u.usina_id} usina={u} />)}
              </tbody>
            </table>
          </>
        )}

        {data && data.total_count > LIMIT && (
          <div className="mt-6 flex items-center justify-center gap-4">
            <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset((o) => o - LIMIT)}>Anterior</Button>
            <span className="text-xs text-muted-foreground">{Math.floor(offset / LIMIT) + 1} / {Math.ceil(data.total_count / LIMIT)}</span>
            <Button variant="outline" size="sm" disabled={offset + LIMIT >= data.total_count} onClick={() => setOffset((o) => o + LIMIT)}>Próxima</Button>
          </div>
        )}
      </main>

      <BuildFooter />
    </div>
  )
}

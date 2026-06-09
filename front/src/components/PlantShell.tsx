import { Link, NavLink, Outlet, useParams } from "react-router-dom"
import { Moon, Sun, ChevronLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { useTheme } from "@/components/theme-provider"
import { useUsina } from "@/hooks/useUsinas"
import { cn } from "@/lib/utils"
import { BuildFooter } from "@/components/shared/BuildFooter"

const tabs = [
  { to: "", label: "Resumo", end: true },
  { to: "financeiro", label: "Financeiro", end: false },
  { to: "bess", label: "Simulador BESS", end: false },
  { to: "dossie", label: "Ressarcimento", end: false },
  { to: "chat", label: "Curtail AI", end: false },
]

export function PlantShell() {
  const { id } = useParams<{ id: string }>()
  const { data: usina, isLoading } = useUsina(id!)
  const { theme, setTheme } = useTheme()

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      <header className="sticky top-0 z-40 border-b border-border/50 bg-background/90 backdrop-blur">
        <div className="container mx-auto max-w-6xl px-4">
          <div className="flex h-14 items-center gap-4">
            <Link to="/usinas">
              <img src="/logo.png" alt="CurtailIQ" className="h-6 w-auto object-contain" />
            </Link>

            <Link to="/usinas" className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors">
              <ChevronLeft className="h-3 w-3" />
              Usinas
            </Link>

            <div className="h-4 w-px bg-border" />

            {isLoading ? (
              <Skeleton className="h-4 w-40" />
            ) : (
              <span className="text-sm font-medium truncate max-w-48">{usina?.nome}</span>
            )}

            <nav className="ml-auto flex items-center gap-1 overflow-x-auto scrollbar-none">
              {tabs.map((t) => (
                <NavLink
                  key={t.to}
                  to={`/usinas/${id}${t.to ? `/${t.to}` : ""}`}
                  end={t.end}
                  className={({ isActive }) =>
                    cn(
                      "shrink-0 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                      isActive
                        ? "bg-teal-500/15 text-teal-400"
                        : "text-muted-foreground hover:text-foreground"
                    )
                  }
                >
                  {t.label}
                </NavLink>
              ))}
            </nav>

            <Button variant="ghost" size="icon" className="shrink-0 h-8 w-8"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </div>
      </header>

      <Outlet />

      <BuildFooter />
    </div>
  )
}

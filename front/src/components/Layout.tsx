import { Outlet, useLocation } from "react-router-dom"
import { Moon, Sun } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useTheme } from "@/components/theme-provider"

export function Layout() {
  const { theme, setTheme } = useTheme()
  const location = useLocation()
  const isHome = location.pathname === "/"

  return (
    <div className="min-h-screen bg-background text-foreground">
      {!isHome && (
        <header className="sticky top-0 z-40 border-b bg-background/80 backdrop-blur">
          <div className="container mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
            <a href="https://energython.cognati.tech/" aria-label="Ir para a página inicial do CurtailIQ">
              <img src="/logo.png" alt="CurtailIQ" className="h-7 w-auto object-contain" />
            </a>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            >
              {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </Button>
          </div>
        </header>
      )}
      <Outlet />
    </div>
  )
}

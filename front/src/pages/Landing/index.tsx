import { useNavigate } from "react-router-dom"
import { Moon, Sun, ArrowRight, DollarSign, ShieldCheck, TrendingUp } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { useTheme } from "@/components/theme-provider"

const features = [
  {
    icon: <DollarSign className="h-6 w-6 text-teal-500" />,
    title: "Perda financeira",
    desc: "Quantifique exatamente quanto foi perdido por evento, razão e período com rastreabilidade horária.",
  },
  {
    icon: <ShieldCheck className="h-6 w-6 text-teal-500" />,
    title: "Ressarcimento regulatório",
    desc: "Identifique eventos elegíveis e gere rascunhos de dossiê com IA, alinhados à REN 1.030/2022.",
  },
  {
    icon: <TrendingUp className="h-6 w-6 text-teal-500" />,
    title: "Risco e mitigação",
    desc: "Preveja exposição futura e simule o ROI de baterias (BESS) com dados reais da usina.",
  },
]

export default function Landing() {
  const navigate = useNavigate()
  const { theme, setTheme } = useTheme()

  return (
    <div className="flex min-h-screen flex-col">
      <header className="flex items-center justify-between px-6 py-4">
        <img src="/logo.png" alt="CurtailIQ" className="h-8 w-auto object-contain" />
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
        >
          {theme === "dark" ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
      </header>

      <main className="flex flex-1 flex-col items-center justify-center gap-12 px-6 py-16 text-center">
        <div className="space-y-6 max-w-xl">
          <img src="/logo.png" alt="CurtailIQ" className="mx-auto h-16 w-auto object-contain" />

          <div className="space-y-3">
            <p className="text-xs font-medium uppercase tracking-widest text-teal-500">
              Inteligência de Curtailment
            </p>
            <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
              Transforme cortes em{" "}
              <span className="text-teal-500">decisão</span>
            </h1>
            <p className="text-muted-foreground text-base leading-relaxed">
              Plataforma analítica para geradoras renováveis do Nordeste — perdas, risco e
              recuperação regulatória em um só lugar.
            </p>
          </div>

          <Button
            size="lg"
            className="gap-2 bg-teal-600 hover:bg-teal-700 text-white"
            onClick={() => navigate("/usinas")}
          >
            Acessar usinas
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>

        <div className="grid w-full max-w-3xl grid-cols-1 gap-4 sm:grid-cols-3">
          {features.map((f) => (
            <Card key={f.title} className="text-left border-border/60">
              <CardContent className="pt-6 space-y-2">
                {f.icon}
                <p className="font-semibold text-sm">{f.title}</p>
                <p className="text-xs text-muted-foreground leading-relaxed">{f.desc}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </main>

      <footer className="py-5 text-center text-xs text-muted-foreground">
        CurtailIQ · Analytica Energython
      </footer>
    </div>
  )
}

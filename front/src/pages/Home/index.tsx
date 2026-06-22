import { ArrowRight, BarChart3, ShieldCheck, Zap } from "lucide-react"
import { Link, useNavigate } from "react-router-dom"
import { Button } from "@/components/ui/button"

export default function Home() {
  const navigate = useNavigate()

  const openDebug = () => {
    sessionStorage.setItem("energython.debugAccess", "true")
    navigate("/debug")
  }

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#05070b] text-white">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute left-1/2 top-[-18rem] h-[42rem] w-[42rem] -translate-x-1/2 rounded-full bg-sky-500/20 blur-3xl" />
        <div className="absolute bottom-[-14rem] right-[-10rem] h-[34rem] w-[34rem] rounded-full bg-cyan-400/15 blur-3xl" />
        <div className="absolute left-[-12rem] top-1/3 h-[30rem] w-[30rem] rounded-full bg-blue-700/20 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.08)_1px,transparent_1px)] [background-size:28px_28px] opacity-20" />
      </div>

      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <Link to="/" className="flex items-center gap-3 rounded-full border border-white/10 bg-white px-4 py-2 shadow-[0_12px_40px_rgba(14,165,233,0.18)]">
          <img src="/logo.png" alt="CurtailIQ" className="h-8 w-12 object-cover object-left" />
          <span className="font-heading text-lg font-semibold tracking-[-0.04em] text-slate-950">CurtailIQ</span>
        </Link>
        <Link to="/usinas" className="hidden text-sm font-medium text-slate-300 transition hover:text-white sm:block">
          Acessar usinas
        </Link>
      </header>

      <main className="relative z-10 mx-auto flex min-h-[calc(100vh-88px)] max-w-6xl items-center px-6 pb-16 pt-8">
        <section className="mx-auto grid w-full items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
          <div className="max-w-3xl">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-sky-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-300 shadow-[0_0_18px_rgba(103,232,249,0.9)]" />
              Inteligência para curtailment renovável
            </div>

            <h1 className="font-heading text-5xl font-semibold tracking-[-0.06em] text-white sm:text-6xl lg:text-7xl">
              Transforme cortes de geração em decisões financeiras.
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
              O CurtailIQ identifica perdas por curtailment, estima impacto econômico e organiza evidências para análise de ressarcimento em usinas renováveis.
            </p>

            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button asChild size="lg" className="h-12 rounded-full bg-sky-400 px-6 text-sm font-semibold text-slate-950 shadow-[0_0_36px_rgba(56,189,248,0.35)] transition hover:bg-cyan-300">
                <Link to="/usinas">
                  Selecione a usina
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button
                size="lg"
                variant="outline"
                className="h-12 rounded-full border-white/20 bg-white/[0.04] px-6 text-sm font-semibold text-white transition hover:bg-white/10"
                onClick={openDebug}
              >
                DEBUG
              </Button>
            </div>
          </div>

          <div className="relative hidden lg:block">
            <div className="absolute inset-8 rounded-full bg-sky-400/10 blur-3xl" />
            <div className="relative overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.035] p-5 shadow-2xl shadow-black/40 backdrop-blur-xl">
              <div className="mb-5 flex items-center justify-between border-b border-white/10 pb-4">
                <div>
                  <p className="text-xs uppercase tracking-[0.28em] text-slate-500">Painel CurtailIQ</p>
                  <p className="mt-1 text-sm text-slate-200">Análise operacional e regulatória</p>
                </div>
                <div className="rounded-full border border-cyan-300/20 bg-cyan-300/10 px-3 py-1 text-xs font-medium text-cyan-200">
                  NE renováveis
                </div>
              </div>

              <div className="grid gap-3">
                <div className="rounded-2xl border border-white/10 bg-black/20 p-4">
                  <div className="flex items-center justify-between text-sm text-slate-400">
                    <span>Perda estimada</span>
                    <BarChart3 className="h-4 w-4 text-sky-300" />
                  </div>
                  <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/10">
                    <div className="h-full w-[76%] rounded-full bg-gradient-to-r from-sky-400 to-cyan-300" />
                  </div>
                  <p className="mt-4 text-3xl font-semibold tracking-tight text-white">R$ 8,9 mi</p>
                  <p className="mt-1 text-xs text-slate-500">projeção energética futura</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <ShieldCheck className="mb-5 h-5 w-5 text-emerald-300" />
                    <p className="text-sm font-medium text-white">Ressarcimento</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">Regras determinísticas e evidências auditáveis.</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <Zap className="mb-5 h-5 w-5 text-amber-300" />
                    <p className="text-sm font-medium text-white">BESS</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">Simulações de captura de energia restringida por curtailment.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

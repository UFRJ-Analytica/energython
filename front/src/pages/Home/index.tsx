import { Link } from "react-router-dom"
import {
  ArrowRight,
  BarChart3,
  Battery,
  Bot,
  DollarSign,
  FileText,
  ShieldCheck,
  TrendingDown,
  Zap,
  AlertTriangle,
  Database,
  MapPin,
  BrainCircuit,
} from "lucide-react"
import { Button } from "@/components/ui/button"

const STATS = [
  { value: "20,6%", label: "da geração renovável cortada no Brasil em 2025" },
  { value: "R$ 6,5 bi", label: "em prejuízo distribuídos por ~1.500 usinas" },
  { value: "35%", label: "de corte médio nas solares do Nordeste" },
]

const ELOS = [
  {
    num: "01",
    tag: "Físico · ML",
    title: "Antecipe o corte",
    desc: "Nosso modelo de ML cruza dados climáticos abertos, a programação DESSEM e o histórico do ONS para prever com antecedência quando e quanto sua usina vai ser cortada.",
    icon: TrendingDown,
    glow: "rgba(56,189,248,0.15)",
    accent: "text-sky-300",
    border: "border-sky-400/20",
    bg: "bg-sky-400/5",
  },
  {
    num: "02",
    tag: "Financeiro · Risco",
    title: "Quantifique a perda",
    desc: "Cada hora cortada vira um número: MWh multiplicado pelo PLD. A partir daí você vê a exposição projetada, simula re-hedge e monta o business case de uma bateria com os dados reais da usina.",
    icon: DollarSign,
    glow: "rgba(34,211,238,0.15)",
    accent: "text-cyan-300",
    border: "border-cyan-400/20",
    bg: "bg-cyan-400/5",
  },
  {
    num: "03",
    tag: "Regulatório · IA",
    title: "Recupere o ressarcível",
    desc: "Cada corte é classificado automaticamente pela motivação regulatória, com base na REN 1.030/2022 e na Lei 15.269/2025. A IA monta o dossiê de pleito e responde dúvidas sobre as normas vigentes.",
    icon: ShieldCheck,
    glow: "rgba(52,211,153,0.15)",
    accent: "text-emerald-300",
    border: "border-emerald-400/20",
    bg: "bg-emerald-400/5",
  },
]

const FEATURES = [
  {
    icon: BarChart3,
    title: "Dashboard por usina",
    desc: "Perda total, razão de restrição e ticket médio por evento. Com rastreabilidade hora a hora.",
  },
  {
    icon: AlertTriangle,
    title: "Risco em tempo real",
    desc: "Probabilidade e magnitude de curtailment nas próximas 48h por planta do seu portfólio.",
  },
  {
    icon: DollarSign,
    title: "Análise financeira",
    desc: "Exposição ao PLD, perda realizada e projeção de exposição futura antes do fechamento da CCEE.",
  },
  {
    icon: Battery,
    title: "Simulador de BESS",
    desc: "Dimensione capacidade de bateria e calcule TIR/ROI com o padrão real de corte da usina.",
  },
  {
    icon: FileText,
    title: "Geração de dossiê",
    desc: "Rascunho de pleito regulatório gerado automaticamente, com evento, horário, MWh e enquadramento normativo.",
  },
  {
    icon: Bot,
    title: "Assistente regulatório",
    desc: "Chat com IA contextualizado à usina, com respostas baseadas em REN 1.030/2022 e CCEE.",
  },
]

const DATA_SOURCES = [
  { label: "ONS", desc: "Geração, COFF eólica e solar, disponibilidade" },
  { label: "CCEE", desc: "PLD horário por submercado" },
  { label: "ANEEL SIGA", desc: "Cadastro e localização de usinas" },
  { label: "Open-Meteo", desc: "Previsão climática (irradiância, vento)" },
]

const TECH_FACTS = [
  { icon: Database, value: "82M+", label: "registros reais do ONS processados" },
  { icon: BrainCircuit, value: "3 modelos", label: "ML com fallback inteligente (advanced → RF → sazonal)" },
  { icon: MapPin, value: "H3", label: "indexação geoespacial de usinas por cluster regional" },
]

export default function Home() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-[#05070b] text-white">
      {/* Background blobs */}
      <div className="pointer-events-none fixed inset-0 z-0">
        <div className="absolute left-1/2 top-[-18rem] h-[42rem] w-[42rem] -translate-x-1/2 rounded-full bg-sky-500/20 blur-3xl" />
        <div className="absolute bottom-[-14rem] right-[-10rem] h-[34rem] w-[34rem] rounded-full bg-cyan-400/10 blur-3xl" />
        <div className="absolute left-[-12rem] top-1/3 h-[30rem] w-[30rem] rounded-full bg-blue-700/15 blur-3xl" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(255,255,255,0.07)_1px,transparent_1px)] [background-size:28px_28px] opacity-20" />
      </div>

      {/* Header */}
      <header className="relative z-10 mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-3 rounded-full border border-white/10 bg-white px-4 py-2 shadow-[0_12px_40px_rgba(14,165,233,0.18)]">
          <img src="/logo.png" alt="CurtailIQ" className="h-8 w-12 object-cover object-left" />
          <span className="font-heading text-lg font-semibold tracking-[-0.04em] text-slate-950">CurtailIQ</span>
        </div>
        <Button
          asChild
          variant="ghost"
          className="hidden text-sm font-medium text-slate-300 hover:bg-white/5 hover:text-white sm:flex"
        >
          <Link to="/usinas">Acessar usinas</Link>
        </Button>
      </header>

      {/* ── HERO ─────────────────────────────────────── */}
      <section className="relative z-10 mx-auto flex min-h-[calc(100vh-88px)] max-w-6xl items-center px-6 pb-16 pt-8">
        <div className="grid w-full items-center gap-12 lg:grid-cols-[1.05fr_0.95fr]">
          {/* Left — headline */}
          <div className="max-w-3xl">
            <div className="mb-7 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-sky-100 shadow-[inset_0_1px_0_rgba(255,255,255,0.08)] backdrop-blur">
              <span className="h-1.5 w-1.5 rounded-full bg-cyan-300 shadow-[0_0_18px_rgba(103,232,249,0.9)]" />
              Inteligência de curtailment para geradoras renováveis
            </div>

            <h1 className="font-heading text-5xl font-semibold tracking-[-0.06em] text-white sm:text-6xl lg:text-7xl">
              Transforme cortes de geração em decisões financeiras.
            </h1>

            <p className="mt-6 max-w-2xl text-base leading-8 text-slate-300 sm:text-lg">
              O CurtailIQ mostra exatamente quando sua usina foi cortada, quanto isso custou e o que você pode recuperar regulatoriamente. Tudo com dados reais, em tempo real.
            </p>

            <div className="mt-9 flex flex-col gap-3 sm:flex-row">
              <Button
                asChild
                size="lg"
                className="h-12 rounded-full bg-sky-400 px-6 text-sm font-semibold text-slate-950 shadow-[0_0_36px_rgba(56,189,248,0.35)] transition hover:bg-cyan-300"
              >
                <Link to="/usinas">
                  Ver usinas
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
            </div>
          </div>

          {/* Right — mock dashboard panel */}
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
                  <p className="mt-1 text-xs text-slate-500">projeção energética futura · ML</p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <ShieldCheck className="mb-5 h-5 w-5 text-emerald-300" />
                    <p className="text-sm font-medium text-white">Ressarcimento</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">Evidências auditáveis e dossiê automático.</p>
                  </div>
                  <div className="rounded-2xl border border-white/10 bg-white/[0.03] p-4">
                    <Zap className="mb-5 h-5 w-5 text-amber-300" />
                    <p className="text-sm font-medium text-white">BESS</p>
                    <p className="mt-1 text-xs leading-5 text-slate-500">ROI de bateria com dados reais de corte.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── STATS BAR ────────────────────────────────── */}
      <section className="relative z-10 border-y border-white/[0.06] bg-white/[0.02] backdrop-blur-sm">
        <div className="mx-auto grid max-w-6xl grid-cols-1 divide-y divide-white/[0.06] px-6 sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          {STATS.map((s) => (
            <div key={s.value} className="flex flex-col gap-1 py-8 text-center sm:px-8">
              <span className="font-heading text-4xl font-bold tracking-tight text-sky-300">{s.value}</span>
              <span className="text-sm text-slate-400">{s.label}</span>
            </div>
          ))}
        </div>
      </section>

      {/* ── 3 ELOS ───────────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <div className="mb-14 max-w-xl">
          <p className="mb-3 text-xs font-semibold uppercase tracking-[0.25em] text-sky-400">Como resolvemos</p>
          <h2 className="font-heading text-4xl font-semibold tracking-tight text-white sm:text-5xl">
            Do corte físico ao pleito regulatório, em três etapas.
          </h2>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {ELOS.map((e) => {
            const Icon = e.icon
            return (
              <div
                key={e.num}
                className={`relative overflow-hidden rounded-2xl border ${e.border} ${e.bg} p-6 backdrop-blur-sm`}
              >
                <p className="mb-6 font-heading text-6xl font-bold tracking-tighter text-white/5">{e.num}</p>
                <div className={`mb-4 inline-flex items-center gap-1.5 rounded-full border ${e.border} bg-white/5 px-2.5 py-1 text-xs font-medium ${e.accent}`}>
                  <Icon className="h-3 w-3" />
                  {e.tag}
                </div>
                <h3 className={`mb-3 font-heading text-xl font-semibold ${e.accent}`}>{e.title}</h3>
                <p className="text-sm leading-7 text-slate-400">{e.desc}</p>
              </div>
            )
          })}
        </div>
      </section>

      {/* ── FEATURES GRID ────────────────────────────── */}
      <section className="relative z-10 border-t border-white/[0.06]">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-14 max-w-xl">
            <p className="mb-3 text-xs font-semibold uppercase tracking-[0.25em] text-cyan-400">O que você tem na plataforma</p>
            <h2 className="font-heading text-4xl font-semibold tracking-tight text-white sm:text-5xl">
              Tudo que o gerador precisa, em um lugar só.
            </h2>
          </div>

          <div className="grid gap-px overflow-hidden rounded-2xl border border-white/[0.06] sm:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => {
              const Icon = f.icon
              return (
                <div
                  key={f.title}
                  className="group bg-white/[0.02] p-6 transition hover:bg-white/[0.05]"
                >
                  <div className="mb-4 flex h-9 w-9 items-center justify-center rounded-xl border border-white/10 bg-white/5 transition group-hover:border-sky-400/30 group-hover:bg-sky-400/10">
                    <Icon className="h-4 w-4 text-slate-400 transition group-hover:text-sky-300" />
                  </div>
                  <p className="mb-1.5 text-sm font-semibold text-white">{f.title}</p>
                  <p className="text-xs leading-6 text-slate-500">{f.desc}</p>
                </div>
              )
            })}
          </div>
        </div>
      </section>

      {/* ── DATA FOUNDATION ─────────────────────────── */}
      <section className="relative z-10 border-t border-white/[0.06]">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-14 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
            <div className="max-w-lg">
              <p className="mb-3 text-xs font-semibold uppercase tracking-[0.25em] text-emerald-400">Base de dados</p>
              <h2 className="font-heading text-4xl font-semibold tracking-tight text-white sm:text-5xl">
                Dados públicos reais. Zero estimativa inventada.
              </h2>
            </div>
            <p className="max-w-sm text-sm leading-7 text-slate-400">
              Cada número que você vê aqui vem de fontes abertas verificáveis. São os mesmos dados que a CCEE e o ONS usam para operar o sistema elétrico brasileiro.
            </p>
          </div>

          {/* Tech facts */}
          <div className="mb-8 grid gap-4 sm:grid-cols-3">
            {TECH_FACTS.map((t) => {
              const Icon = t.icon
              return (
                <div key={t.label} className="flex items-start gap-4 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-emerald-400/20 bg-emerald-400/5">
                    <Icon className="h-5 w-5 text-emerald-300" />
                  </div>
                  <div>
                    <p className="font-heading text-lg font-bold text-white">{t.value}</p>
                    <p className="text-xs leading-5 text-slate-500">{t.label}</p>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Data sources */}
          <div className="grid gap-px overflow-hidden rounded-xl border border-white/[0.06] sm:grid-cols-4">
            {DATA_SOURCES.map((s) => (
              <div key={s.label} className="bg-white/[0.015] px-5 py-4">
                <p className="mb-1 font-heading text-sm font-semibold text-sky-300">{s.label}</p>
                <p className="text-xs leading-5 text-slate-500">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA SECTION ──────────────────────────────── */}
      <section className="relative z-10 mx-auto max-w-6xl px-6 py-24">
        <div className="relative overflow-hidden rounded-3xl border border-sky-400/20 bg-gradient-to-br from-sky-400/10 via-transparent to-cyan-400/5 p-10 text-center shadow-[inset_0_1px_0_rgba(56,189,248,0.1)] sm:p-16">
          <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(56,189,248,0.08),transparent_70%)]" />
          <p className="relative mb-4 text-xs font-semibold uppercase tracking-[0.25em] text-sky-400">
            Pronto para começar
          </p>
          <h2 className="relative font-heading text-3xl font-semibold tracking-tight text-white sm:text-5xl">
            Veja o que sua usina perdeu<br className="hidden sm:block" />
            e quanto você ainda pode recuperar.
          </h2>
          <p className="relative mx-auto mt-4 max-w-xl text-base text-slate-400">
            Escolha uma usina e veja em minutos: perdas acumuladas, risco de corte, simulação de BESS e o que você tem direito a ressarcir.
          </p>
          <div className="relative mt-8">
            <Button
              asChild
              size="lg"
              className="h-12 rounded-full bg-sky-400 px-8 text-sm font-semibold text-slate-950 shadow-[0_0_48px_rgba(56,189,248,0.4)] transition hover:bg-cyan-300"
            >
              <Link to="/usinas">
                Selecionar usina
                <ArrowRight className="ml-2 h-4 w-4" />
              </Link>
            </Button>
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────── */}
      <footer className="relative z-10 border-t border-white/[0.06] py-8 text-center text-xs text-slate-600">
        CurtailIQ · Analytica Energython · 2026
      </footer>
    </div>
  )
}

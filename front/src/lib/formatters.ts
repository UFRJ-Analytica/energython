const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 })
const pct = new Intl.NumberFormat("pt-BR", { style: "percent", maximumFractionDigits: 1 })
const num = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 2 })

export const fmtBRL = (v: number) => brl.format(v)
export const fmtPct = (v: number) => pct.format(v / 100)
export const fmtMWh = (v: number) => `${num.format(v)} MWh`
export const fmtMW = (v: number) => `${num.format(v)} MW`
export const fmtNum = (v: number) => num.format(v)

export const fmtDate = (iso: string) =>
  new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", year: "2-digit", hour: "2-digit", minute: "2-digit" })

export const toIso = (d: Date) => d.toISOString().replace("Z", "")

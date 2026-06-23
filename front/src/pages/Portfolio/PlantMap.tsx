import "leaflet/dist/leaflet.css"

import L from "leaflet"
import { useMemo } from "react"
import { useNavigate } from "react-router-dom"
import { MapContainer, Marker, Popup, TileLayer, Tooltip } from "react-leaflet"
import { Button } from "@/components/ui/button"
import type { UsinaOut } from "@/types/usinas"
import { fmtBRL, fmtMWh, fmtMW } from "@/lib/formatters"

interface Props {
  usinas: UsinaOut[]
}

function toNum(v: unknown): number | null {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

function compactBRL(value: number) {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    notation: "compact",
    maximumFractionDigits: 1,
  }).format(value)
}

function sourceLabel(fonte: string) {
  return fonte === "solar" ? "Solar" : fonte === "eolica" ? "Eólica" : fonte
}

function markerIcon(fonte: string, perda: number, maxPerda: number) {
  const scale = Math.sqrt(Math.max(perda, 0) / Math.max(maxPerda, 1))
  const size = Math.round(34 + scale * 22)
  const isSolar = fonte === "solar"
  const glyph = isSolar
    ? `<svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"/></svg>`
    : `<svg viewBox="0 0 24 24" width="19" height="19" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h11a3 3 0 1 0-3-3"/><path d="M4 14h15a3 3 0 1 1-3 3"/><path d="M2 20h9"/></svg>`
  const gradient = isSolar
    ? "linear-gradient(135deg,#fde68a 0%,#f59e0b 46%,#ef4444 100%)"
    : "linear-gradient(135deg,#7dd3fc 0%,#0ea5e9 45%,#6366f1 100%)"
  const shadow = isSolar ? "rgba(245,158,11,.45)" : "rgba(14,165,233,.45)"

  return L.divIcon({
    className: "curtailiq-plant-marker",
    html: `
      <div style="position:relative;width:${size}px;height:${size}px;transform:translate(-50%,-50%);">
        <div style="position:absolute;inset:-8px;border-radius:999px;background:${shadow};filter:blur(14px);opacity:.55;"></div>
        <div style="position:absolute;inset:0;border-radius:999px;background:${gradient};box-shadow:0 14px 34px ${shadow}, inset 0 1px 0 rgba(255,255,255,.55);border:1px solid rgba(255,255,255,.7);display:grid;place-items:center;color:white;">
          ${glyph}
        </div>
        <div style="position:absolute;left:50%;bottom:-5px;width:12px;height:12px;transform:translateX(-50%) rotate(45deg);background:${gradient};border-right:1px solid rgba(255,255,255,.55);border-bottom:1px solid rgba(255,255,255,.55);"></div>
      </div>
    `,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
    popupAnchor: [0, -size / 2],
    tooltipAnchor: [0, -size / 2],
  })
}

export function PlantMap({ usinas }: Props) {
  const navigate = useNavigate()
  const points = useMemo(
    () =>
      usinas
        .map((u) => ({
          ...u,
          latitude: toNum(u.latitude),
          longitude: toNum(u.longitude),
        }))
        .filter(
          (u): u is UsinaOut & { latitude: number; longitude: number } =>
            u.latitude !== null && u.longitude !== null,
        ),
    [usinas],
  )

  const center: [number, number] = useMemo(() => {
    if (!points.length) return [-9.5, -39.5]
    const lat = points.reduce((acc, p) => acc + p.latitude, 0) / points.length
    const lon = points.reduce((acc, p) => acc + p.longitude, 0) / points.length
    return [lat, lon]
  }, [points])

  const maxPerda = useMemo(
    () => Math.max(...points.map((p) => Number(p.total_perda_reais || 0)), 1),
    [points],
  )
  const topPerda = points[0]

  if (!points.length) {
    return (
      <div className="rounded-[2rem] border border-border/60 bg-card p-8 text-sm text-muted-foreground">
        Sem coordenadas para as usinas retornadas pelo backend.
      </div>
    )
  }

  return (
    <div className="overflow-hidden rounded-[2rem] border border-border/60 bg-card shadow-[0_30px_120px_rgba(0,0,0,0.28)]">
      <div className="relative">
        <MapContainer
          center={center}
          zoom={6}
          minZoom={4}
          maxZoom={13}
          scrollWheelZoom
          className="h-[680px] w-full bg-slate-950"
          zoomControl
        >
          <TileLayer
            attribution='&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />

          {points.map((u) => (
            <Marker
              key={u.usina_id}
              position={[u.latitude, u.longitude]}
              icon={markerIcon(u.fonte, Number(u.total_perda_reais || 0), maxPerda)}
            >
              <Tooltip direction="top" offset={[0, -18]} opacity={0.96}>
                <div className="text-xs">
                  <strong>{u.nome}</strong><br />
                  {compactBRL(Number(u.total_perda_reais || 0))} · {sourceLabel(u.fonte)}
                </div>
              </Tooltip>
              <Popup>
                <div className="min-w-56 space-y-2 text-xs">
                  <div>
                    <div className="text-sm font-semibold">{u.nome}</div>
                    <div className="text-muted-foreground">{sourceLabel(u.fonte)} · {u.submercado} · ID ONS {u.id_ons ?? "—"}</div>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <div className="rounded-lg bg-rose-500/10 p-2">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Perda financeira</div>
                      <div className="font-semibold text-rose-500">{fmtBRL(Number(u.total_perda_reais || 0))}</div>
                    </div>
                    <div className="rounded-lg bg-sky-500/10 p-2">
                      <div className="text-[10px] uppercase tracking-wider text-muted-foreground">Energia</div>
                      <div className="font-semibold text-sky-500">{fmtMWh(Number(u.total_corte_mwh || 0))}</div>
                    </div>
                  </div>
                  <div>Capacidade: {fmtMW(Number(u.potencia_mw || 0))}</div>
                  {u.ceg && <div>CEG: {u.ceg}</div>}
                  {u.nom_conjuntousina && <div>Conjunto ONS: {u.nom_conjuntousina}</div>}
                  <Button
                    size="sm"
                    className="mt-2 h-8 w-full text-xs"
                    onClick={() => navigate(`/usinas/${u.usina_id}`)}
                  >
                    Abrir análise da usina
                  </Button>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>

        <div className="pointer-events-none absolute left-4 top-4 z-[500] max-w-sm rounded-2xl border border-white/10 bg-slate-950/80 p-4 text-white shadow-2xl backdrop-blur-md">
          <p className="text-[10px] font-semibold uppercase tracking-[0.24em] text-emerald-300/80">Curtailment NE</p>
          <p className="mt-1 text-lg font-black">{points.length} usinas mapeadas</p>
          {topPerda ? (
            <p className="mt-1 text-xs text-slate-300">
              Maior perda: <span className="font-semibold text-rose-200">{topPerda.nome}</span> · {compactBRL(Number(topPerda.total_perda_reais || 0))}
            </p>
          ) : null}
        </div>

        <div className="pointer-events-none absolute bottom-4 left-4 z-[500] flex flex-wrap gap-2 rounded-2xl border border-white/10 bg-slate-950/80 p-3 text-xs text-white shadow-2xl backdrop-blur-md">
          <span className="inline-flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-gradient-to-br from-sky-300 to-indigo-500 shadow-[0_0_16px_rgba(14,165,233,.75)]" /> Eólica</span>
          <span className="inline-flex items-center gap-2"><span className="h-3 w-3 rounded-full bg-gradient-to-br from-amber-200 to-red-500 shadow-[0_0_16px_rgba(245,158,11,.75)]" /> Solar</span>
          <span className="text-slate-300">Tamanho = perda financeira</span>
        </div>
      </div>
    </div>
  )
}

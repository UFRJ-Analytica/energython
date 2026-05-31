import { useMemo, useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { UsinaOut } from "@/types/usinas"

interface Props {
  usinas: UsinaOut[]
}

type Point = { usina: UsinaOut; x: number; y: number }

const BOUNDS_NE = {
  minLat: -18,
  maxLat: 1,
  minLon: -48,
  maxLon: -32,
}

function project(lat: number, lon: number, width: number, height: number) {
  const x = ((lon - BOUNDS_NE.minLon) / (BOUNDS_NE.maxLon - BOUNDS_NE.minLon)) * width
  const y = ((BOUNDS_NE.maxLat - lat) / (BOUNDS_NE.maxLat - BOUNDS_NE.minLat)) * height
  return { x, y }
}

export function PlantMap({ usinas }: Props) {
  const [hovered, setHovered] = useState<Point | null>(null)

  const points = useMemo(() => {
    const width = 1000
    const height = 420
    return usinas
      .filter((u) => typeof u.latitude === "number" && typeof u.longitude === "number")
      .map((u) => {
        const { x, y } = project(u.latitude as number, u.longitude as number, width, height)
        return { usina: u, x, y }
      })
  }, [usinas])

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Mapa das usinas do Nordeste</CardTitle>
      </CardHeader>
      <CardContent>
        {points.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sem coordenadas para as usinas filtradas.</p>
        ) : (
          <div className="relative">
            <svg viewBox="0 0 1000 420" className="h-[320px] w-full rounded-md border bg-slate-950/95">
              <rect x="0" y="0" width="1000" height="420" fill="#0b1220" />
              <g opacity="0.2">
                {Array.from({ length: 9 }).map((_, i) => (
                  <line key={`v-${i}`} x1={i * 125} y1={0} x2={i * 125} y2={420} stroke="#60a5fa" strokeWidth="1" />
                ))}
                {Array.from({ length: 7 }).map((_, i) => (
                  <line key={`h-${i}`} x1={0} y1={i * 70} x2={1000} y2={i * 70} stroke="#60a5fa" strokeWidth="1" />
                ))}
              </g>
              {points.map((p) => (
                <g
                  key={p.usina.usina_id}
                  onMouseEnter={() => setHovered(p)}
                  onMouseLeave={() => setHovered(null)}
                >
                  <circle cx={p.x} cy={p.y} r={6} fill={p.usina.fonte === "solar" ? "#f59e0b" : "#38bdf8"} stroke="#fff" strokeWidth={1.5} />
                </g>
              ))}
            </svg>

            {hovered && (
              <div
                className="pointer-events-none absolute z-10 w-64 rounded-md border bg-background p-2 text-xs shadow"
                style={{ left: `${(hovered.x / 1000) * 100}%`, top: `${(hovered.y / 420) * 100}%`, transform: "translate(8px, -110%)" }}
              >
                <div className="font-semibold">{hovered.usina.nome}</div>
                <div>ID: {hovered.usina.usina_id}</div>
                <div>Fonte: {hovered.usina.fonte}</div>
                <div>Capacidade: {hovered.usina.potencia_mw.toFixed(2)} MW</div>
                <div>Submercado: {hovered.usina.submercado}</div>
                <div>
                  Lat/Lon: {(hovered.usina.latitude as number).toFixed(4)}, {(hovered.usina.longitude as number).toFixed(4)}
                </div>
              </div>
            )}
          </div>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          Passe o mouse nos pontos para ver as informações da usina.
        </p>
      </CardContent>
    </Card>
  )
}

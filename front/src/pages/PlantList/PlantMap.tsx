import "leaflet/dist/leaflet.css"

import { useMemo } from "react"
import { useNavigate } from "react-router-dom"
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import type { UsinaOut } from "@/types/usinas"

interface Props {
  usinas: UsinaOut[]
}

function toNum(v: unknown): number | null {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
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

  const maxCurtailment = useMemo(
    () => Math.max(...points.map((p) => Number(p.total_corte_mwh || 0)), 1),
    [points],
  )

  if (!points.length) {
    return (
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium">Mapa das usinas (NE)</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Coordenadas indisponíveis para as usinas desta página.
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Mapa das usinas (NE)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <div className="overflow-hidden rounded-md border">
          <MapContainer
            center={center}
            zoom={6}
            minZoom={4}
            maxZoom={12}
            scrollWheelZoom
            className="h-[320px] w-full"
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />

            {points.map((u) => (
              <CircleMarker
                key={u.usina_id}
                center={[u.latitude, u.longitude]}
                radius={6 + 10 * Math.sqrt(Number(u.total_corte_mwh || 0) / maxCurtailment)}
                pathOptions={{
                  color: "#ffffff",
                  weight: 1,
                  fillOpacity: 0.9,
                  fillColor: u.fonte === "solar" ? "#f59e0b" : "#38bdf8",
                }}
              >
                <Popup>
                  <div className="space-y-1 text-xs">
                    <div className="font-semibold">{u.nome}</div>
                    <div className="text-[11px] uppercase tracking-wide text-muted-foreground">Usina individual</div>
                    <div>ID ONS: {u.id_ons ?? u.usina_id}</div>
                    {u.ceg && <div>CEG: {u.ceg}</div>}
                    <div>Fonte: {u.fonte}</div>
                    <div>Capacidade da usina: {u.potencia_mw.toFixed(2)} MW</div>
                    {u.nom_conjuntousina && <div>Conjunto regulatório: {u.nom_conjuntousina}</div>}
                    {typeof u.total_corte_mwh === "number" && (
                      <div>Perda energética: {u.total_corte_mwh.toLocaleString("pt-BR", { maximumFractionDigits: 2 })} MWh</div>
                    )}
                    {typeof u.total_ressarcivel_mwh === "number" && (
                      <div>Energia ressarcível: {u.total_ressarcivel_mwh.toLocaleString("pt-BR", { maximumFractionDigits: 2 })} MWh</div>
                    )}
                    <div>Submercado: {u.submercado}</div>
                    <div>
                      Lat/Lon: {u.latitude.toFixed(4)}, {u.longitude.toFixed(4)}
                    </div>
                    <Button
                      size="sm"
                      className="mt-2 h-7 w-full text-xs"
                      onClick={() => navigate(`/usinas/${u.usina_id}`)}
                    >
                      Selecionar usina e ir para análise
                    </Button>
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
        <p className="text-xs text-muted-foreground">
          {points.length} usinas individuais com coordenadas nesta página. O conjunto ONS aparece apenas como metadado regulatório; o tamanho do marcador segue a energia cortada (MWh).
        </p>
      </CardContent>
    </Card>
  )
}

import "leaflet/dist/leaflet.css"

import { useMemo } from "react"
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { UsinaOut } from "@/types/usinas"

interface Props {
  usinas: UsinaOut[]
}

export function PlantMap({ usinas }: Props) {
  const points = useMemo(
    () =>
      usinas.filter(
        (u) => typeof u.latitude === "number" && typeof u.longitude === "number",
      ) as Array<UsinaOut & { latitude: number; longitude: number }>,
    [usinas],
  )

  const center: [number, number] = useMemo(() => {
    if (!points.length) return [-9.5, -39.5]
    const lat = points.reduce((acc, p) => acc + p.latitude, 0) / points.length
    const lon = points.reduce((acc, p) => acc + p.longitude, 0) / points.length
    return [lat, lon]
  }, [points])

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Mapa das usinas do Nordeste</CardTitle>
      </CardHeader>
      <CardContent>
        {points.length === 0 ? (
          <p className="text-sm text-muted-foreground">Sem coordenadas para as usinas filtradas.</p>
        ) : (
          <div className="overflow-hidden rounded-md border">
            <MapContainer
              center={center}
              zoom={6}
              minZoom={4}
              maxZoom={12}
              scrollWheelZoom
              className="h-[380px] w-full"
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />

              {points.map((u) => (
                <CircleMarker
                  key={u.usina_id}
                  center={[u.latitude, u.longitude]}
                  radius={6}
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
                      <div>ID: {u.usina_id}</div>
                      <div>Fonte: {u.fonte}</div>
                      <div>Capacidade: {u.potencia_mw.toFixed(2)} MW</div>
                      <div>Submercado: {u.submercado}</div>
                      <div>
                        Lat/Lon: {u.latitude.toFixed(4)}, {u.longitude.toFixed(4)}
                      </div>
                    </div>
                  </Popup>
                </CircleMarker>
              ))}
            </MapContainer>
          </div>
        )}
        <p className="mt-2 text-xs text-muted-foreground">
          Arraste para navegar e use zoom (+/- ou scroll) para explorar as usinas.
        </p>
      </CardContent>
    </Card>
  )
}

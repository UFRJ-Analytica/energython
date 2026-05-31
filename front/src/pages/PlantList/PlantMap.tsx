import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { UsinaOut } from "@/types/usinas"

interface Props {
  usinas: UsinaOut[]
}

function toNum(v: unknown): number | null {
  const n = Number(v)
  return Number.isFinite(n) ? n : null
}

export function PlantMap({ usinas }: Props) {
  const points = usinas
    .map((u) => ({
      id: u.usina_id,
      nome: u.nome,
      lat: toNum(u.latitude),
      lon: toNum(u.longitude),
    }))
    .filter((p) => p.lat !== null && p.lon !== null) as Array<{ id: string; nome: string; lat: number; lon: number }>

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

  const centerLat = points.reduce((acc, p) => acc + p.lat, 0) / points.length
  const centerLon = points.reduce((acc, p) => acc + p.lon, 0) / points.length
  const markers = points
    .map((p) => `${p.lat.toFixed(6)},${p.lon.toFixed(6)},red-pushpin`)
    .join("|")

  const mapUrl = `https://staticmap.openstreetmap.de/staticmap.php?center=${centerLat.toFixed(6)},${centerLon.toFixed(6)}&zoom=5&size=1024x360&maptype=mapnik&markers=${encodeURIComponent(markers)}`

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">Mapa das usinas (NE)</CardTitle>
      </CardHeader>
      <CardContent className="space-y-2">
        <img
          src={mapUrl}
          alt="Mapa com localização das usinas da página"
          className="h-[280px] w-full rounded-md border object-cover"
          loading="lazy"
        />
        <p className="text-xs text-muted-foreground">
          {points.length} usinas com coordenadas nesta página. Fonte cartográfica: OpenStreetMap.
        </p>
      </CardContent>
    </Card>
  )
}

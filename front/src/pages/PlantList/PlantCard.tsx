import { useNavigate } from "react-router-dom"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Sun, Wind } from "lucide-react"
import type { UsinaOut } from "@/types/usinas"
import { fmtMWh, fmtMW } from "@/lib/formatters"

interface Props {
  usina: UsinaOut
}

export function PlantCard({ usina }: Props) {
  const navigate = useNavigate()

  return (
    <Card
      className="cursor-pointer transition-shadow hover:shadow-md"
      onClick={() => navigate(`/usinas/${usina.usina_id}`)}
    >
      <CardHeader className="flex flex-row items-start justify-between pb-2">
        <CardTitle className="text-base">{usina.nome}</CardTitle>
        {usina.fonte === "solar" ? (
          <Sun className="h-5 w-5 text-yellow-500 shrink-0" />
        ) : (
          <Wind className="h-5 w-5 text-blue-500 shrink-0" />
        )}
      </CardHeader>
      <CardContent className="space-y-2 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Badge variant="outline">{usina.submercado}</Badge>
          <span>{fmtMW(usina.potencia_mw)}</span>
        </div>
        {usina.nom_conjuntousina && (
          <p className="text-xs">Conjunto regulatório: {usina.nom_conjuntousina}</p>
        )}
        {typeof usina.total_corte_mwh === "number" && (
          <p className="text-xs">Energia cortada: {fmtMWh(usina.total_corte_mwh)}</p>
        )}
      </CardContent>
    </Card>
  )
}

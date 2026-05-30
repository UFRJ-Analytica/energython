import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertTriangle, CheckCircle, XCircle } from "lucide-react"
import { QUALIDADE_LABELS } from "@/lib/constants"
import type { QualidadeDados } from "@/types/financeiro"

const icons = {
  completo: <CheckCircle className="h-4 w-4 text-green-500" />,
  parcial: <AlertTriangle className="h-4 w-4 text-yellow-500" />,
  sem_pld: <XCircle className="h-4 w-4 text-red-500" />,
}

interface Props {
  qualidade: QualidadeDados
}

export function DataQualityBanner({ qualidade }: Props) {
  if (qualidade.status === "completo") return null

  return (
    <Alert variant="default" className="border-yellow-500/40 bg-yellow-500/5">
      <div className="flex items-center gap-2">
        {icons[qualidade.status]}
        <AlertDescription>
          {QUALIDADE_LABELS[qualidade.status]} — {qualidade.pld_faltante_eventos} de {qualidade.total_eventos} eventos sem
          PLD
        </AlertDescription>
      </div>
    </Alert>
  )
}

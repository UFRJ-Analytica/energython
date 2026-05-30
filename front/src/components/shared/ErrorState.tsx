import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { AlertCircle } from "lucide-react"
import { ApiException } from "@/api/client"

interface Props {
  error: unknown
}

export function ErrorState({ error }: Props) {
  const title = error instanceof ApiException ? error.code : "Erro inesperado"
  const detail = error instanceof Error ? error.message : "Não foi possível carregar os dados."

  return (
    <Alert variant="destructive">
      <AlertCircle className="h-4 w-4" />
      <AlertTitle className="font-mono text-xs">{title}</AlertTitle>
      <AlertDescription>{detail}</AlertDescription>
    </Alert>
  )
}

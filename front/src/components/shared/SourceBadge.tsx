import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip"

interface Props {
  fonte: "gold" | "ia"
  confianca: number
  justificativa?: string
}

export function SourceBadge({ fonte, confianca, justificativa }: Props) {
  const label = fonte === "gold" ? "Gold" : `IA ${Math.round(confianca * 100)}%`
  const variant = fonte === "gold" ? "default" : confianca >= 0.8 ? "secondary" : "outline"

  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Badge variant={variant} className="cursor-default">{label}</Badge>
      </TooltipTrigger>
      {justificativa && (
        <TooltipContent side="top" className="max-w-xs">
          {justificativa}
        </TooltipContent>
      )}
    </Tooltip>
  )
}

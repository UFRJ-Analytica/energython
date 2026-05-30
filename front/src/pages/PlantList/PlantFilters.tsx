import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { FONTES, SUBMERCADOS } from "@/lib/constants"

interface Props {
  fonte: string
  submercado: string
  onFonte: (v: string) => void
  onSubmercado: (v: string) => void
}

export function PlantFilters({ fonte, submercado, onFonte, onSubmercado }: Props) {
  return (
    <div className="flex gap-3">
      <Select value={fonte} onValueChange={onFonte}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="Fonte" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todas as fontes</SelectItem>
          {FONTES.map((f) => (
            <SelectItem key={f} value={f}>{f === "solar" ? "Solar" : "Eólica"}</SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select value={submercado} onValueChange={onSubmercado}>
        <SelectTrigger className="w-36">
          <SelectValue placeholder="Submercado" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">Todos</SelectItem>
          {SUBMERCADOS.map((s) => (
            <SelectItem key={s} value={s}>{s}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}

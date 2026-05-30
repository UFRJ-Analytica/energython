import { useState } from "react"
import { format, subDays } from "date-fns"
import { ptBR } from "date-fns/locale"
import { CalendarIcon } from "lucide-react"
import type { DateRange } from "react-day-picker"
import { Button } from "@/components/ui/button"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { toIso } from "@/lib/formatters"

interface Props {
  onChange: (inicio: string, fim: string) => void
  defaultDays?: number
}

export function DateRangePicker({ onChange, defaultDays = 30 }: Props) {
  const [range, setRange] = useState<DateRange>({
    from: subDays(new Date(), defaultDays),
    to: new Date(),
  })

  const handleSelect = (r?: DateRange) => {
    if (!r) return
    setRange(r)
    if (r.from && r.to) onChange(toIso(r.from), toIso(r.to))
  }

  const label =
    range.from && range.to
      ? `${format(range.from, "dd/MM/yy")} – ${format(range.to, "dd/MM/yy")}`
      : "Selecionar período"

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm" className="gap-2">
          <CalendarIcon className="h-4 w-4" />
          {label}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="end">
        <Calendar mode="range" selected={range} onSelect={handleSelect} locale={ptBR} numberOfMonths={2} />
      </PopoverContent>
    </Popover>
  )
}

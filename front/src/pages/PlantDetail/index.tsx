import { useNavigate, useParams } from "react-router-dom"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { DateRangePicker } from "@/components/shared/DateRangePicker"
import { ErrorState } from "@/components/shared/ErrorState"
import { usePlantDateRange } from "@/hooks/usePlantDateRange"
import { useUsina } from "@/hooks/useUsinas"
import { SummaryTab } from "./SummaryTab"
import { FinanceiroTab } from "./FinanceiroTab"
import { RegulatorioTab } from "./RegulatorioTab"

export default function PlantDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: usina, isLoading, error } = useUsina(id!)
  const dateRange = usePlantDateRange(usina?.data_fim)

  if (isLoading) return <div className="container mx-auto max-w-5xl px-4 py-8"><Skeleton className="h-12 w-64" /></div>
  if (error) return <div className="container mx-auto max-w-5xl px-4 py-8"><ErrorState error={error} /></div>

  return (
    <div className="container mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/usinas")}>
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div>
            <h1 className="text-xl font-bold">{usina?.nome}</h1>
            <p className="text-xs text-muted-foreground">
              {usina?.fonte === "solar" ? "Solar" : "Eólica"} · {usina?.potencia_mw} MW · {usina?.submercado}
            </p>
          </div>
        </div>
        <DateRangePicker
          initialFrom={dateRange.inicio ? new Date(dateRange.inicio) : undefined}
          initialTo={dateRange.fim ? new Date(dateRange.fim) : undefined}
          minDate={dateRange.minDate}
          maxDate={dateRange.maxDate}
          onChange={dateRange.setRange}
        />
      </div>

      <Tabs defaultValue="resumo">
        <TabsList className="mb-6">
          <TabsTrigger value="resumo">Visão Geral</TabsTrigger>
          <TabsTrigger value="financeiro">Financeiro</TabsTrigger>
          <TabsTrigger value="regulatorio">Regulatório</TabsTrigger>
        </TabsList>

        <TabsContent value="resumo">
          <SummaryTab usinaId={id!} inicio={dateRange.inicio} fim={dateRange.fim} />
        </TabsContent>

        <TabsContent value="financeiro">
          <FinanceiroTab usinaId={id!} inicio={dateRange.inicio} fim={dateRange.fim} />
        </TabsContent>

        <TabsContent value="regulatorio">
          <RegulatorioTab usinaId={id!} inicio={dateRange.inicio} fim={dateRange.fim} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

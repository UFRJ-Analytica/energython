import { useState } from "react"
import { useNavigate, useParams } from "react-router-dom"
import { subDays } from "date-fns"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { DateRangePicker } from "@/components/shared/DateRangePicker"
import { ErrorState } from "@/components/shared/ErrorState"
import { useUsina } from "@/hooks/useUsinas"
import { toIso } from "@/lib/formatters"
import { SummaryTab } from "./SummaryTab"
import { FinanceiroTab } from "./FinanceiroTab"
import { RegulatorioTab } from "./RegulatorioTab"

export default function PlantDetail() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const { data: usina, isLoading, error } = useUsina(id!)

  const [inicio, setInicio] = useState(() => toIso(subDays(new Date(), 30)))
  const [fim, setFim] = useState(() => toIso(new Date()))

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
        <DateRangePicker onChange={(i, f) => { setInicio(i); setFim(f) }} />
      </div>

      <Tabs defaultValue="resumo">
        <TabsList className="mb-6">
          <TabsTrigger value="resumo">Visão Geral</TabsTrigger>
          <TabsTrigger value="financeiro">Financeiro</TabsTrigger>
          <TabsTrigger value="regulatorio">Regulatório</TabsTrigger>
        </TabsList>

        <TabsContent value="resumo">
          <SummaryTab usinaId={id!} inicio={inicio} fim={fim} />
        </TabsContent>

        <TabsContent value="financeiro">
          <FinanceiroTab usinaId={id!} inicio={inicio} fim={fim} />
        </TabsContent>

        <TabsContent value="regulatorio">
          <RegulatorioTab usinaId={id!} inicio={inicio} fim={fim} />
        </TabsContent>
      </Tabs>
    </div>
  )
}

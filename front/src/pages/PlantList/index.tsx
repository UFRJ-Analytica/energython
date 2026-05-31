import { useState } from "react"
import { Skeleton } from "@/components/ui/skeleton"
import { Button } from "@/components/ui/button"
import { ErrorState } from "@/components/shared/ErrorState"
import { useUsinas } from "@/hooks/useUsinas"
import { PlantCard } from "./PlantCard"
import { PlantFilters } from "./PlantFilters"
import { PlantMap } from "./PlantMap"

const LIMIT = 12

export default function PlantList() {
  const [fonte, setFonte] = useState("all")
  const [submercado, setSubmercado] = useState("all")
  const [offset, setOffset] = useState(0)

  const { data, isLoading, error } = useUsinas({
    fonte: fonte !== "all" ? fonte : undefined,
    submercado: submercado !== "all" ? submercado : undefined,
    limit: LIMIT,
    offset,
  })

  return (
    <div className="container mx-auto max-w-5xl px-4 py-8">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Usinas</h1>
          <p className="text-sm text-muted-foreground">Selecione uma usina para analisar</p>
        </div>
        <PlantFilters
          fonte={fonte}
          submercado={submercado}
          onFonte={(v) => { setFonte(v); setOffset(0) }}
          onSubmercado={(v) => { setSubmercado(v); setOffset(0) }}
        />
      </div>

      {error && <ErrorState error={error} />}

      {isLoading ? (
        <>
          <Skeleton className="mb-4 h-72 w-full rounded-xl" />
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-28 rounded-xl" />)}
          </div>
        </>
      ) : (
        <>
          {data && <div className="mb-4"><PlantMap usinas={data.items} /></div>}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3">
            {data?.items.map((u) => <PlantCard key={u.usina_id} usina={u} />)}
          </div>

          {data && data.total_count > LIMIT && (
            <div className="mt-6 flex justify-center gap-3">
              <Button variant="outline" size="sm" disabled={offset === 0} onClick={() => setOffset((o) => o - LIMIT)}>
                Anterior
              </Button>
              <span className="self-center text-sm text-muted-foreground">
                {Math.floor(offset / LIMIT) + 1} / {Math.ceil(data.total_count / LIMIT)}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={offset + LIMIT >= data.total_count}
                onClick={() => setOffset((o) => o + LIMIT)}
              >
                Próxima
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}

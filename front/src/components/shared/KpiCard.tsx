import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { ReactNode } from "react"

interface Props {
  title: string
  value: string
  sub?: string
  icon?: ReactNode
  highlight?: "success" | "warning" | "danger"
}

const colors = {
  success: "text-green-500",
  warning: "text-yellow-500",
  danger: "text-red-500",
}

export function KpiCard({ title, value, sub, icon, highlight }: Props) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
        {icon}
      </CardHeader>
      <CardContent>
        <p className={`text-2xl font-bold ${highlight ? colors[highlight] : ""}`}>{value}</p>
        {sub && <p className="mt-1 text-xs text-muted-foreground">{sub}</p>}
      </CardContent>
    </Card>
  )
}

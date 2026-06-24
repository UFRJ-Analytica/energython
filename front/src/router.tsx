import { Suspense, lazy, type ReactNode } from "react"
import { createBrowserRouter } from "react-router-dom"

const Home = lazy(() => import("@/pages/Home"))
const Build = lazy(() => import("@/pages/Build"))
const Portfolio = lazy(() => import("@/pages/Portfolio"))
const PlantShell = lazy(() => import("@/components/PlantShell").then((module) => ({ default: module.PlantShell })))
const Resumo = lazy(() => import("@/pages/Resumo"))
const Financeiro = lazy(() => import("@/pages/Financeiro"))
const Simulador = lazy(() => import("@/pages/Simulador"))
const Dossie = lazy(() => import("@/pages/Dossie"))
const Chat = lazy(() => import("@/pages/Chat"))

function PageLoader() {
  return (
    <div className="min-h-screen bg-background px-4 py-8 text-foreground">
      <div className="container mx-auto max-w-5xl space-y-4">
        <div className="h-10 w-52 animate-pulse rounded-lg bg-muted" />
        <div className="grid gap-4 md:grid-cols-3">
          <div className="h-28 animate-pulse rounded-xl bg-muted" />
          <div className="h-28 animate-pulse rounded-xl bg-muted" />
          <div className="h-28 animate-pulse rounded-xl bg-muted" />
        </div>
      </div>
    </div>
  )
}

function lazyPage(element: ReactNode) {
  return <Suspense fallback={<PageLoader />}>{element}</Suspense>
}

export const router = createBrowserRouter([
  { path: "/", element: lazyPage(<Home />) },
  { path: "/build", element: lazyPage(<Build />) },
  { path: "/usinas", element: lazyPage(<Portfolio />) },
  {
    path: "/usinas/:id",
    element: lazyPage(<PlantShell />),
    children: [
      { index: true, element: lazyPage(<Resumo />) },
      { path: "financeiro", element: lazyPage(<Financeiro />) },
      { path: "bess", element: lazyPage(<Simulador />) },
      { path: "dossie", element: lazyPage(<Dossie />) },
      { path: "chat", element: lazyPage(<Chat />) },
    ],
  },
])

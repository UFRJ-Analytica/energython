import { createBrowserRouter } from "react-router-dom"
import { PlantShell } from "@/components/PlantShell"
import Home from "@/pages/Home"
import Portfolio from "@/pages/Portfolio"
import Resumo from "@/pages/Resumo"
import Financeiro from "@/pages/Financeiro"
import Simulador from "@/pages/Simulador"
import Dossie from "@/pages/Dossie"
import Chat from "@/pages/Chat"
import Build from "@/pages/Build"

export const router = createBrowserRouter([
  { path: "/", element: <Home /> },
  { path: "/build", element: <Build /> },
  { path: "/usinas", element: <Portfolio /> },
  {
    path: "/usinas/:id",
    element: <PlantShell />,
    children: [
      { index: true, element: <Resumo /> },
      { path: "financeiro", element: <Financeiro /> },
      { path: "bess", element: <Simulador /> },
      { path: "dossie", element: <Dossie /> },
      { path: "chat", element: <Chat /> },
    ],
  },
])

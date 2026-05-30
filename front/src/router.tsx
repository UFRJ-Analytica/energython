import { createBrowserRouter, Navigate } from "react-router-dom"
import { PlantShell } from "@/components/PlantShell"
import Portfolio from "@/pages/Portfolio"
import Resumo from "@/pages/Resumo"
import Financeiro from "@/pages/Financeiro"
import Simulador from "@/pages/Simulador"
import Dossie from "@/pages/Dossie"
import Chat from "@/pages/Chat"

export const router = createBrowserRouter([
  { path: "/", element: <Navigate to="/usinas" replace /> },
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

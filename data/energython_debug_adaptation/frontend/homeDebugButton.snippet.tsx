// Aplicar em front/src/pages/Home/index.tsx
// 1) Adicione useNavigate ao import de react-router-dom se ainda não existir:
// import { Link, useNavigate } from "react-router-dom"
//
// 2) Dentro do componente Home():
// const navigate = useNavigate()
// const openDebug = () => {
//   sessionStorage.setItem("energython.debugAccess", "true")
//   navigate("/debug")
// }
//
// 3) Ao lado do botão "Selecione a usina", adicione:

<Button
  size="lg"
  variant="outline"
  className="h-12 rounded-full border-white/20 bg-white/[0.04] px-6 text-sm font-semibold text-white transition hover:bg-white/10"
  onClick={openDebug}
>
  DEBUG
</Button>

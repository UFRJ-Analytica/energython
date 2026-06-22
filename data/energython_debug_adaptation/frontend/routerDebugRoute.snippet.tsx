// Aplicar em front/src/router.tsx
//
// 1) Adicionar o lazy import:
// const Debug = lazy(() => import("@/pages/Debug"))
//
// 2) Adicionar a rota no array createBrowserRouter:

{ path: "/debug", element: lazyPage(<Debug />) },

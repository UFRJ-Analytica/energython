# Diagrama de tarefas — Energython DEBUG

## Ordem macro

```mermaid
flowchart TD
    A[1. Congelar contrato atual] --> B[2. Mapear leitura atual do banco]
    B --> C[3. Mapear banco novo para aliases antigos]
    C --> D[4. Alterar somente SQL/aliases no PostgresRepository]
    D --> E[5. Criar endpoints DEBUG isolados]
    E --> F[6. Criar página DEBUG isolada]
    F --> G[7. Adicionar botão DEBUG na Home]
    G --> H[8. Proteger /debug via sessionStorage]
    H --> I[9. Rodar testes backend]
    I --> J[10. Rodar typecheck/build frontend]
    J --> K[11. Validar fluxo normal]
```

## Diagrama de camadas

```mermaid
flowchart LR
    subgraph DB[Banco/DW]
      DW1[dw.mart_eolica]
      DW2[dw.dim_usina]
      DW3[dw.fato_restricao_coff]
      DW4[PLD]
    end

    subgraph Repo[Repository]
      R1[PostgresRepository]
      R2[SQL com aliases do contrato atual]
    end

    subgraph Normal[Fluxo normal]
      S1[FinanceiroService]
      S2[RegulatorioService]
      S3[CurtailmentService]
    end

    subgraph Debug[Fluxo DEBUG isolado]
      DS[DebugService]
      DR[DebugRouter /api/debug]
    end

    subgraph Front[Frontend]
      H[Home]
      B[Botão DEBUG]
      P[/debug]
      U[Fluxo normal /usinas]
    end

    DB --> Repo
    R1 --> R2
    Repo --> Normal
    Repo --> Debug
    Normal --> U
    Debug --> P
    H --> B
    B --> P
    H --> U
```

## Proteção da rota DEBUG

```mermaid
flowchart TD
    A[Usuário na Home] --> B[Clica DEBUG]
    B --> C[sessionStorage.setItem debugAccess=true]
    C --> D[navigate /debug]
    D --> E[DebugPage verifica flag]
    E --> F[Renderiza diagnóstico]
    G[Usuário digita /debug direto] --> H[Sem flag]
    H --> I[Redirect para /]
```

## Ordem de implementação segura

1. Criar/copiar backend DEBUG, sem registrar router.
2. Rodar `python -m py_compile` nos novos arquivos.
3. Registrar router em `main.py`.
4. Testar `/api/debug/health-dados`.
5. Criar frontend DEBUG.
6. Adicionar rota `/debug`.
7. Adicionar botão DEBUG na Home.
8. Rodar `npm run typecheck` e `npm run build`.
9. Testar que `/usinas`, `/usinas/:id`, financeiro e dossiê continuam funcionando.

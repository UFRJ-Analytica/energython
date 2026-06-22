# Artefatos de modelos (CatBoost)

Pasta trazida do protótipo Streamlit para fazer parte do projeto Energython.

## Conteúdo

```text
data/models_artifacts/
└── catboost_info/        # logs/artefatos de treino do CatBoost (catboost_training.json etc.)
```

## O que é

`catboost_info/` é gerado automaticamente pelo CatBoost durante o treino do modelo
híbrido (Linear + CatBoost) do protótipo. Contém o histórico de iterações e métricas
internas de treinamento.

## Uso no Energython

- Referência para o forecast experimental da camada DEBUG (que hoje usa
  `LinearRegression + GradientBoostingRegressor` do scikit-learn, sem exigir CatBoost).
- Caso o projeto adote CatBoost no futuro, estes artefatos servem de baseline/registro.

## Observação

Não é necessário para rodar a aplicação atual; é material de modelo para análise e evolução.

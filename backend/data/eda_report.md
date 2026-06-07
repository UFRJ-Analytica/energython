# EDA Completa - ONS Data Lake

> Relatório gerado automaticamente | Total de datasets analisados: 13

## Sumário dos Datasets

| # | Dataset | Linhas | Colunas | Numéricas | Categóricas | Missing (max) |
|---|---------|--------|---------|-----------|-------------|---------------|
| 1 | ANEEL SIGA - Sistema de Informações de Geração | 50,523 | 23 | 6 | 21 | 94.2% |
| 2 | ONS Balanço DESSEM Geral | 960 | 8 | 6 | 2 | 0.0% |
| 3 | ONS Balanço DESSEM Detalhe | 960 | 12 | 10 | 2 | 0.0% |
| 4 | ONS Disponibilidade de Usina | 811,287 | 13 | 3 | 10 | 0.4% |
| 5 | ONS Fator de Capacidade | 148,830 | 21 | 8 | 13 | 15.5% |
| 6 | ONS Geração por Usina | 7,012,281 | 12 | 1 | 11 | 0.0% |
| 7 | ONS Restrição COFF Eólica Detalhamento | 5,318,304 | 12 | 4 | 8 | 5.3% |
| 8 | ONS Restrição COFF Eólica por Usina | 983,424 | 15 | 5 | 10 | 99.9% |
| 9 | ONS Restrição COFF Fotovoltaica | 432,720 | 15 | 5 | 10 | 98.8% |
| 10 | ONS Restrição COFF Fotovoltaica Detalhamento | 2,620,088 | 12 | 3 | 8 | 1.1% |
| 11 | ONS Taxa TEIF/TEIP | 29,732 | 8 | 2 | 6 | 4.0% |
| 12 | ONS Taxa TEIF/TEIP Operacional | 29,735 | 8 | 2 | 6 | 4.0% |
| 13 | ONS Dados Hidrológicos (Parquet) | 1,116,576 | 18 | 11 | 6 | 99.3% |

---
## ANEEL SIGA - Sistema de Informações de Geração

**Arquivos processados:** 2  
**Dimensões:** 50,523 linhas x 23 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `DatGeracaoConjuntoDados` | str | 0 | 0.0% |
| `NomEmpreendimento` | str | 0 | 0.0% |
| `IdeNucleoCEG` | int64 | 0 | 0.0% |
| `CodCEG` | str | 0 | 0.0% |
| `SigUFPrincipal` | str | 0 | 0.0% |
| `SigTipoGeracao` | str | 0 | 0.0% |
| `DscFaseUsina` | str | 0 | 0.0% |
| `DscOrigemCombustivel` | str | 0 | 0.0% |
| `DscFonteCombustivel` | str | 0 | 0.0% |
| `DscTipoOutorga` | str | 0 | 0.0% |
| `NomFonteCombustivel` | str | 0 | 0.0% |
| `DatEntradaOperacao` | str | 0 | 0.0% |
| `MdaPotenciaOutorgadaKw` | str | 0 | 0.0% |
| `MdaPotenciaFiscalizadaKw` | int64 | 0 | 0.0% |
| `MdaGarantiaFisicaKw` | str | 0 | 0.0% |
| `IdcGeracaoQualificada` | str | 31,914 | 63.2% |
| `NumCoordNEmpreendimento` | str | 0 | 0.0% |
| `NumCoordEEmpreendimento` | str | 0 | 0.0% |
| `DatInicioVigencia` | str | 39,270 | 77.7% |
| `DatFimVigencia` | str | 39,290 | 77.8% |
| `DscPropriRegimePariticipacao` | str | 0 | 0.0% |
| `DscSubBacia` | str | 47,610 | 94.2% |
| `DscMuninicpios` | str | 0 | 0.0% |

### Colunas Convertidas (formato BR -> numérico)

- `MdaPotenciaOutorgadaKw` → `MdaPotenciaOutorgadaKw_numeric`
- `MdaGarantiaFisicaKw` → `MdaGarantiaFisicaKw_numeric`
- `NumCoordNEmpreendimento` → `NumCoordNEmpreendimento_numeric`
- `NumCoordEEmpreendimento` → `NumCoordEEmpreendimento_numeric`

### Estatísticas Numéricas

| Estatística | `IdeNucleoCEG` | `MdaPotenciaFiscalizadaKw` | `MdaPotenciaOutorgadaKw_numeric` | `MdaGarantiaFisicaKw_numeric` | `NumCoordNEmpreendimento_numeric` | `NumCoordEEmpreendimento_numeric` |
|-------------|---|---|---|---|---|---|
| count | 50,523.0 | 50,523.0 | 50,523.0 | 50,523.0 | 50,523.0 | 50,523.0 |
| mean | 51,611.5 | 8,648.0 | 13,032.7 | 4,077.5 | -8.6097 | -49.0360 |
| std | 15,736.1 | 122,321.7 | 123,728.6 | 75,085.6 | 8.5975 | 7.9108 |
| min | 8.0000 | 0.0000 | 0.0100 | 0.0000 | -33.7228 | -72.8111 |
| 25% | 38,924.5 | 1.0000 | 1.0000 | 0.0000 | -17.6536 | -52.4267 |
| 50% | 57,430.0 | 1.0000 | 1.0000 | 0.0000 | -3.4953 | -50.5872 |
| 75% | 64,496.5 | 100.0000 | 1,625.0 | 0.0000 | -1.9549 | -47.9514 |
| max | 76,517.0 | 11,233,100.0 | 11,233,100.0 | 7,750,800.0 | 4.8894 | 0.0000 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `MdaPotenciaFiscalizadaKw` | `MdaPotenciaOutorgadaKw_numeric` | 0.9862 🔴 |
| `MdaPotenciaFiscalizadaKw` | `MdaGarantiaFisicaKw_numeric` | 0.9033 🔴 |
| `MdaPotenciaOutorgadaKw_numeric` | `MdaGarantiaFisicaKw_numeric` | 0.9030 🔴 |
| `IdeNucleoCEG` | `NumCoordNEmpreendimento_numeric` | 0.3578 🟢 |
| `IdeNucleoCEG` | `MdaPotenciaFiscalizadaKw` | -0.1266 🟢 |
| `IdeNucleoCEG` | `MdaPotenciaOutorgadaKw_numeric` | -0.1243 🟢 |
| `NumCoordNEmpreendimento_numeric` | `NumCoordEEmpreendimento_numeric` | 0.1105 🟢 |
| `IdeNucleoCEG` | `MdaGarantiaFisicaKw_numeric` | -0.1023 🟢 |
| `MdaPotenciaOutorgadaKw_numeric` | `NumCoordNEmpreendimento_numeric` | -0.0599 🟢 |
| `IdeNucleoCEG` | `NumCoordEEmpreendimento_numeric` | -0.0567 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `MdaPotenciaFiscalizadaKw` | 11,595 | 22.9% |
| `MdaPotenciaOutorgadaKw_numeric` | 11,193 | 22.1% |
| `NumCoordEEmpreendimento_numeric` | 6,109 | 12.1% |
| `IdeNucleoCEG` | 168 | 0.3% |

### Cobertura Temporal

- **`DatGeracaoConjuntoDados`**: 2026-05-19 00:00:00 → 2026-05-27 00:00:00 (8 dias)
- **`DatEntradaOperacao`**: 1900-01-03 00:00:00 → 2026-05-25 00:00:00 (46163 dias)
- **`DatInicioVigencia`**: 1970-07-17 00:00:00 → 2026-12-20 00:00:00 (20610 dias)
- **`DatFimVigencia`**: 1998-09-15 00:00:00 → 2063-01-14 00:00:00 (23497 dias)

### Variáveis Categóricas

- **`DatGeracaoConjuntoDados`**: 2 valores únicos
  - Top: "2026-05-19" (25,267), "2026-05-27" (25,256)
- **`NomEmpreendimento`**: 24974 valores únicos
- **`CodCEG`**: 25273 valores únicos
- **`SigUFPrincipal`**: 27 valores únicos
  - Top: "PA" (26,404), "MS" (6,040), "MG" (2,771)
- **`SigTipoGeracao`**: 7 valores únicos
  - Top: "UFV" (38,208), "UTE" (6,227), "EOL" (3,124)
- **`DscFaseUsina`**: 3 valores únicos
  - Top: "Operação" (45,458), "Construção não iniciada" (4,747), "Construção" (318)
- **`DscOrigemCombustivel`**: 6 valores únicos
  - Top: "Solar" (38,208), "Fóssil" (4,838), "Eólica" (3,124)
- **`DscFonteCombustivel`**: 13 valores únicos
  - Top: "Radiação solar" (38,208), "Petróleo" (4,402), "Cinética do vento" (3,124)
- **`DscTipoOutorga`**: 3 valores únicos
  - Top: "Registro" (39,268), "Autorização" (10,735), "Concessão" (520)
- **`NomFonteCombustivel`**: 31 valores únicos
  - Top: "Radiação solar" (38,208), "Óleo Diesel" (4,272), "Cinética do vento" (3,124)

### Colunas com Alta Proporção de Zeros (>50%)

- `MdaGarantiaFisicaKw_numeric`: 88.9% zeros

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `IdeNucleoCEG` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |
| `NumCoordNEmpreendimento_numeric` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |
| `NumCoordEEmpreendimento_numeric` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `MdaPotenciaFiscalizadaKw` | ⭐⭐⭐⭐☆ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Muitos outliers (22.95%) |
| `MdaPotenciaOutorgadaKw_numeric` | ⭐⭐⭐⭐☆ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Muitos outliers (22.15%) |
| `MdaGarantiaFisicaKw_numeric` | ⭐⭐⭐☆☆ | Tem variância significativa; Poucos missings (0%); Alta proporção de zeros (88.92%); Alta correlação com 2 feature(s) |

---
## ONS Balanço DESSEM Geral

**Arquivos processados:** 5  
**Dimensões:** 960 linhas x 8 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `din_programacaodia` | str | 0 | 0.0% |
| `num_patamar` | int64 | 0 | 0.0% |
| `cod_subsistema` | str | 0 | 0.0% |
| `val_demanda` | float64 | 0 | 0.0% |
| `val_geracao_renovavel` | float64 | 0 | 0.0% |
| `val_geracao_hidraulica` | float64 | 0 | 0.0% |
| `val_geracao_termica` | float64 | 0 | 0.0% |
| `val_cons_elevatoria` | float64 | 0 | 0.0% |

### Estatísticas Numéricas

| Estatística | `num_patamar` | `val_demanda` | `val_geracao_renovavel` | `val_geracao_hidraulica` | `val_geracao_termica` | `val_cons_elevatoria` |
|-------------|---|---|---|---|---|---|
| count | 960.0000 | 960.0000 | 960.0000 | 960.0000 | 960.0000 | 960.0000 |
| mean | 24.5000 | 18,947.3 | 7,634.7 | 10,741.3 | 1,114.6 | 18.8372 |
| std | 13.8606 | 13,834.5 | 7,507.4 | 10,479.4 | 1,089.5 | 38.6528 |
| min | 1.0000 | 6,938.7 | 321.0000 | 1,164.5 | 3.5000 | 0.0000 |
| 25% | 12.7500 | 8,922.9 | 1,370.0 | 2,178.4 | 250.0000 | 0.0000 |
| 50% | 24.5000 | 12,926.8 | 5,215.5 | 5,857.0 | 679.0000 | 0.0000 |
| 75% | 36.2500 | 20,789.1 | 15,600.2 | 15,811.3 | 2,245.8 | 5.8075 |
| max | 48.0000 | 51,867.8 | 24,071.2 | 41,500.7 | 3,088.0 | 114.8300 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_geracao_hidraulica` | `val_geracao_termica` | 0.8973 🟡 |
| `val_demanda` | `val_geracao_hidraulica` | 0.8545 🟡 |
| `val_demanda` | `val_geracao_termica` | 0.7914 🟡 |
| `val_demanda` | `val_cons_elevatoria` | 0.7655 🟡 |
| `val_geracao_termica` | `val_cons_elevatoria` | 0.7041 🟡 |
| `val_geracao_hidraulica` | `val_cons_elevatoria` | 0.6118 🟢 |
| `val_geracao_renovavel` | `val_cons_elevatoria` | 0.3051 🟢 |
| `val_demanda` | `val_geracao_renovavel` | 0.2968 🟢 |
| `num_patamar` | `val_cons_elevatoria` | -0.1617 🟢 |
| `num_patamar` | `val_geracao_hidraulica` | 0.1412 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_cons_elevatoria` | 240 | 25.0% |
| `val_demanda` | 162 | 16.9% |
| `val_geracao_hidraulica` | 35 | 3.6% |

### Cobertura Temporal

- **`din_programacaodia`**: 2025-05-23 00:00:00 → 2025-05-27 00:00:00 (4 dias)

### Variáveis Categóricas

- **`din_programacaodia`**: 5 valores únicos
  - Top: "2025-05-23" (192), "2025-05-24" (192), "2025-05-25" (192)
- **`cod_subsistema`**: 4 valores únicos
  - Top: "N" (240), "NE" (240), "S" (240)

### Colunas com Alta Proporção de Zeros (>50%)

- `val_cons_elevatoria`: 75.0% zeros

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `num_patamar` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |
| `val_demanda` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s); Outliers moderados - variação informativa |
| `val_geracao_renovavel` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |
| `val_geracao_hidraulica` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa |
| `val_geracao_termica` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s) |
| `val_cons_elevatoria` | ⭐⭐⭐☆☆ | Tem variância significativa; Poucos missings (0%); Muitos outliers (25.0%) |

---
## ONS Balanço DESSEM Detalhe

**Arquivos processados:** 5  
**Dimensões:** 960 linhas x 12 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `din_programacaodia` | str | 0 | 0.0% |
| `num_patamar` | int64 | 0 | 0.0% |
| `cod_subsistema` | str | 0 | 0.0% |
| `val_demanda` | float64 | 0 | 0.0% |
| `val_ger_hidraulica` | float64 | 0 | 0.0% |
| `val_ger_pch` | float64 | 0 | 0.0% |
| `val_ger_termica` | float64 | 0 | 0.0% |
| `val_ger_pct` | float64 | 0 | 0.0% |
| `val_ger_eolica` | float64 | 0 | 0.0% |
| `val_ger_fotovoltaica` | float64 | 0 | 0.0% |
| `val_ger_mmgd` | float64 | 0 | 0.0% |
| `val_cons_elevatoria` | float64 | 0 | 0.0% |

### Estatísticas Numéricas

| Estatística | `num_patamar` | `val_demanda` | `val_ger_hidraulica` | `val_ger_pch` | `val_ger_termica` | `val_ger_pct` | `val_ger_eolica` | `val_ger_fotovoltaica` | `val_ger_mmgd` | `val_cons_elevatoria` |
|-------------|---|---|---|---|---|---|---|---|---|---|
| count | 960.0000 | 960.0000 | 960.0000 | 960.0000 | 960.0000 | 960.0000 | 960.0000 | 960.0000 | 960.0000 | 960.0000 |
| mean | 24.5000 | 18,947.3 | 10,741.3 | 677.6380 | 1,114.6 | 945.4698 | 3,611.7 | 978.0768 | 1,421.8 | 18.8372 |
| std | 13.8606 | 13,834.5 | 10,479.4 | 865.9530 | 1,089.5 | 1,283.3 | 6,204.8 | 1,962.1 | 2,531.0 | 38.6528 |
| min | 1.0000 | 6,938.7 | 1,164.5 | 52.0000 | 3.5000 | 163.0000 | 3.0000 | 0.0000 | 0.0000 | 0.0000 |
| 25% | 12.7500 | 8,922.9 | 2,178.4 | 69.7500 | 250.0000 | 199.0000 | 31.7050 | 0.0000 | 0.0000 | 0.0000 |
| 50% | 24.5000 | 12,926.8 | 5,857.0 | 250.0000 | 679.0000 | 220.0000 | 229.0000 | 0.0000 | 11.5000 | 0.0000 |
| 75% | 36.2500 | 20,789.1 | 15,811.3 | 801.7500 | 2,245.8 | 944.0000 | 1,616.2 | 42.0000 | 1,842.2 | 5.8075 |
| max | 48.0000 | 51,867.8 | 41,500.7 | 2,221.0 | 3,088.0 | 3,330.0 | 19,911.0 | 6,620.0 | 11,581.0 | 114.8300 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_ger_pch` | `val_ger_pct` | 0.9863 🔴 |
| `val_demanda` | `val_ger_pct` | 0.9677 🔴 |
| `val_demanda` | `val_ger_pch` | 0.9663 🔴 |
| `val_ger_hidraulica` | `val_ger_termica` | 0.8973 🟡 |
| `val_ger_hidraulica` | `val_ger_pct` | 0.8797 🟡 |
| `val_ger_termica` | `val_ger_pct` | 0.8578 🟡 |
| `val_demanda` | `val_ger_hidraulica` | 0.8545 🟡 |
| `val_ger_pct` | `val_cons_elevatoria` | 0.8429 🟡 |
| `val_ger_hidraulica` | `val_ger_pch` | 0.8369 🟡 |
| `val_ger_pch` | `val_cons_elevatoria` | 0.8298 🟡 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_ger_pch` | 240 | 25.0% |
| `val_ger_pct` | 240 | 25.0% |
| `val_cons_elevatoria` | 240 | 25.0% |
| `val_ger_eolica` | 229 | 23.9% |
| `val_ger_fotovoltaica` | 225 | 23.4% |
| `val_demanda` | 162 | 16.9% |
| `val_ger_mmgd` | 75 | 7.8% |
| `val_ger_hidraulica` | 35 | 3.6% |

### Cobertura Temporal

- **`din_programacaodia`**: 2025-05-23 00:00:00 → 2025-05-27 00:00:00 (4 dias)

### Variáveis Categóricas

- **`din_programacaodia`**: 5 valores únicos
  - Top: "2025-05-23" (192), "2025-05-24" (192), "2025-05-25" (192)
- **`cod_subsistema`**: 4 valores únicos
  - Top: "N" (240), "NE" (240), "S" (240)

### Colunas com Alta Proporção de Zeros (>50%)

- `val_cons_elevatoria`: 75.0% zeros
- `val_ger_fotovoltaica`: 58.0% zeros

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `num_patamar` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |
| `val_demanda` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa |
| `val_ger_hidraulica` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 4 feature(s); Outliers moderados - variação informativa |
| `val_ger_termica` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s) |
| `val_ger_mmgd` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Alta correlação com 1 feature(s); Outliers moderados - variação informativa |
| `val_ger_pch` | ⭐⭐⭐⭐☆ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 5 feature(s); Muitos outliers (25.0%) |
| `val_ger_pct` | ⭐⭐⭐⭐☆ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 5 feature(s); Muitos outliers (25.0%) |
| `val_ger_eolica` | ⭐⭐⭐⭐☆ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Muitos outliers (23.85%) |
| `val_ger_fotovoltaica` | ⭐⭐⭐☆☆ | Tem variância significativa; Poucos missings (0%); Alta correlação com 1 feature(s); Muitos outliers (23.44%) |
| `val_cons_elevatoria` | ⭐⭐⭐☆☆ | Tem variância significativa; Poucos missings (0%); Alta correlação com 2 feature(s); Muitos outliers (25.0%) |

---
## ONS Disponibilidade de Usina

**Arquivos processados:** 5  
**Dimensões:** 811,287 linhas x 13 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `id_subsistema` | str | 0 | 0.0% |
| `nom_subsistema` | str | 0 | 0.0% |
| `id_estado` | str | 0 | 0.0% |
| `nom_estado` | str | 3,599 | 0.4% |
| `nom_usina` | str | 0 | 0.0% |
| `id_tipousina` | str | 0 | 0.0% |
| `nom_tipocombustivel` | str | 0 | 0.0% |
| `id_ons` | str | 0 | 0.0% |
| `ceg` | str | 0 | 0.0% |
| `din_instante` | str | 0 | 0.0% |
| `val_potenciainstalada` | float64 | 0 | 0.0% |
| `val_dispoperacional` | float64 | 0 | 0.0% |
| `val_dispsincronizada` | float64 | 0 | 0.0% |

### Estatísticas Numéricas

| Estatística | `val_potenciainstalada` | `val_dispoperacional` | `val_dispsincronizada` |
|-------------|---|---|---|
| count | 811,287.0 | 811,287.0 | 811,287.0 |
| mean | 488.1346 | 400.9323 | 310.2402 |
| std | 975.8284 | 837.1323 | 740.7890 |
| min | 0.0000 | 0.0000 | 0.0000 |
| 25% | 90.0000 | 73.8000 | 38.5000 |
| 50% | 189.0000 | 156.4507 | 106.3000 |
| 75% | 443.0000 | 373.3300 | 265.5000 |
| max | 8,535.0 | 8,185.0 | 8,185.0 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_potenciainstalada` | `val_dispoperacional` | 0.9819 🔴 |
| `val_dispoperacional` | `val_dispsincronizada` | 0.9635 🔴 |
| `val_potenciainstalada` | `val_dispsincronizada` | 0.9404 🔴 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_potenciainstalada` | 107,970 | 13.3% |
| `val_dispoperacional` | 106,358 | 13.1% |
| `val_dispsincronizada` | 100,776 | 12.4% |

### Cobertura Temporal

- **`din_instante`**: 2015-01-01 01:00:00 → 2015-05-31 23:00:00 (150 dias)

### Variáveis Categóricas

- **`id_subsistema`**: 4 valores únicos
  - Top: "SE" (449,899), "NE" (172,752), "S" (143,960)
- **`nom_subsistema`**: 4 valores únicos
  - Top: "Sudeste/Centro-Oeste" (449,899), "Nordeste" (172,752), "Sul" (143,960)
- **`id_estado`**: 25 valores únicos
  - Top: "MG" (125,965), "SP" (118,767), "RS" (68,381)
- **`nom_estado`**: 24 valores únicos
  - Top: "Minas Gerais" (125,965), "São Paulo" (118,767), "Rio Grande do Sul" (68,381)
- **`nom_usina`**: 243 valores únicos
  - Top: "Santa Clara" (4,368), "Funil" (4,368), "Campos" (3,623)
- **`id_tipousina`**: 3 valores únicos
  - Top: "UHE" (508,203), "UTE" (295,886), "UTN" (7,198)
- **`nom_tipocombustivel`**: 7 valores únicos
  - Top: "Hidráulica" (508,203), "Gás" (105,139), "Óleo Diesel" (79,178)
- **`id_ons`**: 227 valores únicos
  - Top: "RJUSCP" (3,623), "APFGO" (3,599), "APSAJ" (3,599)
- **`ceg`**: 225 valores únicos
  - Top: "UHE.PH.PR.001161-4.01" (7,198), "UHE.PH.SP.001084-7.01" (7,198), "UTE.GN.RJ.027935-8.01" (3,623)
- **`din_instante`**: 3623 valores únicos

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_potenciainstalada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa |
| `val_dispoperacional` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa |
| `val_dispsincronizada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa |

---
## ONS Fator de Capacidade

**Arquivos processados:** 5  
**Dimensões:** 148,830 linhas x 21 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `id_subsistema` | str | 0 | 0.0% |
| `nom_subsistema` | str | 0 | 0.0% |
| `id_estado` | str | 0 | 0.0% |
| `nom_estado` | str | 0 | 0.0% |
| `cod_pontoconexao` | str | 0 | 0.0% |
| `nom_pontoconexao` | str | 0 | 0.0% |
| `nom_localizacao` | str | 23,133 | 15.5% |
| `val_latitudesecoletora` | float64 | 0 | 0.0% |
| `val_longitudesecoletora` | float64 | 0 | 0.0% |
| `val_latitudepontoconexao` | float64 | 0 | 0.0% |
| `val_longitudepontoconexao` | float64 | 0 | 0.0% |
| `nom_modalidadeoperacao` | str | 0 | 0.0% |
| `nom_tipousina` | str | 0 | 0.0% |
| `nom_usina_conjunto` | str | 0 | 0.0% |
| `id_ons` | str | 0 | 0.0% |
| `ceg` | str | 0 | 0.0% |
| `din_instante` | str | 0 | 0.0% |
| `val_geracaoprogramada` | float64 | 0 | 0.0% |
| `val_geracaoverificada` | float64 | 0 | 0.0% |
| `val_capacidadeinstalada` | float64 | 0 | 0.0% |
| `val_fatorcapacidade` | float64 | 0 | 0.0% |

### Estatísticas Numéricas

| Estatística | `val_latitudesecoletora` | `val_longitudesecoletora` | `val_latitudepontoconexao` | `val_longitudepontoconexao` | `val_geracaoprogramada` | `val_geracaoverificada` | `val_capacidadeinstalada` | `val_fatorcapacidade` |
|-------------|---|---|---|---|---|---|---|---|
| count | 148,830.0 | 148,830.0 | 148,830.0 | 148,830.0 | 148,830.0 | 148,830.0 | 148,830.0 | 148,830.0 |
| mean | -7.8821 | -40.5896 | -8.3856 | -40.7478 | 19.4347 | 24.1258 | 73.6244 | 0.3377 |
| std | 9.5706 | 4.5089 | 9.2667 | 4.3757 | 20.3341 | 22.7265 | 22.5876 | 0.2946 |
| min | -30.0791 | -50.1721 | -29.8950 | -50.3139 | 0.0000 | 0.0000 | 31.3500 | 0.0000 |
| 25% | -5.1153 | -41.0316 | -5.5930 | -40.3005 | 4.0000 | 5.6302 | 54.6000 | 0.0781 |
| 50% | -3.0192 | -39.6787 | -3.6904 | -40.3005 | 13.0000 | 17.9455 | 68.4700 | 0.2536 |
| 75% | -2.9194 | -36.4025 | -3.6904 | -36.9086 | 30.0000 | 37.5665 | 105.0000 | 0.5728 |
| max | -2.9194 | -36.1632 | -3.6904 | -36.9086 | 368.5000 | 102.6900 | 105.0000 | 1.0071 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_latitudesecoletora` | `val_latitudepontoconexao` | 1.0000 🔴 |
| `val_longitudesecoletora` | `val_longitudepontoconexao` | 0.9926 🔴 |
| `val_geracaoverificada` | `val_fatorcapacidade` | 0.9029 🔴 |
| `val_latitudepontoconexao` | `val_longitudepontoconexao` | 0.9020 🔴 |
| `val_latitudesecoletora` | `val_longitudepontoconexao` | 0.8984 🟡 |
| `val_longitudesecoletora` | `val_latitudepontoconexao` | 0.8714 🟡 |
| `val_latitudesecoletora` | `val_longitudesecoletora` | 0.8670 🟡 |
| `val_geracaoprogramada` | `val_geracaoverificada` | 0.6301 🟢 |
| `val_geracaoprogramada` | `val_fatorcapacidade` | 0.5092 🟢 |
| `val_geracaoprogramada` | `val_capacidadeinstalada` | 0.3135 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_latitudesecoletora` | 23,133 | 15.5% |
| `val_longitudesecoletora` | 23,133 | 15.5% |
| `val_latitudepontoconexao` | 23,133 | 15.5% |
| `val_longitudepontoconexao` | 23,133 | 15.5% |
| `val_geracaoprogramada` | 5,247 | 3.5% |
| `val_geracaoverificada` | 3,924 | 2.6% |

### Cobertura Temporal

- **`din_instante`**: 2009-07-01 00:00:00 → 2013-12-31 23:00:00 (1644 dias)

### Variáveis Categóricas

- **`id_subsistema`**: 2 valores únicos
  - Top: "NE" (125,697), "S" (23,133)
- **`nom_subsistema`**: 2 valores únicos
  - Top: "Nordeste" (125,697), "Sul" (23,133)
- **`id_estado`**: 3 valores únicos
  - Top: "CE" (77,030), "RN" (48,667), "RS" (23,133)
- **`nom_estado`**: 3 valores únicos
  - Top: "CEARA" (77,030), "RIO GRANDE DO NORTE" (48,667), "RIO GRANDE DO SUL" (23,133)
- **`cod_pontoconexao`**: 3 valores únicos
  - Top: "CESBT-230-A" (77,030), "RNACD-230" (48,667), "RSOSO269" (23,133)
- **`nom_pontoconexao`**: 3 valores únicos
  - Top: "SOBRAL III - 230 kV (A)" (77,030), "ACU II - 230 kV (A)" (48,667), "OSORIO 2 - 69 kV (A)" (23,133)
- **`nom_localizacao`**: 1 valores únicos
  - Top: "Litoral" (125,697)
- **`nom_modalidadeoperacao`**: 2 valores únicos
  - Top: "Tipo I" (125,697), "Tipo II-B" (23,133)
- **`nom_tipousina`**: 1 valores únicos
  - Top: "Eólica" (148,830)
- **`nom_usina_conjunto`**: 8 valores únicos
  - Top: "Praia Formosa" (39,451), "Icaraizinho" (37,579), "Alegria I" (26,181)

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_latitudesecoletora` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa |
| `val_longitudesecoletora` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa |
| `val_latitudepontoconexao` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa |
| `val_longitudepontoconexao` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa |
| `val_geracaoprogramada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `val_geracaoverificada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s); Outliers moderados - variação informativa |
| `val_capacidadeinstalada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |
| `val_fatorcapacidade` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s) |

---
## ONS Geração por Usina

**Arquivos processados:** 5  
**Dimensões:** 7,012,281 linhas x 12 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `din_instante` | str | 0 | 0.0% |
| `id_subsistema` | str | 0 | 0.0% |
| `nom_subsistema` | str | 0 | 0.0% |
| `id_estado` | str | 0 | 0.0% |
| `nom_estado` | str | 0 | 0.0% |
| `cod_modalidadeoperacao` | str | 24 | 0.0% |
| `nom_tipousina` | str | 0 | 0.0% |
| `nom_tipocombustivel` | str | 0 | 0.0% |
| `nom_usina` | str | 0 | 0.0% |
| `id_ons` | str | 0 | 0.0% |
| `ceg` | str | 0 | 0.0% |
| `val_geracao` | float64 | 72 | 0.0% |

### Estatísticas Numéricas

| Estatística | `val_geracao` |
|-------------|---|
| count | 7,012,209.0 |
| mean | 253.8671 |
| std | 649.5423 |
| min | 0.0000 |
| 25% | 0.0000 |
| 50% | 49.0000 |
| 75% | 195.7000 |
| max | 6,352.5 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_geracao` | 881,708 | 12.6% |

### Cobertura Temporal

- **`din_instante`**: 2000-01-01 00:00:00 → 2004-12-31 23:00:00 (1826 dias)

### Variáveis Categóricas

- **`din_instante`**: 43843 valores únicos
- **`id_subsistema`**: 4 valores únicos
  - Top: "SE" (4,069,156), "NE" (1,622,247), "S" (1,238,664)
- **`nom_subsistema`**: 5 valores únicos
  - Top: "SUDESTE" (4,025,313), "NORDESTE" (1,622,247), "SUL" (1,238,664)
- **`id_estado`**: 22 valores únicos
  - Top: "SP" (1,485,788), "MG" (1,063,533), "RS" (613,680)
- **`nom_estado`**: 22 valores únicos
  - Top: "SAO PAULO" (1,485,788), "MINAS GERAIS" (1,063,533), "RIO GRANDE DO SUL" (613,680)
- **`cod_modalidadeoperacao`**: 4 valores únicos
  - Top: "TIPO I" (5,726,397), "Pequenas Usinas (Tipo III)" (679,459), "TIPO II-A" (404,180)
- **`nom_tipousina`**: 3 valores únicos
  - Top: "HIDROELÉTRICA" (4,482,346), "TÉRMICA" (2,448,105), "NUCLEAR" (81,830)
- **`nom_tipocombustivel`**: 7 valores únicos
  - Top: "Hidráulica" (4,482,346), "Óleo Diesel" (1,049,980), "Gás" (659,687)
- **`nom_usina`**: 214 valores únicos
  - Top: "Willian Arjona" (67,984), "Tucuruí" (43,843), "Xingó" (43,843)
- **`id_ons`**: 215 valores únicos
  - Top: "PATU" (43,843), "ALUXG" (43,843), "PQU_PHCHF" (43,843)

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_geracao` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0.0%); Distribuição não-esparsa; Outliers moderados - variação informativa |

---
## ONS Restrição COFF Eólica Detalhamento

**Arquivos processados:** 5  
**Dimensões:** 5,318,304 linhas x 12 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `id_subsistema` | str | 0 | 0.0% |
| `id_estado` | str | 0 | 0.0% |
| `nom_modalidadeoperacao` | str | 0 | 0.0% |
| `nom_conjuntousina` | str | 79,728 | 1.5% |
| `nom_usina` | str | 0 | 0.0% |
| `id_ons` | str | 0 | 0.0% |
| `ceg` | str | 0 | 0.0% |
| `din_instante` | str | 0 | 0.0% |
| `val_ventoverificado` | float64 | 3,312 | 0.1% |
| `flg_dadoventoinvalido` | float64 | 3,312 | 0.1% |
| `val_geracaoestimada` | float64 | 283,673 | 5.3% |
| `val_geracaoverificada` | float64 | 3,312 | 0.1% |

### Estatísticas Numéricas

| Estatística | `val_ventoverificado` | `flg_dadoventoinvalido` | `val_geracaoestimada` | `val_geracaoverificada` |
|-------------|---|---|---|---|
| count | 5,314,992.0 | 5,314,992.0 | 5,034,631.0 | 5,314,992.0 |
| mean | 6.3508 | 0.4513 | 6.8934 | 10.2321 |
| std | 5.4958 | 0.4976 | 9.2694 | 9.9167 |
| min | -1.2300 | 0.0000 | -0.3320 | 0.0000 |
| 25% | 3.8000 | 0.0000 | 0.0000 | 2.4640 |
| 50% | 6.5260 | 0.0000 | 2.1270 | 7.7880 |
| 75% | 8.7500 | 1.0000 | 11.7450 | 15.8810 |
| max | 637.5570 | 1.0000 | 93.4460 | 5,350.4 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_geracaoestimada` | `val_geracaoverificada` | 0.6296 🟢 |
| `flg_dadoventoinvalido` | `val_geracaoestimada` | -0.5827 🟢 |
| `val_ventoverificado` | `val_geracaoestimada` | 0.3589 🟢 |
| `val_ventoverificado` | `val_geracaoverificada` | 0.2817 🟢 |
| `val_ventoverificado` | `flg_dadoventoinvalido` | -0.2276 🟢 |
| `flg_dadoventoinvalido` | `val_geracaoverificada` | -0.1683 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_geracaoestimada` | 113,562 | 2.1% |
| `val_geracaoverificada` | 85,436 | 1.6% |
| `val_ventoverificado` | 39,599 | 0.7% |

### Cobertura Temporal

- **`din_instante`**: 2021-10-01 00:00:00 → 2022-02-28 23:30:00 (150 dias)

### Variáveis Categóricas

- **`id_subsistema`**: 3 valores únicos
  - Top: "NE" (4,586,256), "S" (623,328), "N" (108,720)
- **`id_estado`**: 9 valores únicos
  - Top: "BA" (1,592,880), "RN" (1,500,336), "CE" (623,328)
- **`nom_modalidadeoperacao`**: 3 valores únicos
  - Top: "Tipo II-C" (5,238,576), "Tipo I" (50,736), "Tipo II-B" (28,992)
- **`nom_conjuntousina`**: 118 valores únicos
  - Top: "Conj. Santa Vitória do Palmar" (202,944), "Conj. Lagoa dos Ventos" (152,208), "Conj. Umburanas" (130,464)
- **`nom_usina`**: 736 valores únicos
  - Top: "Delta 3 I" (7,248), "Delta 3 II" (7,248), "Delta 3 III" (7,248)
- **`id_ons`**: 736 valores únicos
  - Top: "MAEDT1" (7,248), "MAEDT2" (7,248), "MAEDT3" (7,248)
- **`ceg`**: 736 valores únicos
  - Top: "EOL.CV.MA.033682-3.01" (7,248), "EOL.CV.MA.033683-1.01" (7,248), "EOL.CV.MA.033684-0.01" (7,248)
- **`din_instante`**: 7248 valores únicos

### Colunas com Alta Proporção de Zeros (>50%)

- `flg_dadoventoinvalido`: 54.8% zeros

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_ventoverificado` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0.06%); Distribuição não-esparsa |
| `val_geracaoverificada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0.06%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `flg_dadoventoinvalido` | ⭐⭐⭐⭐☆ | Tem variância significativa; Poucos missings (0.06%) |
| `val_geracaoestimada` | ⭐⭐⭐⭐☆ | Tem variância significativa; Missings moderados (5.33%); Outliers moderados - variação informativa |

---
## ONS Restrição COFF Eólica por Usina

**Arquivos processados:** 5  
**Dimensões:** 983,424 linhas x 15 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `id_subsistema` | str | 0 | 0.0% |
| `nom_subsistema` | str | 0 | 0.0% |
| `id_estado` | str | 0 | 0.0% |
| `nom_estado` | str | 0 | 0.0% |
| `nom_usina` | str | 0 | 0.0% |
| `id_ons` | str | 0 | 0.0% |
| `ceg` | str | 0 | 0.0% |
| `din_instante` | str | 0 | 0.0% |
| `val_geracao` | float64 | 0 | 0.0% |
| `val_geracaolimitada` | float64 | 965,735 | 98.2% |
| `val_disponibilidade` | float64 | 0 | 0.0% |
| `val_geracaoreferencia` | float64 | 34,660 | 3.5% |
| `val_geracaoreferenciafinal` | float64 | 982,010 | 99.9% |
| `cod_razaorestricao` | str | 965,735 | 98.2% |
| `cod_origemrestricao` | str | 970,691 | 98.7% |

### Estatísticas Numéricas

| Estatística | `val_geracao` | `val_geracaolimitada` | `val_disponibilidade` | `val_geracaoreferencia` | `val_geracaoreferenciafinal` |
|-------------|---|---|---|---|---|
| count | 983,424.0 | 17,689.0 | 983,424.0 | 948,764.0 | 1,414.0 |
| mean | 55.1713 | 37.4501 | -879,811.3 | 36.3811 | 37.2025 |
| std | 63.1934 | 52.2224 | 43,458,015.7 | 52.2916 | 53.8683 |
| min | 0.0000 | 0.0000 | -2,147,219,947.0 | -0.4750 | 0.0000 |
| 25% | 12.4000 | 0.0000 | 31.1850 | 0.7440 | 0.0000 |
| 50% | 35.1470 | 18.0000 | 84.0000 | 16.0030 | 9.3210 |
| 75% | 74.8270 | 53.0000 | 156.4070 | 49.5840 | 52.5580 |
| max | 5,378.3 | 338.8240 | 582.7900 | 424.3170 | 256.5000 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_geracao` | `val_geracaolimitada` | 0.9026 🔴 |
| `val_geracao` | `val_geracaoreferencia` | 0.7857 🟡 |
| `val_geracaolimitada` | `val_disponibilidade` | 0.7711 🟡 |
| `val_geracaolimitada` | `val_geracaoreferencia` | 0.7264 🟡 |
| `val_geracaoreferencia` | `val_geracaoreferenciafinal` | 0.7187 🟡 |
| `val_disponibilidade` | `val_geracaoreferencia` | 0.5193 🟢 |
| `val_geracao` | `val_geracaoreferenciafinal` | 0.5155 🟢 |
| `val_disponibilidade` | `val_geracaoreferenciafinal` | 0.5052 🟢 |
| `val_geracaolimitada` | `val_geracaoreferenciafinal` | 0.4686 🟢 |
| `val_geracao` | `val_disponibilidade` | 0.0177 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_geracaoreferencia` | 69,702 | 7.1% |
| `val_geracao` | 62,282 | 6.3% |
| `val_disponibilidade` | 15,266 | 1.6% |
| `val_geracaolimitada` | 1,193 | 0.1% |
| `val_geracaoreferenciafinal` | 129 | 0.0% |

### Cobertura Temporal

- **`din_instante`**: 2021-10-01 00:00:00 → 2022-02-28 23:30:00 (150 dias)

### Variáveis Categóricas

- **`id_subsistema`**: 3 valores únicos
  - Top: "NE" (889,200), "S" (86,976), "N" (7,248)
- **`nom_subsistema`**: 3 valores únicos
  - Top: "NORDESTE" (889,200), "SUL" (86,976), "NORTE" (7,248)
- **`id_estado`**: 9 valores únicos
  - Top: "RN" (333,408), "BA" (286,896), "CE" (137,712)
- **`nom_estado`**: 9 valores únicos
  - Top: "RIO GRANDE DO NORTE" (333,408), "BAHIA" (286,896), "CEARA" (137,712)
- **`nom_usina`**: 137 valores únicos
  - Top: "CONJ. PAULINO NEVES" (7,248), "CONJ. ABIL I" (7,248), "CONJ. ALVORADA" (7,248)
- **`id_ons`**: 137 valores únicos
  - Top: "CJU_MAPLN" (7,248), "CJU_BAABL" (7,248), "CJU_BAALV" (7,248)
- **`ceg`**: 12 valores únicos
  - Top: "-" (903,696), "EOL.CV.CE.033756-0.01" (7,248), "EOL.CV.CE.028699-0.01" (7,248)
- **`din_instante`**: 7248 valores únicos
- **`cod_razaorestricao`**: 3 valores únicos
  - Top: "CNF" (7,310), "REL" (6,535), "ENE" (3,844)
- **`cod_origemrestricao`**: 2 valores únicos
  - Top: "SIS" (11,702), "LOC" (1,031)

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_geracao` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s); Outliers moderados - variação informativa |
| `val_disponibilidade` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `val_geracaoreferencia` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (3.52%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `val_geracaolimitada` | ⭐⭐☆☆☆ | Tem variância significativa; Muitos missings (98.2%); Distribuição não-esparsa; Alta correlação com 1 feature(s) |
| `val_geracaoreferenciafinal` | ⭐⭐☆☆☆ | Tem variância significativa; Muitos missings (99.86%); Distribuição não-esparsa |

---
## ONS Restrição COFF Fotovoltaica

**Arquivos processados:** 5  
**Dimensões:** 432,720 linhas x 15 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `id_subsistema` | str | 0 | 0.0% |
| `nom_subsistema` | str | 0 | 0.0% |
| `id_estado` | str | 0 | 0.0% |
| `nom_estado` | str | 0 | 0.0% |
| `nom_usina` | str | 0 | 0.0% |
| `id_ons` | str | 0 | 0.0% |
| `ceg` | str | 0 | 0.0% |
| `din_instante` | str | 0 | 0.0% |
| `val_geracao` | float64 | 0 | 0.0% |
| `val_geracaolimitada` | float64 | 371,591 | 85.9% |
| `val_disponibilidade` | float64 | 0 | 0.0% |
| `val_geracaoreferencia` | float64 | 0 | 0.0% |
| `val_geracaoreferenciafinal` | float64 | 427,356 | 98.8% |
| `cod_razaorestricao` | str | 371,591 | 85.9% |
| `cod_origemrestricao` | str | 371,591 | 85.9% |

### Estatísticas Numéricas

| Estatística | `val_geracao` | `val_geracaolimitada` | `val_disponibilidade` | `val_geracaoreferencia` | `val_geracaoreferenciafinal` |
|-------------|---|---|---|---|---|
| count | 432,720.0 | 61,129.0 | 432,720.0 | 432,720.0 | 5,364.0 |
| mean | 49.0427 | 83.9874 | 156.1338 | 45.2017 | 92.1637 |
| std | 100.2826 | 101.9210 | 196.4393 | 97.1265 | 144.9406 |
| min | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 25% | 0.0000 | 11.0000 | 18.4500 | 0.0000 | 0.0000 |
| 50% | 0.0140 | 49.5000 | 87.8800 | 0.0000 | 28.4600 |
| 75% | 55.3675 | 121.0000 | 205.9880 | 43.2742 | 129.6068 |
| max | 922.7940 | 966.8000 | 1,877.4 | 875.3850 | 835.4310 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_geracao` | `val_geracaolimitada` | 0.9594 🔴 |
| `val_geracaoreferencia` | `val_geracaoreferenciafinal` | 0.8696 🟡 |
| `val_geracao` | `val_geracaoreferencia` | 0.8542 🟡 |
| `val_disponibilidade` | `val_geracaoreferenciafinal` | 0.7207 🟡 |
| `val_geracaolimitada` | `val_disponibilidade` | 0.7080 🟡 |
| `val_geracaolimitada` | `val_geracaoreferencia` | 0.6346 🟢 |
| `val_disponibilidade` | `val_geracaoreferencia` | 0.5448 🟢 |
| `val_geracao` | `val_disponibilidade` | 0.5431 🟢 |
| `val_geracao` | `val_geracaoreferenciafinal` | 0.4773 🟢 |
| `val_geracaolimitada` | `val_geracaoreferenciafinal` | 0.4033 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_geracaoreferencia` | 63,284 | 14.6% |
| `val_geracao` | 52,963 | 12.2% |
| `val_disponibilidade` | 29,363 | 6.8% |
| `val_geracaolimitada` | 3,468 | 0.8% |
| `val_geracaoreferenciafinal` | 526 | 0.1% |

### Cobertura Temporal

- **`din_instante`**: 2024-04-01 00:00:00 → 2024-08-31 23:30:00 (152 dias)

### Variáveis Categóricas

- **`id_subsistema`**: 2 valores únicos
  - Top: "NE" (298,176), "SE" (134,544)
- **`nom_subsistema`**: 2 valores únicos
  - Top: "NORDESTE" (298,176), "SUDESTE/CENTRO-OESTE" (134,544)
- **`id_estado`**: 8 valores únicos
  - Top: "MG" (90,480), "BA" (83,520), "CE" (66,096)
- **`nom_estado`**: 8 valores únicos
  - Top: "MINAS GERAIS" (90,480), "BAHIA" (83,520), "CEARA" (66,096)
- **`nom_usina`**: 61 valores únicos
  - Top: "CONJ. BJL" (7,344), "CONJ. BOM JESUS" (7,344), "CONJ. FUTURA" (7,344)
- **`id_ons`**: 61 valores únicos
  - Top: "CJU_BABJL" (7,344), "CJU_BABJU" (7,344), "CJU_BAFFUT" (7,344)
- **`ceg`**: 5 valores únicos
  - Top: "-" (403,344), "UFV.RS.CE.047255-7.01" (7,344), "UFV.RS.CE.034037-5.01" (7,344)
- **`din_instante`**: 7344 valores únicos
- **`cod_razaorestricao`**: 3 valores únicos
  - Top: "CNF" (33,382), "ENE" (22,383), "REL" (5,364)
- **`cod_origemrestricao`**: 2 valores únicos
  - Top: "SIS" (50,792), "LOC" (10,337)

### Colunas com Alta Proporção de Zeros (>50%)

- `val_geracaoreferencia`: 59.7% zeros

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_geracao` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Alta correlação com 2 feature(s); Outliers moderados - variação informativa |
| `val_disponibilidade` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `val_geracaoreferencia` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Alta correlação com 2 feature(s); Outliers moderados - variação informativa |
| `val_geracaolimitada` | ⭐⭐☆☆☆ | Tem variância significativa; Muitos missings (85.87%); Distribuição não-esparsa; Alta correlação com 1 feature(s) |
| `val_geracaoreferenciafinal` | ⭐⭐☆☆☆ | Tem variância significativa; Muitos missings (98.76%); Distribuição não-esparsa; Alta correlação com 1 feature(s) |

---
## ONS Restrição COFF Fotovoltaica Detalhamento

**Arquivos processados:** 5  
**Dimensões:** 2,620,088 linhas x 12 colunas  
**Duplicatas:** 8 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `id_subsistema` | str | 0 | 0.0% |
| `id_estado` | str | 0 | 0.0% |
| `nom_modalidadeoperacao` | str | 0 | 0.0% |
| `nom_conjuntousina` | str | 29,376 | 1.1% |
| `nom_usina` | str | 0 | 0.0% |
| `id_ons` | str | 0 | 0.0% |
| `ceg` | str | 0 | 0.0% |
| `din_instante` | str | 0 | 0.0% |
| `val_irradianciaverificado` | float64 | 0 | 0.0% |
| `flg_dadoirradianciainvalido` | bool | 0 | 0.0% |
| `val_geracaoestimada` | float64 | 48 | 0.0% |
| `val_geracaoverificada` | float64 | 0 | 0.0% |

### Estatísticas Numéricas

| Estatística | `val_irradianciaverificado` | `val_geracaoestimada` | `val_geracaoverificada` |
|-------------|---|---|---|
| count | 2,620,088.0 | 2,620,040.0 | 2,620,088.0 |
| mean | 242.6788 | 7.5004 | 8.0646 |
| std | 363.6980 | 12.6699 | 12.5742 |
| min | -2.0000 | 0.0000 | -0.0910 |
| 25% | 0.0000 | 0.0000 | 0.0000 |
| 50% | 0.5680 | 0.0000 | 0.0180 |
| 75% | 508.2060 | 14.5850 | 14.9740 |
| max | 123,312.4 | 131.2960 | 164.0000 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_geracaoestimada` | `val_geracaoverificada` | 0.7416 🟡 |
| `val_irradianciaverificado` | `val_geracaoestimada` | 0.6866 🟢 |
| `val_irradianciaverificado` | `val_geracaoverificada` | 0.5927 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_geracaoestimada` | 99,932 | 3.8% |
| `val_geracaoverificada` | 98,779 | 3.8% |
| `val_irradianciaverificado` | 17,678 | 0.7% |

### Cobertura Temporal

- **`din_instante`**: 2024-04-01 00:00:00 → 2024-08-31 23:30:00 (152 dias)

### Variáveis Categóricas

- **`id_subsistema`**: 2 valores únicos
  - Top: "NE" (1,633,488), "SE" (986,600)
- **`id_estado`**: 8 valores únicos
  - Top: "MG" (786,632), "BA" (455,472), "PI" (398,112)
- **`nom_modalidadeoperacao`**: 2 valores únicos
  - Top: "Tipo II-C" (2,590,712), "Tipo II-B" (29,376)
- **`nom_conjuntousina`**: 57 valores únicos
  - Top: "Conj. Futura" (161,568), "Conj. Janaúba" (146,880), "Conj. Sol do Cerrado" (124,848)
- **`nom_usina`**: 379 valores únicos
  - Top: "BJL 11" (7,344), "BJL 4" (7,344), "Bom Jesus da Lapa II" (7,344)
- **`id_ons`**: 379 valores únicos
  - Top: "BAFB11" (7,344), "BAFB04" (7,344), "BAUFB2" (7,344)
- **`ceg`**: 379 valores únicos
  - Top: "UFV.RS.BA.034153-3.01" (7,344), "UFV.RS.BA.034158-4.01" (7,344), "UFV.RS.BA.032893-6.01" (7,344)
- **`din_instante`**: 7344 valores únicos

### Colunas com Alta Proporção de Zeros (>50%)

- `val_geracaoestimada`: 63.7% zeros

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_geracaoestimada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0.0%); Outliers moderados - variação informativa |
| `val_geracaoverificada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Outliers moderados - variação informativa |
| `val_irradianciaverificado` | ⭐⭐⭐⭐☆ | Tem variância significativa; Poucos missings (0%) |

---
## ONS Taxa TEIF/TEIP

**Arquivos processados:** 1  
**Dimensões:** 29,732 linhas x 8 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `nom_usina` | str | 0 | 0.0% |
| `cod_ceg` | str | 1,186 | 4.0% |
| `tip_usina` | str | 0 | 0.0% |
| `din_mes` | str | 0 | 0.0% |
| `nom_taxa` | str | 0 | 0.0% |
| `val_taxa` | float64 | 0 | 0.0% |
| `num_versao` | float64 | 0 | 0.0% |
| `din_calculo` | str | 0 | 0.0% |

### Estatísticas Numéricas

| Estatística | `val_taxa` | `num_versao` |
|-------------|---|---|
| count | 29,732.0 | 29,732.0 |
| mean | 0.0519 | 1.3038 |
| std | 0.0916 | 1.0603 |
| min | 0.0000 | 1.0000 |
| 25% | 0.0105 | 1.0000 |
| 50% | 0.0267 | 1.0000 |
| 75% | 0.0534 | 1.0000 |
| max | 1.0000 | 19.0000 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_taxa` | `num_versao` | -0.0152 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_taxa` | 2,924 | 9.8% |

### Cobertura Temporal

- **`din_mes`**: 2021-04-01 00:00:00 → 2026-04-01 00:00:00 (1826 dias)
- **`din_calculo`**: 2022-11-13 00:13:47.990000 → 2026-05-29 12:04:48.387000 (1293 dias)

### Variáveis Categóricas

- **`nom_usina`**: 265 valores únicos
  - Top: "CANA BRAVA" (124), "14 DE JULHO" (122), "AGUA VERMELHA" (122)
- **`cod_ceg`**: 251 valores únicos
  - Top: "UHE.PH.PA.030354-2.01" (244), "UHE.PH.SP.001084-7.01" (244), "UHE.PH.PR.001161-4.01" (244)
- **`tip_usina`**: 3 valores únicos
  - Top: "Hidroelétrica                 " (19,656), "Térmica                       " (9,832), "Nuclear                       " (244)
- **`din_mes`**: 61 valores únicos
  - Top: "2023-12-01" (508), "2023-11-01" (506), "2023-10-01" (506)
- **`nom_taxa`**: 2 valores únicos
  - Top: "TEIFa" (14,866), "TEIP" (14,866)
- **`din_calculo`**: 15335 valores únicos

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_taxa` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `num_versao` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |

---
## ONS Taxa TEIF/TEIP Operacional

**Arquivos processados:** 1  
**Dimensões:** 29,735 linhas x 8 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `nom_usina` | str | 0 | 0.0% |
| `cod_ceg` | str | 1,186 | 4.0% |
| `tip_usina` | str | 0 | 0.0% |
| `din_mes` | str | 0 | 0.0% |
| `nom_taxa` | str | 0 | 0.0% |
| `val_taxa` | float64 | 0 | 0.0% |
| `num_versao` | float64 | 0 | 0.0% |
| `din_calculo` | str | 0 | 0.0% |

### Estatísticas Numéricas

| Estatística | `val_taxa` | `num_versao` |
|-------------|---|---|
| count | 29,735.0 | 29,735.0 |
| mean | 0.0466 | 1.3658 |
| std | 0.0724 | 1.1314 |
| min | 0.0000 | 1.0000 |
| 25% | 0.0104 | 1.0000 |
| 50% | 0.0263 | 1.0000 |
| 75% | 0.0502 | 1.0000 |
| max | 0.8195 | 21.0000 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_taxa` | `num_versao` | -0.0325 🟢 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_taxa` | 2,822 | 9.5% |

### Cobertura Temporal

- **`din_mes`**: 2021-04-01 00:00:00 → 2026-04-01 00:00:00 (1826 dias)
- **`din_calculo`**: 2022-11-13 00:13:47.990000 → 2026-05-29 12:04:48.387000 (1293 dias)

### Variáveis Categóricas

- **`nom_usina`**: 265 valores únicos
  - Top: "CANA BRAVA" (124), "14 DE JULHO" (122), "AGUA VERMELHA" (122)
- **`cod_ceg`**: 251 valores únicos
  - Top: "UHE.PH.PA.030354-2.01" (244), "UHE.PH.SP.001084-7.01" (244), "UHE.PH.PR.001161-4.01" (244)
- **`tip_usina`**: 3 valores únicos
  - Top: "Hidroelétrica                 " (19,656), "Térmica                       " (9,835), "Nuclear                       " (244)
- **`din_mes`**: 61 valores únicos
  - Top: "2023-12-01" (508), "2023-11-01" (506), "2023-10-01" (506)
- **`nom_taxa`**: 2 valores únicos
  - Top: "TEIFa_oper" (14,869), "TEIP_oper" (14,866)
- **`din_calculo`**: 16724 valores únicos

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `val_taxa` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `num_versao` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |

---
## ONS Dados Hidrológicos (Parquet)

**Arquivos processados:** 33  
**Dimensões:** 1,116,576 linhas x 18 colunas  
**Duplicatas:** 0 (0.0%)

### Colunas e Tipos

| Coluna | Tipo | Missing | Missing % |
|--------|------|---------|-----------|
| `id_subsistema` | str | 0 | 0.0% |
| `nom_subsistema` | str | 0 | 0.0% |
| `tip_reservatorio` | str | 0 | 0.0% |
| `nom_bacia` | str | 0 | 0.0% |
| `id_reservatorio` | str | 0 | 0.0% |
| `nom_reservatorio` | str | 0 | 0.0% |
| `cod_usina` | int64 | 0 | 0.0% |
| `din_instante` | datetime64[ns] | 0 | 0.0% |
| `val_nivelmontante` | float64 | 6,105 | 0.6% |
| `val_niveljusante` | float64 | 53,671 | 4.8% |
| `val_volumeutil` | float64 | 21,550 | 1.9% |
| `val_vazaoafluente` | float64 | 41,290 | 3.7% |
| `val_vazaodefluente` | float64 | 22,963 | 2.1% |
| `val_vazaoturbinada` | float64 | 67,939 | 6.1% |
| `val_vazaovertida` | float64 | 54,182 | 4.8% |
| `val_vazaooutrasestruturas` | float64 | 407,079 | 36.5% |
| `val_vazaotransferida` | float64 | 499,311 | 44.7% |
| `val_vazaovertidanaoturbinavel` | float64 | 1,109,280 | 99.3% |

### Estatísticas Numéricas

| Estatística | `cod_usina` | `val_nivelmontante` | `val_niveljusante` | `val_volumeutil` | `val_vazaoafluente` | `val_vazaodefluente` | `val_vazaoturbinada` | `val_vazaovertida` | `val_vazaooutrasestruturas` | `val_vazaotransferida` | `val_vazaovertidanaoturbinavel` |
|-------------|---|---|---|---|---|---|---|---|---|---|---|
| count | 1,116,576.0 | 1,110,471.0 | 1,062,905.0 | 1,095,026.0 | 1,075,286.0 | 1,093,613.0 | 1,048,637.0 | 1,062,394.0 | 709,497.0 | 617,265.0 | 7,296.0 |
| mean | 134.3691 | 399.0033 | 333.9336 | 57.9488 | 940.3694 | 898.4457 | 759.3197 | 166.9335 | 6.7150 | 47.2322 | 971.1774 |
| std | 93.6223 | 215.8509 | 207.9190 | 87.4518 | 3,658.7 | 3,266.0 | 2,323.3 | 1,310.9 | 46.2382 | 532.9341 | 1,797.8 |
| min | 1.0000 | 0.0000 | 0.0000 | -943.8100 | -681,969.0 | 0.0000 | 0.0000 | 0.0000 | -27.0000 | -571.0000 | 0.0000 |
| 25% | 49.0000 | 254.6000 | 168.5400 | 41.0400 | 58.0000 | 70.0000 | 62.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 50% | 121.0000 | 376.0100 | 326.6500 | 68.0800 | 185.0000 | 195.0000 | 189.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 75% | 203.0000 | 561.9400 | 495.0200 | 87.9100 | 642.0000 | 623.0000 | 577.0000 | 0.0000 | 1.0000 | 0.0000 | 1,760.0 |
| max | 315.0000 | 1,240.5 | 6,959.5 | 1,479.0 | 661,916.0 | 46,338.0 | 29,198.0 | 100,000.0 | 6,893.0 | 9,242.0 | 6,032.0 |

### Correlações Mais Fortes

| Feature A | Feature B | Correlação |
|-----------|-----------|------------|
| `val_nivelmontante` | `val_niveljusante` | 0.9750 🔴 |
| `val_vazaodefluente` | `val_vazaoturbinada` | 0.9497 🔴 |
| `val_vazaovertida` | `val_vazaovertidanaoturbinavel` | 0.9178 🔴 |
| `val_vazaodefluente` | `val_vazaovertidanaoturbinavel` | 0.9072 🔴 |
| `val_vazaoafluente` | `val_vazaodefluente` | 0.9056 🔴 |
| `val_niveljusante` | `val_vazaovertidanaoturbinavel` | 0.8650 🟡 |
| `val_vazaoafluente` | `val_vazaoturbinada` | 0.8509 🟡 |
| `val_vazaodefluente` | `val_vazaovertida` | 0.8309 🟡 |
| `val_vazaoafluente` | `val_vazaovertidanaoturbinavel` | 0.7992 🟡 |
| `val_vazaoafluente` | `val_vazaovertida` | 0.7685 🟡 |

### Outliers (método IQR)

| Coluna | Outliers | % |
|--------|----------|---|
| `val_vazaoafluente` | 135,764 | 12.2% |
| `val_vazaooutrasestruturas` | 131,161 | 11.8% |
| `val_vazaodefluente` | 116,290 | 10.4% |
| `val_vazaoturbinada` | 110,532 | 9.9% |
| `val_volumeutil` | 17,354 | 1.6% |
| `val_vazaovertidanaoturbinavel` | 720 | 0.1% |
| `val_nivelmontante` | 2 | 0.0% |
| `val_niveljusante` | 7 | 0.0% |

### Cobertura Temporal

- **`din_instante`**: 2019-01-01 01:00:00 → 2019-10-31 23:59:00 (303 dias)

### Variáveis Categóricas

- **`id_subsistema`**: 4 valores únicos
  - Top: "SE" (752,305), "S" (225,920), "N" (72,797)
- **`nom_subsistema`**: 4 valores únicos
  - Top: "Sudeste/Centro-Oeste" (752,305), "Sul" (225,920), "Norte" (72,797)
- **`tip_reservatorio`**: 4 valores únicos
  - Top: "Fio dagua" (610,950), "Reservatório com Usina" (443,147), "Reservatório sem usina" (49,131)
- **`nom_bacia`**: 22 valores únicos
  - Top: "PARANAIBA" (138,387), "GRANDE" (109,377), "AMAZONAS" (108,568)
- **`id_reservatorio`**: 154 valores únicos
  - Top: "AMUHRD" (7,298), "GRJAGU" (7,297), "AMUSBM" (7,296)
- **`nom_reservatorio`**: 154 valores únicos
  - Top: "RONDON II" (7,298), "JAGUARA" (7,297), "BELO MONTE" (7,296)

### Colunas com Alta Proporção de Zeros (>50%)

- `val_vazaovertida`: 75.5% zeros
- `val_vazaotransferida`: 50.4% zeros

### Ranking de Features para ML

| Feature | Score (0-5) | Razões |
|---------|-------------|--------|
| `cod_usina` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa |
| `val_nivelmontante` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (0.55%); Distribuição não-esparsa; Alta correlação com 1 feature(s) |
| `val_niveljusante` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (4.81%); Distribuição não-esparsa; Alta correlação com 2 feature(s) |
| `val_volumeutil` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (1.93%); Distribuição não-esparsa; Outliers moderados - variação informativa |
| `val_vazaoafluente` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (3.7%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa |
| `val_vazaodefluente` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Poucos missings (2.06%); Distribuição não-esparsa; Alta correlação com 4 feature(s); Outliers moderados - variação informativa |
| `val_vazaoturbinada` | ⭐⭐⭐⭐⭐ | Tem variância significativa; Missings moderados (6.08%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa |
| `val_vazaovertida` | ⭐⭐⭐⭐☆ | Tem variância significativa; Poucos missings (4.85%); Alta correlação com 2 feature(s) |
| `val_vazaooutrasestruturas` | ⭐⭐☆☆☆ | Tem variância significativa; Muitos missings (36.46%); Outliers moderados - variação informativa |
| `val_vazaovertidanaoturbinavel` | ⭐⭐☆☆☆ | Tem variância significativa; Muitos missings (99.35%); Distribuição não-esparsa; Alta correlação com 3 feature(s) |
| `val_vazaotransferida` | ⭐☆☆☆☆ | Tem variância significativa; Muitos missings (44.72%) |

---
# Recomendações Gerais de Features para ML

## Top Features por Dataset

### ANEEL SIGA - Sistema de Informações de Geração

- **`IdeNucleoCEG`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa
- **`NumCoordNEmpreendimento_numeric`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa
- **`NumCoordEEmpreendimento_numeric`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa
- **`MdaPotenciaFiscalizadaKw`** (score 4/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Muitos outliers (22.95%)
- **`MdaPotenciaOutorgadaKw_numeric`** (score 4/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Muitos outliers (22.15%)
- **`MdaGarantiaFisicaKw_numeric`** (score 3/5): Tem variância significativa; Poucos missings (0%); Alta proporção de zeros (88.92%); Alta correlação com 2 feature(s)

### ONS Balanço DESSEM Geral

- **`num_patamar`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa
- **`val_demanda`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s); Outliers moderados - variação informativa
- **`val_geracao_renovavel`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa
- **`val_geracao_hidraulica`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa
- **`val_geracao_termica`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s)
- **`val_cons_elevatoria`** (score 3/5): Tem variância significativa; Poucos missings (0%); Muitos outliers (25.0%)

### ONS Balanço DESSEM Detalhe

- **`num_patamar`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa
- **`val_demanda`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa
- **`val_ger_hidraulica`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 4 feature(s); Outliers moderados - variação informativa
- **`val_ger_termica`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s)
- **`val_ger_mmgd`** (score 5/5): Tem variância significativa; Poucos missings (0%); Alta correlação com 1 feature(s); Outliers moderados - variação informativa
- **`val_ger_pch`** (score 4/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 5 feature(s); Muitos outliers (25.0%)
- **`val_ger_pct`** (score 4/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 5 feature(s); Muitos outliers (25.0%)
- **`val_ger_eolica`** (score 4/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Muitos outliers (23.85%)
- **`val_ger_fotovoltaica`** (score 3/5): Tem variância significativa; Poucos missings (0%); Alta correlação com 1 feature(s); Muitos outliers (23.44%)
- **`val_cons_elevatoria`** (score 3/5): Tem variância significativa; Poucos missings (0%); Alta correlação com 2 feature(s); Muitos outliers (25.0%)

### ONS Disponibilidade de Usina

- **`val_potenciainstalada`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa
- **`val_dispoperacional`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa
- **`val_dispsincronizada`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa

### ONS Fator de Capacidade

- **`val_latitudesecoletora`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa
- **`val_longitudesecoletora`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa
- **`val_latitudepontoconexao`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa
- **`val_longitudepontoconexao`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 3 feature(s); Outliers moderados - variação informativa
- **`val_geracaoprogramada`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa
- **`val_geracaoverificada`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s); Outliers moderados - variação informativa
- **`val_capacidadeinstalada`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa
- **`val_fatorcapacidade`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s)

### ONS Geração por Usina

- **`val_geracao`** (score 5/5): Tem variância significativa; Poucos missings (0.0%); Distribuição não-esparsa; Outliers moderados - variação informativa

### ONS Restrição COFF Eólica Detalhamento

- **`val_ventoverificado`** (score 5/5): Tem variância significativa; Poucos missings (0.06%); Distribuição não-esparsa
- **`val_geracaoverificada`** (score 5/5): Tem variância significativa; Poucos missings (0.06%); Distribuição não-esparsa; Outliers moderados - variação informativa
- **`flg_dadoventoinvalido`** (score 4/5): Tem variância significativa; Poucos missings (0.06%)
- **`val_geracaoestimada`** (score 4/5): Tem variância significativa; Missings moderados (5.33%); Outliers moderados - variação informativa

### ONS Restrição COFF Eólica por Usina

- **`val_geracao`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Alta correlação com 1 feature(s); Outliers moderados - variação informativa
- **`val_disponibilidade`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa
- **`val_geracaoreferencia`** (score 5/5): Tem variância significativa; Poucos missings (3.52%); Distribuição não-esparsa; Outliers moderados - variação informativa

### ONS Restrição COFF Fotovoltaica

- **`val_geracao`** (score 5/5): Tem variância significativa; Poucos missings (0%); Alta correlação com 2 feature(s); Outliers moderados - variação informativa
- **`val_disponibilidade`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa
- **`val_geracaoreferencia`** (score 5/5): Tem variância significativa; Poucos missings (0%); Alta correlação com 2 feature(s); Outliers moderados - variação informativa

### ONS Restrição COFF Fotovoltaica Detalhamento

- **`val_geracaoestimada`** (score 5/5): Tem variância significativa; Poucos missings (0.0%); Outliers moderados - variação informativa
- **`val_geracaoverificada`** (score 5/5): Tem variância significativa; Poucos missings (0%); Outliers moderados - variação informativa
- **`val_irradianciaverificado`** (score 4/5): Tem variância significativa; Poucos missings (0%)

### ONS Taxa TEIF/TEIP

- **`val_taxa`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa
- **`num_versao`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa

### ONS Taxa TEIF/TEIP Operacional

- **`val_taxa`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa; Outliers moderados - variação informativa
- **`num_versao`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa

### ONS Dados Hidrológicos (Parquet)

- **`cod_usina`** (score 5/5): Tem variância significativa; Poucos missings (0%); Distribuição não-esparsa
- **`val_nivelmontante`** (score 5/5): Tem variância significativa; Poucos missings (0.55%); Distribuição não-esparsa; Alta correlação com 1 feature(s)
- **`val_niveljusante`** (score 5/5): Tem variância significativa; Poucos missings (4.81%); Distribuição não-esparsa; Alta correlação com 2 feature(s)
- **`val_volumeutil`** (score 5/5): Tem variância significativa; Poucos missings (1.93%); Distribuição não-esparsa; Outliers moderados - variação informativa
- **`val_vazaoafluente`** (score 5/5): Tem variância significativa; Poucos missings (3.7%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa
- **`val_vazaodefluente`** (score 5/5): Tem variância significativa; Poucos missings (2.06%); Distribuição não-esparsa; Alta correlação com 4 feature(s); Outliers moderados - variação informativa
- **`val_vazaoturbinada`** (score 5/5): Tem variância significativa; Missings moderados (6.08%); Distribuição não-esparsa; Alta correlação com 2 feature(s); Outliers moderados - variação informativa
- **`val_vazaovertida`** (score 4/5): Tem variância significativa; Poucos missings (4.85%); Alta correlação com 2 feature(s)

## Estratégias de Feature Engineering Sugeridas

### 1. Features Temporais
- Extrair hora, dia da semana, mês, trimestre das colunas `din_instante`
- Criar lags temporais (t-1, t-2, ..., t-24) para séries horárias
- Médias móveis (7d, 30d) para suavizar sazonalidade
- Indicadores de fim de semana, feriado, horário de ponta

### 2. Features de Geração de Energia
- Ratio geração/capacidade instalada = fator de capacidade real
- Diferença geração verificada - geração programada = desvio operacional
- Geração por fonte (eólica, solar, hidro, térmica) como % do total
- Disponibilidade sincronizada / potência instalada = fator de disponibilidade

### 3. Features Meteorológicas Implícitas
- `val_ventoverificado` → proxy para regime de ventos
- `val_irradianciaverificado` → proxy para insolação
- Essas variáveis são inputs diretos para modelos de previsão de geração renovável

### 4. Features Geográficas
- Subsistema (N, NE, S, SE) como feature categórica
- Estado como feature com encoding geográfico
- Lat/Long dos pontos de conexão para features espaciais

### 5. Features de Restrição Operacional
- Taxa de restrição = geração limitada / geração de referência
- Indicador binário de corte (curtailment)
- Código de razão de restrição como categórica

### 6. Features de Confiabilidade
- TEIF (Taxa de Indisponibilidade Forçada) como indicador de risco
- TEIP (Taxa de Indisponibilidade Programada) para manutenção
- Essas taxas permitem prever falhas e indisponibilidades futuras

### 7. Cross-Dataset Features
- JOIN geração + fator capacidade por usina/instante → eficiência real
- JOIN geração + restrição → geração líquida vs potencial
- JOIN disponibilidade + TEIF/TEIP → modelo de confiabilidade
- JOIN ANEEL SIGA + geração → features de tipo/porte da usina

## Possíveis Targets para Modelos ML

| Target | Tipo | Dataset Principal | Aplicação |
|--------|------|-------------------|-----------|
| `val_geracao` | Regressão | geracao-usina-2 | Previsão de geração por usina |
| `val_fatorcapacidade` | Regressão | fator-capacidade-2 | Previsão de fator de capacidade |
| `val_demanda` | Regressão | balanco_dessem_geral | Previsão de demanda por subsistema |
| `val_dispoperacional` | Regressão | disponibilidade_usina | Previsão de disponibilidade |
| `cod_razaorestricao` | Classificação | restricao_coff_eolica | Classificar tipo de restrição |
| `val_taxa` (TEIF) | Regressão | taxa_teif_teip | Previsão de indisponibilidade forçada |
| Curtailment (sim/não) | Classificação | restricao_coff_* | Detectar corte de geração |

## Cuidados e Pitfalls

1. **Dados em formato BR**: Vírgula como decimal, ponto como milhar — converter antes de usar
2. **Encoding**: Alguns CSVs (ANEEL) usam latin-1 com caracteres corrompidos — limpar acentos
3. **Zeros vs Missing**: Muitas colunas têm zeros que significam 'sem geração' (válido) vs missing real
4. **Multicolinearidade**: Colunas como geração programada/verificada/estimada são altamente correlacionadas — escolher uma ou usar PCA
5. **Leakage temporal**: Não usar dados futuros como features — respeitar janelas temporais
6. **Sazonalidade**: Geração eólica/solar tem forte sazonalidade — usar features cíclicas (sin/cos)
7. **Granularidade**: Dados variam de horário a mensal — alinhar temporalmente antes de fazer joins

# Markets Data Hub

Datapipeline som samlar in, validerar och visualiserar svensk finansmarknadsdata. Byggt med [Dagster](https://dagster.io/) och driftas på Dagster Cloud Serverless.

## Datakällor och assets

Projektet innehåller fyra assets i gruppen **Market_operations**:

| Asset | Beskrivning | Källa | Schema |
|---|---|---|---|
| `riksbank_certificate` | Auktionsresultat för Riksbankscertifikat (erbjuden/tilldelad volym, ränta, ISIN m.m.) | Webscraping av Riksbankens sida | Tisdagar 10:40 UTC |
| `sales_of_gov_bonds` | Auktionsresultat för statsobligationer (SGB) och reala statsobligationer (SGB IL) | Webscraping av Riksbankens sida | Fredagar 10:40 UTC |
| `get_swestr_values` | SWESTR-noteringar (ränta, percentilspridning, volym, antal transaktioner) | Riksbankens SWESTR-API | Vardagar 09:05 UTC |
| `get_policy_rate_values` | Riksbankens styrränta (SECBREPOEFF-serien) | Riksbankens SWEA-API | Vardagar 09:05 UTC |

All data valideras med Pydantic-scheman, transformeras med Polars och lagras som Parquet-filer.

## Interaktiv analys

En [Marimo](https://marimo.io/)-notebook (`src/markets_data_hub/notebooks/analysis.py`) visualiserar insamlad data:

- **Riksbankscertifikat** -- nyckeltal för senaste auktionen, likviditetsöverskott över tid
- **Statsobligationer** -- bid-to-cover per auktion för SGB och SGB IL
- **Kort penningmarknad** -- aktuell SWESTR-notering, spridningsboxplottar, SWESTR vs styrränta över tid

Starta notebooken med:

```bash
marimo run src/markets_data_hub/notebooks/analysis.py
```

## Kom igång

### Förutsättningar

- Python >= 3.10, < 3.15
- En API-nyckel från Riksbanken (för SWESTR- och SWEA-API:erna)

### Installation

```bash
pip install -e ".[dev]"
```

### Miljövariabler

| Variabel | Beskrivning |
|---|---|
| `RIKSBANK_API_KEY` | API-nyckel för Riksbankens SWESTR- och SWEA-API:er |

### Starta Dagster lokalt

```bash
dagster dev
```

Öppna http://localhost:3000 i webbläsaren.

## Tester

```bash
pytest tests
```

## Teknikstack

- **Dagster** -- orkestrering och schemaläggning
- **Polars** -- datatransformation
- **Pydantic** -- datavalidering
- **BeautifulSoup4** -- webscraping
- **Marimo + Altair** -- interaktiv visualisering
- **Parquet** -- datalagring

## Projektstruktur

```
src/markets_data_hub/
  definitions.py          # Jobs, scheman och resursdefinitioner
  assets/
    assets.py             # Asset-definitioner (datapipelines)
    schemas.py            # Pydantic-modeller
  utils/
    constants.py          # Nyckelmappningar för datatransformation
    functions.py          # Scraping- och API-funktioner
  notebooks/
    analysis.py           # Marimo-notebook för visualisering
  data/                   # Genererade Parquet-filer
tests/
  test_assets.py          # Enhetstester för assets
  test_defs.py            # Tester för pipeline-definitioner
```

## Deployment

Projektet deployar automatiskt till [Dagster Cloud Serverless](https://dagster.io/cloud) via GitHub Actions:

- **Push till main** -- produktionsdeploy (`deploy.yml`)
- **Push till feature-branch** -- branch-deploy (`branch_deployments.yml`)

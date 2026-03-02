# Markets Data Hub

Data pipeline that collects, validates, and visualizes Swedish financial market data. Built with [Dagster](https://dagster.io/) and hosted on Dagster Cloud Serverless.

## Data sources and assets

The project contains four assets in the **Market_operations** group:

| Asset | Description | Source | Schedule |
|---|---|---|---|
| `riksbank_certificate` | Auction results for Riksbank certificates (offered/allocated volume, interest rate, ISIN, etc.) | Web scraping of the Riksbank website | Tuesdays 10:40 UTC |
| `sales_of_gov_bonds` | Auction results for government bonds (SGB) and inflation-linked government bonds (SGB IL) | Web scraping of the Riksbank website | Fridays 10:40 UTC |
| `get_swestr_values` | SWESTR rates (interest rate, percentile spread, volume, number of transactions) | Riksbank SWESTR API | Weekdays 09:05 UTC |
| `get_policy_rate_values` | Riksbank policy rate (SECBREPOEFF series) | Riksbank SWEA API | Weekdays 09:05 UTC |

All data is validated with Pydantic schemas, transformed with Polars, and stored as Parquet files.

## Interactive analysis

A [Marimo](https://marimo.io/) notebook (`src/markets_data_hub/notebooks/analysis.py`) visualizes the collected data:

- **Riksbank certificates** -- key metrics from the latest auction, liquidity surplus over time
- **Government bonds** -- bid-to-cover ratio per auction for SGB and SGB IL
- **Short-term money market** -- current SWESTR rate, spread box plots, SWESTR vs policy rate over time

Run the notebook with:

```bash
marimo run src/markets_data_hub/notebooks/analysis.py
```

## Getting started

### Prerequisites

- Python >= 3.10, < 3.15
- A Riksbank API key (for the SWESTR and SWEA APIs)

### Installation

```bash
pip install -e ".[dev]"
```

### Environment variables

| Variable | Description |
|---|---|
| `RIKSBANK_API_KEY` | API key for the Riksbank SWESTR and SWEA APIs |

### Running Dagster locally

```bash
dagster dev
```

Open http://localhost:3000 in your browser.

## Tests

```bash
pytest tests
```

## Tech stack

- **Dagster** -- orchestration and scheduling
- **Polars** -- data transformation
- **Pydantic** -- data validation
- **BeautifulSoup4** -- web scraping
- **Marimo + Altair** -- interactive visualization
- **Parquet** -- data storage

## Project structure

```
src/markets_data_hub/
  definitions.py          # Jobs, schedules, and resource definitions
  assets/
    assets.py             # Asset definitions (data pipelines)
    schemas.py            # Pydantic models
  utils/
    constants.py          # Key mappings for data transformation
    functions.py          # Scraping and API functions
  notebooks/
    analysis.py           # Marimo notebook for visualization
  data/                   # Generated Parquet files
tests/
  test_assets.py          # Unit tests for assets
  test_defs.py            # Tests for pipeline definitions
```

## Deployment

The project deploys automatically to [Dagster Cloud Serverless](https://dagster.io/cloud) via GitHub Actions:

- **Push to main** -- production deploy (`deploy.yml`)
- **Push to feature branch** -- branch deploy (`branch_deployments.yml`)

## TODO

- Update README
- Add an export of data
- API to access data for Riksbank certificate auctions and Sales of government bond

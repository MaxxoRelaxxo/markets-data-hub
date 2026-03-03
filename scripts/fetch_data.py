#!/usr/bin/env python3
"""Standalone data fetcher for CI.

Fetches market data from Riksbank APIs, web scraping, and SCB,
then writes Parquet files.  When these are committed and pushed to
main the GitHub Pages workflow rebuilds the frontend automatically.

Usage:
    uv run python scripts/fetch_data.py --swestr --policy-rate
    uv run python scripts/fetch_data.py --certificates --bonds
    uv run python scripts/fetch_data.py --scb
    uv run python scripts/fetch_data.py --all
    uv run python scripts/fetch_data.py --check-19th   # exit 0 / prints true|false
"""

import argparse
import logging
import os
import sys
from datetime import date, timedelta
from pathlib import Path

import polars as pl
import requests

# Ensure src package is on the path (for local runs without uv)
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from markets_data_hub.utils.functions import (
    scrape_rb_cert_auctions,
    transform_record,
    scrape_riksbank_auctions,
    convert_record,
    fetch_scb,
)
from markets_data_hub.assets.schemas import (
    RbCertAuctionResult,
    AuctionResult,
    SwestrResult,
    PolicyRateResult,
)

DATA_DIR = ROOT / "src" / "markets_data_hub" / "data"
DATA_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("fetch_data")


# ---------------------------------------------------------------------------
# Swedish banking-day helpers (duplicated from definitions.py so this script
# stays independent of Dagster)
# ---------------------------------------------------------------------------

def _swedish_public_holidays(year: int) -> set[date]:
    a = year % 19
    b, c = divmod(year, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    easter = date(year, month, day)

    jun20 = date(year, 6, 20)
    midsummer_day = jun20 + timedelta(days=(5 - jun20.weekday()) % 7)
    midsummer_eve = midsummer_day - timedelta(days=1)

    oct31 = date(year, 10, 31)
    all_saints = oct31 + timedelta(days=(5 - oct31.weekday()) % 7)

    return {
        date(year, 1, 1),
        date(year, 1, 6),
        easter - timedelta(days=2),
        easter,
        easter + timedelta(days=1),
        date(year, 5, 1),
        easter + timedelta(days=39),
        date(year, 6, 6),
        midsummer_eve,
        midsummer_day,
        all_saints,
        date(year, 12, 24),
        date(year, 12, 25),
        date(year, 12, 26),
        date(year, 12, 31),
    }


def _is_banking_day(d: date) -> bool:
    return d.weekday() < 5 and d not in _swedish_public_holidays(d.year)


def is_nth_banking_day(target_date: date, n: int) -> bool:
    """Return True if *target_date* is the n-th banking day of its month."""
    d = date(target_date.year, target_date.month, 1)
    count = 0
    while d <= target_date:
        if _is_banking_day(d):
            count += 1
        if d == target_date:
            return count == n
        d += timedelta(days=1)
    return False


# ---------------------------------------------------------------------------
# Fetch targets
# ---------------------------------------------------------------------------

def fetch_swestr() -> None:
    api_key = os.environ["RIKSBANK_API_KEY"]
    log.info("Fetching SWESTR rates ...")
    resp = requests.get(
        "https://api.riksbank.se/swestr/v1/all/SWESTR",
        params={"fromDate": "2020-01-01"},
        headers={
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": api_key,
        },
        timeout=30,
    )
    resp.raise_for_status()

    validated = [SwestrResult(**row) for row in resp.json()]
    df = pl.DataFrame(
        [r.model_dump() for r in validated],
        schema={
            "rate": pl.Float64,
            "date": pl.Date,
            "pctl12_5": pl.Float64,
            "pctl87_5": pl.Float64,
            "volume": pl.Int64,
            "alternativeCalculation": pl.Boolean,
            "alternativeCalculationReason": pl.Utf8,
            "publicationTime": pl.Datetime,
            "republication": pl.Boolean,
            "numberOfTransactions": pl.Int64,
            "numberOfAgents": pl.Int64,
        },
    )

    path = DATA_DIR / "swestr_values.parquet"
    df.write_parquet(path)
    log.info("SWESTR: %d rows -> %s", len(df), path)


def fetch_policy_rate() -> None:
    api_key = os.environ["RIKSBANK_API_KEY"]
    log.info("Fetching policy rate ...")
    resp = requests.get(
        "https://api.riksbank.se/swea/v1/Observations/SECBREPOEFF/1994-06-01",
        headers={
            "Cache-Control": "no-cache",
            "Ocp-Apim-Subscription-Key": api_key,
        },
        timeout=30,
    )
    resp.raise_for_status()

    validated = [PolicyRateResult(**row) for row in resp.json()]
    df = pl.DataFrame([r.model_dump() for r in validated])

    path = DATA_DIR / "policy_rate_values.parquet"
    df.write_parquet(path)
    log.info("Policy rate: %d rows -> %s", len(df), path)


def fetch_certificates() -> None:
    log.info("Scraping Riksbank certificate auctions ...")
    data = scrape_rb_cert_auctions(limit=None)

    validated = []
    for r in data:
        try:
            mapped = transform_record(r)
            if mapped is None:
                continue
            validated.append(RbCertAuctionResult(**mapped))
        except Exception as e:
            log.warning("Cert validation error: %s", e)

    df = pl.DataFrame([v.model_dump() for v in validated])
    path = DATA_DIR / "rb_cert_auctions_result.parquet"
    df.write_parquet(path)
    log.info("Certificates: %d rows -> %s", len(df), path)


def fetch_bonds() -> None:
    log.info("Scraping government bond auctions ...")
    data = scrape_riksbank_auctions()

    validated = []
    for r in data:
        try:
            parsed = convert_record(r)
            validated.append(AuctionResult(**parsed))
        except Exception as e:
            log.warning("Bond validation error: %s", e)

    df = pl.DataFrame([item.model_dump() for item in validated])
    path = DATA_DIR / "sales_of_government_bonds.parquet"
    df.write_parquet(path)
    log.info("Bonds: %d rows -> %s", len(df), path)


def fetch_scb_rates() -> None:
    log.info("Fetching SCB mortgage rates ...")
    mortgage = fetch_scb(
        table_id="TAB5783",
        selection={
            "ContentsCode": ["000004ZW"],
            "Referenssektor": ["1", "1.1", "1.2"],
            "Motpartssektor": ["2c"],
            "Avtal": ["0200", "0100"],
            "Rantebindningstid": ["*"],
            "Tid": ["*"],
        },
    )
    path = DATA_DIR / "mortgage_rates.parquet"
    mortgage.write_parquet(path)
    log.info("Mortgage rates: %d rows -> %s", len(mortgage), path)

    log.info("Fetching SCB deposit rates ...")
    deposit = fetch_scb(
        table_id="TAB4386",
        selection={
            "ContentsCode": ["000000N3"],
            "Referenssektor": ["1.1b"],
            "Motpartssektor": ["2"],
            "Avtal": ["0200", "0100"],
            "Rantebindningstid": ["*"],
            "Tid": ["*"],
        },
    )
    path = DATA_DIR / "deposit_rates.parquet"
    deposit.write_parquet(path)
    log.info("Deposit rates: %d rows -> %s", len(deposit), path)

    log.info("Fetching SCB NFC lending rates ...")
    nfc = fetch_scb(
        table_id="TAB3406",
        selection={
            "BranschKrita": ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "99"],
            "FtgStrlKrita": ["0", "1", "2", "3", "4"],
            "UrspRant": ["0", "1"],
            "AterRant": ["0", "1"],
            "ContentsCode": ["000003FR", "000006WB"],
            "Tid": ["*"],
        },
    )
    path = DATA_DIR / "nfc_lending_rates.parquet"
    nfc.write_parquet(path)
    log.info("NFC lending: %d rows -> %s", len(nfc), path)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

TARGETS = {
    "swestr": fetch_swestr,
    "policy_rate": fetch_policy_rate,
    "certificates": fetch_certificates,
    "bonds": fetch_bonds,
    "scb": fetch_scb_rates,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch market data to Parquet.")
    parser.add_argument("--swestr", action="store_true")
    parser.add_argument("--policy-rate", action="store_true")
    parser.add_argument("--certificates", action="store_true")
    parser.add_argument("--bonds", action="store_true")
    parser.add_argument("--scb", action="store_true")
    parser.add_argument("--all", action="store_true", help="Fetch all targets")
    parser.add_argument(
        "--check-19th",
        action="store_true",
        help="Print true/false if today is the 19th banking day, then exit.",
    )
    args = parser.parse_args()

    if args.check_19th:
        print("true" if is_nth_banking_day(date.today(), 19) else "false")
        return

    selected: list[tuple[str, callable]] = []
    if args.all or args.swestr:
        selected.append(("swestr", fetch_swestr))
    if args.all or args.policy_rate:
        selected.append(("policy_rate", fetch_policy_rate))
    if args.all or args.certificates:
        selected.append(("certificates", fetch_certificates))
    if args.all or args.bonds:
        selected.append(("bonds", fetch_bonds))
    if args.all or args.scb:
        selected.append(("scb", fetch_scb_rates))

    if not selected:
        parser.error("Specify at least one target (--swestr, --policy-rate, etc.) or --all")

    ok, fail = 0, 0
    for name, fn in selected:
        try:
            fn()
            ok += 1
        except Exception:
            log.exception("FAILED: %s", name)
            fail += 1

    log.info("Done. %d succeeded, %d failed.", ok, fail)
    if fail:
        sys.exit(1)


if __name__ == "__main__":
    main()

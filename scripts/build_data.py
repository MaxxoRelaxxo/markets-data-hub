#!/usr/bin/env python3
"""Convert Parquet/Excel data to JSON for the React frontend."""

import json
from datetime import date, datetime
from pathlib import Path

import polars as pl

DATA_DIR = Path(__file__).resolve().parent.parent / "src" / "markets_data_hub" / "data"
OUT_DIR = Path(__file__).resolve().parent.parent / "frontend" / "public" / "data"


class _Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)


def _dump(obj, name):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(json.dumps(obj, cls=_Encoder, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {path}  ({path.stat().st_size / 1024:.1f} KB)")


def build_cert():
    df = (
        pl.read_parquet(DATA_DIR / "rb_cert_auctions_result.parquet")
        .sort("Anbudsdag")
        .with_columns(
            (pl.col("Erbjuden_volym") - pl.col("Tilldelad_volym"))
            .round(1)
            .alias("Aterstaende"),
            (pl.col("Erbjuden_volym") - pl.col("Erbjuden_volym").shift(1))
            .round(1)
            .alias("delta_erbjuden"),
            (pl.col("Tilldelad_volym") - pl.col("Tilldelad_volym").shift(1))
            .round(1)
            .alias("delta_tilldelad"),
            (pl.col("Antal_bud") - pl.col("Antal_bud").shift(1)).alias("delta_antal_bud"),
        )
        .with_columns(
            (pl.col("Aterstaende") - pl.col("Aterstaende").shift(1))
            .round(1)
            .alias("delta_aterstaende"),
        )
    )

    row = df.row(-1, named=True)
    latest = {
        "erbjuden_volym": row["Erbjuden_volym"],
        "tilldelad_volym": row["Tilldelad_volym"],
        "aterstaende": row["Aterstaende"],
        "antal_bud": row["Antal_bud"],
        "delta_erbjuden": row["delta_erbjuden"],
        "delta_tilldelad": row["delta_tilldelad"],
        "delta_aterstaende": row["delta_aterstaende"],
        "delta_antal_bud": row["delta_antal_bud"],
    }

    # Hardcoded deposit requirement dates (matches notebook)
    deposit_dates = {
        date(2025, 10, 14): 40.055,
        date(2025, 10, 28): 40.055,
        date(2025, 11, 4): 40.055,
        date(2025, 11, 21): 40.055,
    }
    first_deposit = min(deposit_dates)

    timeseries = []
    for r in df.iter_rows(named=True):
        d = r["Anbudsdag"]
        ri = deposit_dates.get(d)
        if ri is None and d >= first_deposit:
            ri = 40.055  # forward-fill
        timeseries.append(
            {
                "date": d.isoformat() if isinstance(d, date) else str(d),
                "erbjuden_volym": r["Erbjuden_volym"],
                "aterstaende": r["Aterstaende"],
                "rantefri_inlaning": ri,
            }
        )

    _dump({"latest": latest, "timeseries": timeseries}, "cert_data.json")


def build_bonds():
    ref_cols = [
        "Instrument/Marknad",
        "ISIN",
    ]
    ref = pl.read_excel(DATA_DIR / "ref_rgk.xlsx", columns=ref_cols)

    df = (
        pl.read_parquet(DATA_DIR / "sales_of_government_bonds.parquet")
        .join(ref, left_on="Isin", right_on="ISIN")
        .sort("Anbudsdag", "Isin")
    )

    # 30E/360 remaining maturity
    df = df.with_columns(
        pl.col("Anbudsdag").dt.year().alias("_y1"),
        pl.col("Anbudsdag").dt.month().alias("_m1"),
        pl.col("Anbudsdag").dt.day().alias("_d1"),
        pl.col("Forfallodag").cast(pl.Date).dt.year().alias("_y2"),
        pl.col("Forfallodag").cast(pl.Date).dt.month().alias("_m2"),
        pl.col("Forfallodag").cast(pl.Date).dt.day().alias("_d2"),
    ).with_columns(
        (
            (pl.col("_y2") - pl.col("_y1")) * 360
            + (pl.col("_m2") - pl.col("_m1")) * 30
            + pl.min_horizontal(pl.col("_d2"), pl.lit(30))
            - pl.min_horizontal(pl.col("_d1"), pl.lit(30))
        ).alias("_days")
    ).with_columns(
        (pl.col("_days") / 360).round(2).alias("lopetid"),
        (pl.col("Budvolym") / pl.col("Tilldelad_volym")).round(2).alias("bid_to_cover"),
    ).filter(pl.col("Tilldelad_volym") > 0)

    def _to_list(sub):
        return [
            {
                "date": r["Anbudsdag"].isoformat() if isinstance(r["Anbudsdag"], date) else str(r["Anbudsdag"]),
                "lan": r["Lan"],
                "bid_to_cover": r["bid_to_cover"],
                "budvolym": r["Budvolym"],
                "tilldelad": r["Tilldelad_volym"],
                "lopetid": r["lopetid"],
            }
            for r in sub.iter_rows(named=True)
        ]

    _dump(
        {
            "sgb": _to_list(df.filter(pl.col("Instrument/Marknad") == "SGB")),
            "sgb_il": _to_list(df.filter(pl.col("Instrument/Marknad") == "SGB IL")),
        },
        "bonds_data.json",
    )


def build_swestr():
    df_swestr = pl.read_parquet(DATA_DIR / "swestr_values.parquet")
    df_policy = pl.read_parquet(DATA_DIR / "policy_rate_values.parquet")

    # Exclude last day of December each year
    cut = (
        df_swestr.filter(pl.col("date").dt.month() == 12)
        .group_by(pl.col("date").dt.year())
        .agg(pl.col("date").max().alias("last_dec"))
        .select("last_dec")
    )
    df = (
        df_swestr.filter(~pl.col("date").is_in(cut["last_dec"].implode()))
        .join(df_policy, on="date")
        .rename({"value": "policy_rate"})
        .with_columns((pl.col("rate") - pl.col("policy_rate")).round(4).alias("diff"))
        .sort("date")
    )

    last = df.tail(1).row(0, named=True)
    latest = {
        "rate": last["rate"],
        "volume": last.get("volume"),
        "transactions": last.get("numberOfTransactions"),
        "agents": last.get("numberOfAgents"),
    }

    timeseries = [
        {
            "date": r["date"].isoformat() if isinstance(r["date"], date) else str(r["date"]),
            "rate": r["rate"],
            "policy_rate": r["policy_rate"],
            "diff": r["diff"],
        }
        for r in df.iter_rows(named=True)
    ]

    # Monthly data for latest month
    latest_date = df.tail(1)["date"][0]
    monthly_df = df.filter(
        (pl.col("date").dt.year() == latest_date.year)
        & (pl.col("date").dt.month() == latest_date.month)
    ).select(["date", "rate", "pctl12_5", "pctl87_5"])

    monthly = [
        {
            "date": r["date"].isoformat() if isinstance(r["date"], date) else str(r["date"]),
            "rate": r["rate"],
            "pctl12_5": r["pctl12_5"],
            "pctl87_5": r["pctl87_5"],
            "band": round(r["pctl87_5"] - r["pctl12_5"], 4) if r["pctl87_5"] and r["pctl12_5"] else None,
        }
        for r in monthly_df.iter_rows(named=True)
    ]

    _dump({"latest": latest, "timeseries": timeseries, "monthly": monthly}, "swestr_data.json")


def build_scb_rates():
    """Build SCB interest-rate data: mortgage rates, deposit rates, and NFC lending rates."""
    df_policy = pl.read_parquet(DATA_DIR / "policy_rate_values.parquet")

    # --- Mortgage rates ---
    df_mortgage = (
        pl.read_parquet(DATA_DIR / "mortgage_rates.parquet")
        .filter(
            (pl.col("Referenssektor") == "MFI")
            & (pl.col("Avtal") == "nya och omförhandlade avtal")
            & pl.col("Rantebindningstid").is_in([
                "T.o.m. 3 månader (rörligt)",
                "Över 3 månader - 1 år",
                "Över ett till fem år (1-5 år)",
                "Över fem år",
            ])
        )
        .select(["Rantebindningstid", "Tid", "value"])
        .with_columns(
            pl.col("Tid").str.replace("M", "-").str.to_date("%Y-%m")
        )
        .rename({"Tid": "date", "Rantebindningstid": "rate"})
    )

    # --- Deposit rates ---
    df_deposit = (
        pl.read_parquet(DATA_DIR / "deposit_rates.parquet")
        .filter(
            (pl.col("Avtal") == "nya och omförhandlade avtal")
            & pl.col("Rantebindningstid").is_in([
                "2 Med villkor",
                "3 Avistakonton",
            ])
        )
        .select(["Rantebindningstid", "Tid", "value"])
        .with_columns(
            pl.col("Tid").str.replace("M", "-").str.to_date("%Y-%m"),
            pl.col("Rantebindningstid").str.replace(r"^\d+\s*", ""),
        )
        .rename({"Tid": "date", "Rantebindningstid": "rate"})
    )

    # --- Policy rate as a line ---
    df_rates = (
        df_policy
        .with_columns(pl.lit("Styrränta").alias("rate"))
        .select(["rate", "date", "value"])
    )
    df_rates = pl.concat([df_rates, df_mortgage, df_deposit]).filter(
        pl.col("date") >= date(2006, 1, 1)
    )

    household_rates = [
        {
            "date": r["date"].isoformat() if isinstance(r["date"], date) else str(r["date"]),
            "rate": r["rate"],
            "value": r["value"],
        }
        for r in df_rates.sort("date", "rate").iter_rows(named=True)
    ]

    # --- NFC lending rates ---
    df_nfc = (
        pl.read_parquet(DATA_DIR / "nfc_lending_rates.parquet")
        .with_columns(
            pl.col("Tid").str.replace("M", "-").str.to_date("%Y-%m"),
            pl.col("BranschKrita", "FtgStrlKrita", "UrspRant", "AterRant")
            .str.replace(r"^\d+\.\s*", "")
            .str.replace(r"^\d+\s*", ""),
        )
        .filter(
            pl.col("value").is_not_null()
            & (pl.col("BranschKrita") != "Totalt, samtliga brancher")
            & (pl.col("FtgStrlKrita") != "Totalt, samtliga företagsstorlekar")
        )
    )

    MEDEL = "Ränta, medel, utestående lån i SEK per låntagare, procent"
    nfc_rates = [
        {
            "date": r["Tid"].isoformat() if isinstance(r["Tid"], date) else str(r["Tid"]),
            "branch": r["BranschKrita"],
            "size": r["FtgStrlKrita"],
            "measure": r["ContentsCode"],
            "value": r["value"],
        }
        for r in df_nfc.filter(
            (pl.col("BranschKrita") != "Bostadsrättsföreningar")
            & (pl.col("ContentsCode") == MEDEL)
        ).sort("Tid", "BranschKrita").iter_rows(named=True)
    ]

    # BRF subset
    MEDIAN = "Ränta, median, utestående lån i SEK per låntagare, procent"
    brf_rates = [
        {
            "date": r["Tid"].isoformat() if isinstance(r["Tid"], date) else str(r["Tid"]),
            "size": r["FtgStrlKrita"],
            "measure": r["ContentsCode"],
            "value": r["value"],
        }
        for r in df_nfc.filter(
            (pl.col("BranschKrita") == "Bostadsrättsföreningar")
            & pl.col("ContentsCode").is_in([MEDEL, MEDIAN])
        ).sort("Tid", "FtgStrlKrita").iter_rows(named=True)
    ]

    _dump(
        {
            "household_rates": household_rates,
            "nfc_rates": nfc_rates,
            "brf_rates": brf_rates,
        },
        "scb_rates_data.json",
    )


if __name__ == "__main__":
    print("Building frontend data...")
    build_cert()
    build_bonds()
    build_swestr()
    build_scb_rates()
    print("Done.")

"""Assets."""

from ..utils.functions import (
    scrape_rb_cert_auctions,
    transform_record, 
    scrape_riksbank_auctions, 
    convert_record, 
    SwestrApiResource,
    SweaApiResource
)
from ..assets.schemas import (
    RbCertAuctionResult,
    AuctionResult,
    SwestrResult,
    PolicyRateResult
)

from dagster import AssetExecutionContext, MaterializeResult, asset
from pathlib import Path
import polars as pl

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


@asset(group_name="Market_operations")
def riksbank_certificate(context: AssetExecutionContext) -> MaterializeResult:
    """Riksbank certificates.

    Webscrapes auction results from Riksbank certificates.
    """
    data = scrape_rb_cert_auctions(limit=None)

    validated = []
    errors = []
    for r in data:
        try:
            mapped = transform_record(r)
            if mapped is None:
                continue
            validated.append(RbCertAuctionResult(**mapped))
        except Exception as e:
            errors.append({"raw": r, "error": str(e)})

    if errors:
        context.log.warning(f"{len(errors)} records could not be validated.")
        for err in errors[:3]:
            context.log.warning(str(err))

    df = pl.DataFrame([v.model_dump() for v in validated])

    output_path = DATA_DIR / "rb_cert_auctions_result.parquet"
    df.write_parquet(output_path)
    context.log.info(f"Writing {len(df)} rows to {output_path}")

    return MaterializeResult(
        metadata={
            "num_records": len(df),
            "path": str(output_path),
        }
    )


@asset(group_name="Market_operations")
def sales_of_gov_bonds(context: AssetExecutionContext) -> MaterializeResult:
    """Sales of government bonds.

    Webscrapes auction results from sales of government bonds.
    """
    data = scrape_riksbank_auctions()

    validated = []
    errors = []
    for r in data:
        try:
            parsed = convert_record(r)
            validated.append(AuctionResult(**parsed))
        except Exception as e:
            errors.append({"raw": r, "error": str(e)})

    if errors:
        context.log.warning(f"{len(errors)} records could not be validated.")
        for err in errors[:3]:
            context.log.warning(str(err))

    df = pl.DataFrame([item.model_dump() for item in validated])

    output_path = DATA_DIR / "sales_of_government_bonds.parquet"
    df.write_parquet(output_path)
    context.log.info(f"Writing {len(df)} rows to {output_path}")

    return MaterializeResult(
        metadata={
            "num_records": len(df),
            "path": str(output_path),
        }
    )


@asset(group_name="Market_operations")
def get_swestr_values(context: AssetExecutionContext, swestr_api: SwestrApiResource) -> MaterializeResult:
    """Get SWESTR values.

    Collect SWESTR values from Swestr API.
    """
    result = swestr_api.get_swestr_rate(
        interest_rate_id="SWESTR",
        from_date="2020-01-01",
    )
    
    validated = [SwestrResult(**row) for row in result]
    
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
    
    output_path = DATA_DIR / "swestr_values.parquet"
    df.write_parquet(output_path)
    context.log.info(f"Writing {len(df)} rows to {output_path}")

    return MaterializeResult(
        metadata={
            "num_records": len(df),
            "path": str(output_path),
        }
    )


@asset(group_name="Market_operations")
def get_policy_rate_values(context: AssetExecutionContext, swea_api: SweaApiResource) -> MaterializeResult:
    """Get policy rate values.

    Collect policy rate values values from Swea API.
    """
    result = swea_api.get_swea_series(
        series_id="SECBREPOEFF",
        from_date="1994-06-01",
    )
    
    validated = [PolicyRateResult(**row) for row in result]
    
    df = pl.DataFrame([r.model_dump() for r in validated])
    
    output_path = DATA_DIR / "policy_rate_values.parquet"
    df.write_parquet(output_path)
    context.log.info(f"Writing {len(df)} rows to {output_path}")

    return MaterializeResult(
        metadata={
            "num_records": len(df),
            "path": str(output_path),
        }
    )
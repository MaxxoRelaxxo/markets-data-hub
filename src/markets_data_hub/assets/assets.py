"""Assets."""

from ..utils.functions import scrape_rb_cert_auctions, transform_record
from ..assets.schemas import RbCertAuctionResult

import polars as pl

from dagster import AssetExecutionContext, MaterializeResult, asset
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


@asset(group_name="Market_operations")
def riksbank_certificate(context: AssetExecutionContext) -> MaterializeResult:
    """Riksbank certertificates.
    
    Webscapres auction results from Riksbank certertificates.
    """
    data = scrape_rb_cert_auctions(limit=0)
    
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
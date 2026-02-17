"""Assets."""

from utils.functions import scrape_rb_cert_auctions, transform_record
from assets.schemas import RbCertAuctionResult
import polars as pl
from dagster import AssetExecutionContext, MaterializeResult, MetadataValue, asset


@asset(group_name="marketoperations")
def riksbanks_certificate(context: AssetExecutionContext) -> MaterializeResult:
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
        print(f"{len(errors)} poster kunde inte valideras")
        for err in errors[:3]:
            print(err)

    df = pl.DataFrame([v.model_dump() for v in validated])
    df.write_parquet("rb_cert_auctions_result.parquet")
    return MaterializeResult(
        metadata={
            "num_records": len(df),  # Metadata can be any key-value pair
            "preview": MetadataValue.md(str(df.head().to_markdown())),
            # The `MetadataValue` class has useful static methods to build Metadata
        }
    )
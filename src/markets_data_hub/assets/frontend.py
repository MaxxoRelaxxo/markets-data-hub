"""Frontend build asset – exports the Marimo notebook to static HTML."""

import subprocess
from pathlib import Path

from dagster import AssetExecutionContext, MaterializeResult, asset

NOTEBOOK_PATH = Path(__file__).resolve().parent.parent / "notebooks" / "analysis.py"
SITE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "site"
OUTPUT_PATH = SITE_DIR / "index.html"


@asset(
    group_name="Market_operations",
    deps=["riksbank_certificate", "sales_of_gov_bonds", "get_swestr_values", "get_policy_rate_values"],
)
def build_frontend(context: AssetExecutionContext) -> MaterializeResult:
    """Build static frontend.

    Exports the Marimo analysis notebook to a self-contained HTML file
    that can be deployed to GitHub Pages.
    """
    SITE_DIR.mkdir(exist_ok=True)

    # Determine the repo root (two levels above src/)
    repo_root = Path(__file__).resolve().parent.parent.parent.parent

    result = subprocess.run(
        [
            "marimo",
            "export",
            "html",
            str(NOTEBOOK_PATH),
            "-o",
            str(OUTPUT_PATH),
            "--no-include-code",
        ],
        cwd=str(repo_root),
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        context.log.error(f"marimo export failed:\n{result.stderr}")
        raise RuntimeError(f"marimo export failed with code {result.returncode}")

    context.log.info(f"Frontend exported to {OUTPUT_PATH}")
    file_size_kb = OUTPUT_PATH.stat().st_size / 1024

    return MaterializeResult(
        metadata={
            "path": str(OUTPUT_PATH),
            "size_kb": round(file_size_kb, 1),
        }
    )

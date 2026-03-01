"""Frontend build asset – converts data to JSON for the React frontend."""

import subprocess
import sys
from pathlib import Path

from dagster import AssetExecutionContext, MaterializeResult, asset

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BUILD_SCRIPT = REPO_ROOT / "scripts" / "build_data.py"


@asset(
    group_name="App",
    deps=[
        "riksbank_certificate",
        "sales_of_gov_bonds",
        "get_swestr_values",
        "get_policy_rate_values",
        "mortgage_rates",
        "deposit_rates",
        "nfc_lending_rates",
    ],
)
def build_frontend(context: AssetExecutionContext) -> MaterializeResult:
    """Build frontend data files.

    Converts Parquet data to JSON so the React frontend can consume it.
    The React build and GitHub Pages deploy are handled by GitHub Actions.
    """
    result = subprocess.run(
        [sys.executable, str(BUILD_SCRIPT)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        context.log.error(f"build_data.py failed:\n{result.stderr}")
        raise RuntimeError(f"build_data.py failed with code {result.returncode}")

    context.log.info(result.stdout)

    out_dir = REPO_ROOT / "frontend" / "public" / "data"
    json_files = list(out_dir.glob("*.json"))
    total_kb = sum(f.stat().st_size for f in json_files) / 1024

    return MaterializeResult(
        metadata={
            "json_files": len(json_files),
            "total_size_kb": round(total_kb, 1),
        }
    )

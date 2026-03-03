"""Sync Parquet data to GitHub so the Pages workflow can rebuild the frontend."""

import base64
from pathlib import Path

import requests
from dagster import AssetExecutionContext, ConfigurableResource, MaterializeResult, asset

DATA_DIR = Path(__file__).parent.parent / "data"

PARQUET_FILES = [
    "rb_cert_auctions_result.parquet",
    "sales_of_government_bonds.parquet",
    "swestr_values.parquet",
    "policy_rate_values.parquet",
    "mortgage_rates.parquet",
    "deposit_rates.parquet",
    "nfc_lending_rates.parquet",
]


class GitHubRepoResource(ConfigurableResource):
    """Push files to a GitHub repo via the Git Data API."""

    token: str
    owner: str
    repo: str
    branch: str = "main"

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
        }

    @property
    def _api(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}"

    def commit_files(self, files: dict[str, bytes], message: str) -> str | None:
        """Create an atomic commit with multiple file changes.

        Returns the new commit SHA, or None if nothing changed.
        """
        s = requests.Session()
        s.headers.update(self._headers)

        # 1. Current HEAD
        ref = s.get(f"{self._api}/git/ref/heads/{self.branch}", timeout=30)
        ref.raise_for_status()
        head_sha = ref.json()["object"]["sha"]

        # 2. Base tree from HEAD
        commit = s.get(f"{self._api}/git/commits/{head_sha}", timeout=30)
        commit.raise_for_status()
        base_tree_sha = commit.json()["tree"]["sha"]

        # 3. Create blobs
        tree_items = []
        for path, content in files.items():
            blob = s.post(
                f"{self._api}/git/blobs",
                json={
                    "content": base64.b64encode(content).decode(),
                    "encoding": "base64",
                },
                timeout=60,
            )
            blob.raise_for_status()
            tree_items.append(
                {"path": path, "mode": "100644", "type": "blob", "sha": blob.json()["sha"]}
            )

        # 4. Create tree (merge with base)
        tree = s.post(
            f"{self._api}/git/trees",
            json={"base_tree": base_tree_sha, "tree": tree_items},
            timeout=30,
        )
        tree.raise_for_status()
        new_tree_sha = tree.json()["sha"]

        # No changes → skip commit
        if new_tree_sha == base_tree_sha:
            return None

        # 5. Create commit
        new_commit = s.post(
            f"{self._api}/git/commits",
            json={"message": message, "tree": new_tree_sha, "parents": [head_sha]},
            timeout=30,
        )
        new_commit.raise_for_status()
        new_sha = new_commit.json()["sha"]

        # 6. Fast-forward branch ref
        s.patch(
            f"{self._api}/git/refs/heads/{self.branch}",
            json={"sha": new_sha},
            timeout=30,
        ).raise_for_status()

        return new_sha


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
def sync_data_to_github(
    context: AssetExecutionContext,
    github_repo: GitHubRepoResource,
) -> MaterializeResult:
    """Push Parquet files to GitHub, triggering the Pages deploy pipeline.

    This asset runs after data assets have been materialised.  It reads
    all Parquet files from the local data directory and commits them to
    the repository via the GitHub API.  The push triggers the existing
    ``pages.yml`` workflow which rebuilds and deploys the frontend.
    """
    files: dict[str, bytes] = {}
    for name in PARQUET_FILES:
        path = DATA_DIR / name
        if path.exists():
            files[f"src/markets_data_hub/data/{name}"] = path.read_bytes()
        else:
            context.log.warning("Missing: %s", path)

    if not files:
        context.log.warning("No parquet files found.")
        return MaterializeResult(metadata={"files_synced": 0})

    sha = github_repo.commit_files(files, "chore: update market data")

    if sha is None:
        context.log.info("No data changes — skipping commit.")
        return MaterializeResult(metadata={"files_synced": 0, "status": "no_changes"})

    context.log.info("Committed %d files → %s", len(files), sha)
    return MaterializeResult(metadata={"files_synced": len(files), "commit_sha": sha})

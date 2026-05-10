"""Download KB assets from GitHub release on MCP server startup."""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

CACHE_DIR = Path(os.environ.get("KB_CACHE_DIR", "data"))


def _headers(token: str) -> dict:
    return {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}


def _asset_headers(token: str) -> dict:
    return {"Authorization": f"token {token}", "Accept": "application/octet-stream"}


async def download_release_assets(
    repo: str,
    token: str,
    assets: list[str] | None = None,
    tag: str = "latest",
) -> Path:
    """Download release assets from a GitHub repo.

    Checks for local files first — if all requested assets exist locally,
    skips the download entirely (useful for local dev/testing).

    Args:
        repo: GitHub repo in 'owner/name' format
        token: GitHub token with repo read access
        assets: List of asset filenames to download (default: all)
        tag: Release tag to download (default: 'latest')

    Returns:
        Path to the cache directory containing downloaded files.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # Skip download if all assets already exist locally
    if assets and all((CACHE_DIR / a).exists() for a in assets):
        return CACHE_DIR

    etag_file = CACHE_DIR / ".release_etag"

    async with httpx.AsyncClient(follow_redirects=True, timeout=120) as client:
        # Get release info
        url = f"https://api.github.com/repos/{repo}/releases/tags/{tag}"
        resp = await client.get(url, headers=_headers(token))
        resp.raise_for_status()
        release = resp.json()

        # Check if we already have this version
        release_id = str(release["id"])
        if etag_file.exists() and etag_file.read_text().strip() == release_id:
            return CACHE_DIR

        # Download each asset
        for asset in release.get("assets", []):
            name = asset["name"]
            if assets and name not in assets:
                continue
            dl_url = asset["url"]
            resp = await client.get(dl_url, headers=_asset_headers(token))
            resp.raise_for_status()
            (CACHE_DIR / name).write_bytes(resp.content)

        # Save etag
        etag_file.write_text(release_id)

    return CACHE_DIR


def load_index(cache_dir: Path | None = None) -> dict:
    """Load index.json from cache."""
    path = (cache_dir or CACHE_DIR) / "index.json"
    return json.loads(path.read_text())


def load_embeddings(cache_dir: Path | None = None) -> list[dict]:
    """Load embeddings.json from cache."""
    path = (cache_dir or CACHE_DIR) / "embeddings.json"
    return json.loads(path.read_text()).get("entries", [])

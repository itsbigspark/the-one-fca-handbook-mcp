"""Fetch KB assets from a single base URI (raw git tree).

The URI points at a base path that the KB tree is served from. Defaults to
GitHub raw URL pointing at main branch. Override KB_URI to use a different
branch, fork, or git host (e.g. GitLab raw URL, self-hosted gitea, etc.).

Layout under the URI:
    {KB_URI}/data/index.json
    {KB_URI}/data/embeddings.json   # optional override via KB_EMBEDDINGS_URI
    {KB_URI}/data/<content paths>   # per-section files fetched via fetch_content

Auth: optional bearer token via the GIT_TOKEN env var, sent as "Authorization:
token <value>" — works for private GitHub repos and most self-hosted Git hosts.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx

CACHE_DIR = Path(os.environ.get("KB_CACHE_DIR", "data"))


def _headers(token: str) -> dict:
    return {"Authorization": f"token {token}"} if token else {}


async def ensure_assets(
    uri: str,
    embeddings_uri: str = "",
    token: str = "",
    assets: list[str] | None = None,
    cache_dir: Path | None = None,
) -> Path:
    """Ensure required KB assets exist locally, fetching from `uri` if missing.

    Args:
        uri: Base URI of the KB tree (e.g. raw GitHub URL pointing at a branch).
        embeddings_uri: Override URI for embeddings.json. If empty, defaults to
            ``{uri}/data/embeddings.json``. Useful for KBs whose embeddings.json
            is too large for git and is published as a release asset instead.
        token: Optional auth token for private repos.
        assets: Filenames to ensure (default: ``["index.json", "embeddings.json"]``).
        cache_dir: Local cache directory (default: ``./data``).

    Returns:
        Path to the cache directory containing the assets.

    Notes:
        - Existing local files are kept; this function only fetches missing ones.
        - A 404 on embeddings.json is tolerated — callers fall back to keyword
          search when ``load_embeddings`` returns None.
    """
    cd = cache_dir or CACHE_DIR
    cd.mkdir(parents=True, exist_ok=True)
    assets = assets or ["index.json", "embeddings.json"]
    embeddings_url = embeddings_uri or f"{uri}/data/embeddings.json"

    async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
        for name in assets:
            target = cd / name
            if target.exists():
                continue
            asset_url = embeddings_url if name == "embeddings.json" else f"{uri}/data/{name}"
            resp = await client.get(asset_url, headers=_headers(token))
            if resp.status_code == 404 and name == "embeddings.json":
                # Embeddings missing — keyword-only fallback
                continue
            resp.raise_for_status()
            target.write_bytes(resp.content)

    return cd


async def fetch_content(
    uri: str,
    path: str,
    token: str = "",
    cache_dir: Path | None = None,
) -> str | None:
    """Fetch a single content file from ``{uri}/data/{path}`` (cached locally).

    Args:
        uri: Base URI of the KB tree.
        path: Relative path within the KB's data dir (e.g. ``"handbook/CRR/section.md"``).
        token: Optional auth token.
        cache_dir: Local cache directory.

    Returns:
        File contents as text, or None if the resource returned 404.
    """
    cd = cache_dir or CACHE_DIR
    local = cd / path
    if local.exists():
        return local.read_text()

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        resp = await client.get(f"{uri}/data/{path}", headers=_headers(token))
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        local.parent.mkdir(parents=True, exist_ok=True)
        local.write_text(resp.text)
        return resp.text


def load_index(cache_dir: Path | None = None) -> dict:
    """Load index.json from cache. Returns ``{"entries": []}`` if missing."""
    path = (cache_dir or CACHE_DIR) / "index.json"
    if not path.exists():
        return {"entries": []}
    return json.loads(path.read_text())


def load_embeddings(cache_dir: Path | None = None) -> list[dict] | None:
    """Load embeddings entries from cache. Returns None if missing (keyword-only fallback)."""
    path = (cache_dir or CACHE_DIR) / "embeddings.json"
    if not path.exists():
        return None
    return json.loads(path.read_text()).get("entries", [])

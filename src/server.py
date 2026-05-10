"""FCA Handbook MCP server — hybrid semantic + keyword search, falls back to keyword-only."""

from __future__ import annotations

import json
import math
import os
import re

import httpx
from mcp.server.fastmcp import FastMCP

from src.kb_assets import download_release_assets, load_embeddings, load_index

PORT = int(os.environ.get("FCA_HANDBOOK_PORT", "4103"))
GIT_TOKEN = os.environ.get("FCA_HANDBOOK_GIT_TOKEN", "")
KB_REPO = os.environ.get("FCA_HANDBOOK_KB_REPO", "itsbigspark/the-one-fca-handbook-kb")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
EMBEDDING_MODEL = "text-embedding-3-small"

mcp = FastMCP(
    "FCA Handbook",
    instructions="FCA Handbook knowledge base — browse sourcebooks, chapters, sections and search regulatory content",
    host="0.0.0.0",
    port=PORT,
)

STOPWORDS = frozenset(["a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have", "in", "is", "it", "its", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with"])

_index_cache: dict | None = None
_embeddings_cache: list[dict] | None = None
_assets_ready = False


async def _ensure_assets():
    global _index_cache, _embeddings_cache, _assets_ready
    if _assets_ready:
        return
    await download_release_assets(
        repo=KB_REPO,
        token=GIT_TOKEN,
        assets=["index.json", "embeddings.json"],
    )
    _index_cache = load_index()
    try:
        _embeddings_cache = load_embeddings()
    except Exception:
        _embeddings_cache = None
    _assets_ready = True


def _cosine_sim(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


async def _embed_query(query: str) -> list[float] | None:
    if not OPENAI_API_KEY:
        return None
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"input": query, "model": EMBEDDING_MODEL},
            timeout=30,
        )
        if resp.status_code != 200:
            return None
        return resp.json()["data"][0]["embedding"]


async def _keyword_search(query: str, max_results: int) -> list[tuple[float, dict]]:
    await _ensure_assets()
    query_terms = set(re.findall(r"[a-z]{3,}", query.lower())) - STOPWORDS
    if not query_terms:
        return []
    scored = []
    for entry in _index_cache.get("entries", []):
        matches = query_terms & set(entry.get("keywords", []))
        if matches:
            scored.append((len(matches) / len(query_terms), entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:max_results]


async def _semantic_search(query: str, max_results: int) -> list[tuple[float, dict]]:
    await _ensure_assets()
    if not _embeddings_cache:
        return []
    query_vec = await _embed_query(query)
    if not query_vec:
        return []
    path_to_entry = {e["path"]: e for e in _index_cache.get("entries", [])}
    scored = []
    for emb in _embeddings_cache:
        sim = _cosine_sim(query_vec, emb["vector"])
        entry = path_to_entry.get(emb["path"])
        if entry and sim > 0.3:
            scored.append((sim, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[:max_results]


async def _hybrid_search(query: str, max_results: int = 10) -> list[dict]:
    kw_results = await _keyword_search(query, max_results * 2)
    sem_results = await _semantic_search(query, max_results * 2)
    if not sem_results:
        return [entry for _, entry in kw_results[:max_results]]
    scores: dict[str, tuple[float, dict]] = {}
    for score, entry in kw_results:
        scores[entry["path"]] = (0.4 * score, entry)
    for score, entry in sem_results:
        path = entry["path"]
        existing = scores.get(path, (0.0, entry))
        scores[path] = (existing[0] + 0.6 * score, entry)
    ranked = sorted(scores.values(), key=lambda x: x[0], reverse=True)
    return [entry for _, entry in ranked[:max_results]]


@mcp.tool()
async def list_sourcebooks() -> str:
    """List all available FCA Handbook sourcebooks (e.g., PRIN, COBS, SYSC)."""
    await _ensure_assets()
    sourcebooks = sorted(set(e["sourcebook"] for e in _index_cache.get("entries", []) if e.get("sourcebook")))
    return json.dumps({"sourcebooks": sourcebooks})


@mcp.tool()
async def list_chapters(sourcebook: str) -> str:
    """List all chapters within a sourcebook."""
    await _ensure_assets()
    chapters = sorted(set(e["chapter"] for e in _index_cache.get("entries", []) if e.get("sourcebook") == sourcebook))
    if not chapters:
        return json.dumps({"error": f"No chapters found for '{sourcebook}'"})
    return json.dumps({"sourcebook": sourcebook, "chapters": chapters})


@mcp.tool()
async def search_handbook(query: str, max_results: int = 10) -> str:
    """Search the FCA Handbook using hybrid semantic + keyword search."""
    results = await _hybrid_search(query, max_results)
    if not results:
        return json.dumps({"query": query, "results": []})
    return json.dumps({
        "query": query,
        "results": [{"path": e["path"], "title": e["title"], "sourcebook": e.get("sourcebook", ""), "chapter": e.get("chapter", "")} for e in results],
    })


def run() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    run()

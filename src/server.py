"""FCA Handbook MCP server — hybrid semantic + keyword search, falls back to keyword-only."""

from __future__ import annotations

import json
import math
import os
import re

import httpx
from mcp.server.fastmcp import FastMCP

from src.kb_assets import ensure_assets, fetch_content, load_embeddings, load_index

PORT = int(os.environ.get("FCA_HANDBOOK_PORT", "4103"))
GIT_TOKEN = os.environ.get("FCA_HANDBOOK_GIT_TOKEN", "")
KB_URI = os.environ.get(
    "FCA_HANDBOOK_KB_URI",
    "https://raw.githubusercontent.com/itsbigspark/the-one-fca-handbook-kb/main",
)
KB_EMBEDDINGS_URI = os.environ.get(
    "FCA_HANDBOOK_KB_EMBEDDINGS_URI",
    "https://github.com/itsbigspark/the-one-fca-handbook-kb/releases/latest/download/embeddings.json",
)
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
    await ensure_assets(
        uri=KB_URI,
        embeddings_uri=KB_EMBEDDINGS_URI,
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
    """List FCA Handbook sourcebooks (PRIN, COBS, SYSC, etc.)."""
    await _ensure_assets()
    sourcebooks = sorted(set(e["sourcebook"] for e in _index_cache.get("entries", []) if e.get("sourcebook")))
    return json.dumps({"sourcebooks": sourcebooks})


@mcp.tool()
async def list_chapters(sourcebook: str) -> str:
    """List chapters within a sourcebook."""
    await _ensure_assets()
    chapters = sorted(set(e["chapter"] for e in _index_cache.get("entries", []) if e.get("sourcebook") == sourcebook))
    if not chapters:
        return json.dumps({"error": f"No chapters found for '{sourcebook}'"})
    return json.dumps({"sourcebook": sourcebook, "chapters": chapters})


@mcp.tool()
async def search_handbook(query: str, max_results: int = 10) -> str:
    """Search FCA Handbook by keyword + semantic similarity."""
    results = await _hybrid_search(query, max_results)
    if not results:
        return json.dumps({"query": query, "results": []})
    return json.dumps({
        "query": query,
        "results": [{"path": e["path"], "title": e["title"], "sourcebook": e.get("sourcebook", ""), "chapter": e.get("chapter", "")} for e in results],
    })


@mcp.tool()
async def get_handbook_section(path: str) -> str:
    """Fetch FCA Handbook section content by path."""
    from pathlib import Path as P
    # Strip .md if user provided a path-like string ending in /
    path = path.strip()
    base = P("data") / "handbook" / path
    # Caller may have given a chapter directory rather than a section file
    if base.is_dir():
        await _ensure_assets()
        sections = []
        if _index_cache:
            for entry in _index_cache.get("entries", []):
                if entry.get("path", "").startswith(path.rstrip("/") + "/"):
                    sections.append({"path": entry["path"], "title": entry.get("title", "")})
        return json.dumps({
            "error": f"'{path}' is a chapter directory, not a section file.",
            "hint": "Pick one of the listed sections below and call get_handbook_section with its full path.",
            "sections": sections[:50],
        })
    # Add .md extension if missing
    if not path.endswith(".md"):
        path = path + ".md"
    f = P("data") / "handbook" / path
    if f.exists():
        return f.read_text()
    # Fallback: resolve display section number (e.g. "SUP/sup16/sup16s12.md" → actual ID)
    # The display number "16.12" doesn't match the API section ID "sup16s41"
    await _ensure_assets()
    import re
    # Extract chapter and section from the path: e.g. SUP/sup16/sup16s12.md
    m = re.search(r"/([a-z]+)(\d+[a-z]*)/[a-z]+\d+[a-z]*s(\d+[a-z]*)\.md$", path, re.IGNORECASE)
    if m and _index_cache:
        sourcebook_part = m.group(1).upper()  # 'SUP'
        chapter_num = m.group(2)              # '16'
        section_num = m.group(3)              # '12'
        display_num = f"{chapter_num}.{section_num}"
        # Find by title prefix like "SUP 16.12 "
        for entry in _index_cache.get("entries", []):
            if entry.get("title", "").startswith(f"{sourcebook_part} {display_num} "):
                resolved = P("data") / "handbook" / entry["path"]
                if resolved.exists():
                    return resolved.read_text()
    # Fetch from KB repo if not local
    text = await fetch_content(KB_URI, f"handbook/{path}", token=GIT_TOKEN)
    if text is not None:
        return text
    return f"Section not found: {path}"


def run() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    run()

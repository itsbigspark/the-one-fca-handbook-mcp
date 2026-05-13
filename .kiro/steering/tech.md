# Tech: FCA Handbook MCP Server

## Stack

| Layer | Choice |
|-------|--------|
| Language | Python 3.11+ |
| MCP Framework | `mcp[cli]` (FastMCP) |
| HTTP Server | uvicorn (via MCP streamable-http transport) |
| HTTP Client | httpx (fetching KB assets) |
| Testing | pytest + pytest-asyncio |
| Linting | ruff |
| Packaging | pyproject.toml (PEP 621) |

## Architecture

```
┌─────────────────────────────────────────┐
│  MCP Client (agent / broker)            │
└──────────────┬──────────────────────────┘
               │ streamable-http :4103
┌──────────────▼──────────────────────────┐
│  src/server.py  (FastMCP — 4 tools)     │
├─────────────────────────────────────────┤
│  src/kb_assets.py (fetch + cache KB)    │
└──────────────┬──────────────────────────┘
               │ HTTPS (GitHub raw / release)
┌──────────────▼──────────────────────────┐
│  the-one-fca-handbook-kb                │
│  (index.json, embeddings.json,          │
│   sourcebook markdown files)            │
└─────────────────────────────────────────┘
```

## Key Decisions

- **httpx for asset fetching** — Async-capable, used to pull KB JSON and content from GitHub
- **Lazy singleton loading** — KB assets loaded on first tool call, cached in `data/` dir
- **Hybrid search** — Cosine similarity on embeddings (60%) + keyword matching (40%); keyword-only fallback
- **Display-number resolution** — Section titles in index are matched to resolve human-readable paths (e.g. "SUP 16.12") to internal file IDs (e.g. `sup16s41`)
- **Dev symlink pattern** — `ln -sf ../the-one-fca-handbook-kb/data data` avoids network fetches during development
- **Embeddings via release asset** — `embeddings.json` is too large for git; served from GitHub release URL

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `FCA_HANDBOOK_KB_URI` | Yes | Base URI of the KB tree |
| `FCA_HANDBOOK_KB_EMBEDDINGS_URI` | No | Override for embeddings.json (default: GitHub release asset) |
| `FCA_HANDBOOK_GIT_TOKEN` | For private KBs | GitHub auth token |
| `OPENAI_API_KEY` | For semantic search | Query embedding |
| `FCA_HANDBOOK_PORT` | No (default 4103) | Server port |

## Running

```bash
make install   # .venv + deps
make run       # http://localhost:4103
make test      # pytest
make lint      # ruff check
```

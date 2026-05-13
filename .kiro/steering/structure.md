# Structure: FCA Handbook MCP Server

```
the-one-fca-handbook-mcp/
├── .kiro/
│   └── steering/
│       ├── product.md          # What and why
│       ├── tech.md             # How and with what
│       └── structure.md        # Where things live (this file)
├── src/
│   ├── __init__.py
│   ├── __main__.py             # Entry point (python -m src)
│   ├── server.py               # FastMCP tool definitions (4 tools)
│   └── kb_assets.py            # Fetch + cache KB assets from remote URI
├── tests/
│   └── __init__.py
├── scripts/
│   ├── scrape_drg.py           # DRG scraping utilities (research)
│   ├── scrape_drg_v3.py
│   ├── scrape_drg_all.py
│   ├── scrape_drg_explore.py
│   └── scrape_drg_full.py
├── resources/                  # Research docs and sample data
│   ├── business-statement.md
│   ├── requirements.md
│   ├── drg-research.md
│   ├── firm-input-analysis.md
│   ├── gaars-pattern-analysis.md
│   ├── firm_input_example.json
│   └── drg_samples/            # Sample DRG HTML pages
├── data/                       # KB asset cache (symlink in dev, fetched in prod)
│   ├── index.json              # Sourcebook/chapter/section metadata
│   ├── embeddings.json         # Pre-computed vectors (from release asset)
│   └── <sourcebook>/<chapter>/<section>.md  # Handbook content
├── .github/
│   └── workflows/              # CI
├── pyproject.toml              # Project metadata and dependencies
├── Makefile                    # Dev workflow automation
├── Dockerfile                  # Container build
├── .gitignore
└── README.md
```

## Module Responsibilities

### `src/server.py`
FastMCP tool registry. Defines 4 tools: `search_handbook`, `get_handbook_section`, `list_sourcebooks`, `list_chapters`. Handles lazy KB asset initialization, hybrid search logic, and display-number → API-ID path resolution.

### `src/kb_assets.py`
Asset fetcher and cache manager. Downloads `index.json` and `embeddings.json` from the configured KB URI. Caches to local `data/` directory. Supports auth via `FCA_HANDBOOK_GIT_TOKEN`. Shared module with fca-data-mcp.

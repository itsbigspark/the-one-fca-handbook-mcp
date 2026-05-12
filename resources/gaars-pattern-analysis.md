# GAARS Pattern — Analysis from `the-one-fca-handbook-kb`

## Pattern Summary

The KB repo follows a **scrape → store → index → embed → release** pipeline:

```
Source (FCA API)
    │
    ▼ scraper.py (httpx, delta detection via timestamp + SHA-256 hash)
    │
    ▼ store.py (markdown files on disk + metadata.json registry)
    │
    ▼ index.py (build index.json: path, title, sourcebook, chapter, keywords)
    │
    ▼ embed.py (OpenAI text-embedding-3-small, batch 100, → embeddings.json)
    │
    ▼ ontology.py (generate ontology.md from API tree + curated descriptions)
    │
    ▼ CI: GitHub Release (index.json + embeddings.json as release assets)
    │
    ▼ MCP Server (the-one-fca-handbook-mcp) downloads release assets on first request
```

## Key Design Patterns

### 1. Delta Detection (Two-Layer)
- **Fast path**: Compare `lastmodifieddate` from source against stored timestamp → skip if unchanged
- **Slow path**: Fetch content, compute SHA-256, compare against stored hash → skip if same

### 2. Store Pattern
- Content as markdown files: `data/handbook/{SOURCEBOOK}/{CHAPTER}/{SECTION}.md`
- Metadata registry: `data/metadata.json` — maps URL → {hash, path, last_modified}
- Scrape history: `data/scrape_history.json` — append-only metrics log

### 3. Index Pattern
- `data/index.json`: flat list of entries with path, title, hierarchy, keywords
- Keywords: top 50 significant words (3+ chars, stopwords removed)
- Title: extracted from first `# ` heading in markdown

### 4. Embeddings Pattern
- `data/embeddings.json`: entries with path + vector
- Input text: `"{title} — {keywords joined by space}"`
- Model: `text-embedding-3-small`
- Batch size: 100

### 5. Ontology Pattern
- `data/ontology.md`: human+AI readable navigational map
- Generated from API tree structure + curated descriptions dict
- Serves as "read this first" for AI consumers

### 6. Release Pattern (GAARS)
- CI builds index.json + embeddings.json
- Published as GitHub Release assets (tagged by version)
- MCP server downloads from release on first tool call
- Local files in `data/` skip download (dev mode)

## File Structure to Replicate

```
the-one-fca-data-kb/
├── src/
│   ├── __init__.py
│   ├── __main__.py          # Entry point for scraper
│   ├── scraper.py           # Fetch DRGs from RegData + SUP16 from handbook API
│   ├── store.py             # Store parsed DRG schemas + SUP16 rules as structured JSON/md
│   ├── index.py             # Build index.json (data items, fields, keywords)
│   ├── embed.py             # Generate embeddings for search
│   ├── ontology.py          # Build unified ontology (DRG fields → concepts)
│   └── config.py            # Env vars
├── data/
│   ├── drg/                 # Parsed DRG schemas (one JSON per data item)
│   ├── sup16/               # SUP 16 rules (markdown, like handbook pattern)
│   ├── metadata.json        # Delta detection registry
│   ├── index.json           # Search index
│   ├── embeddings.json      # Vector embeddings
│   └── ontology.json        # Unified field ontology
├── tests/
├── pyproject.toml
├── Makefile
├── Dockerfile
├── .github/workflows/ci.yml
└── README.md
```

## What Changes for the Data KB

| Aspect | Handbook KB | Data KB |
|--------|-------------|---------|
| Source | FCA Handbook JSON API | RegData DRGs (XSD/Excel) + Handbook API (SUP 16) |
| Content format | Markdown (prose) | Structured JSON (schemas, fields, validations) |
| Scraper | HTTP API calls | Playwright (RegData SPA) + HTTP API (SUP 16) |
| Index entries | Sections with keywords | Data items + individual fields |
| Ontology | Sourcebook navigation map | Field-to-concept mapping across data items |
| Delta detection | Timestamp + hash on markdown | Version number on DRGs + hash on parsed output |

## Makefile Targets to Replicate

```makefile
make install          # .venv + deps
make scrape-drg       # Fetch/parse DRG schemas from RegData
make scrape-sup16     # Fetch SUP 16 rules from handbook API
make build-index      # Build index.json
make build-embeddings # Generate embeddings
make build-ontology   # Build unified ontology
make test             # pytest
make clean            # Remove .venv/caches
```

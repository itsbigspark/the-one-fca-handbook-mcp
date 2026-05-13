# Product: FCA Handbook MCP Server

## Purpose

An MCP server providing hybrid semantic + keyword search over the FCA Handbook knowledge base. Enables AI agents to navigate sourcebooks, chapters, and sections of the FCA regulatory handbook.

## Users

- AI agents performing regulatory research and compliance tasks
- The-one broker connecting handbook tools with register and data MCPs
- Regulatory reporting agents needing handbook section content

## Key Capabilities

1. **Hybrid Search** — Semantic (60%) + keyword (40%) search across handbook content; keyword-only fallback when embeddings unavailable
2. **Section Retrieval** — Fetch full section content by path, with automatic display-number → API-ID resolution
3. **Sourcebook Navigation** — List available sourcebooks and their chapters
4. **Graceful Path Handling** — Directory paths return section listings; `.md` extension optional

## Design Principles

- **KB-backed** — Serves pre-built artefacts from the companion KB repo
- **Lazy asset loading** — Fetches index + embeddings on first request, caches locally
- **Smart path resolution** — Translates human-readable section numbers (SUP 16.12) to internal IDs (sup16s41)
- **Streamable HTTP transport** — Runs as standalone HTTP server on port 4103

## Non-Goals

- Not a handbook editor or submission tool
- No live FCA website scraping at runtime
- No authentication beyond network-level trust

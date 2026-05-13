# the-one-fca-handbook-mcp

FCA Handbook MCP server — hybrid semantic + keyword search over the knowledge base.

## Quick Start

```bash
make install    # Set up virtualenv
make run        # Start MCP server on port 4103
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `FCA_HANDBOOK_PORT` | Server port (default: 4103) |
| `FCA_HANDBOOK_KB_URI` | **Required.** Base URI of the KB tree, e.g. `https://raw.githubusercontent.com/itsbigspark/the-one-fca-handbook-kb/main`. Container fails to start if this is unset. Override to point at a different branch, fork, or git host (GitLab, gitea, etc.) |
| `FCA_HANDBOOK_KB_EMBEDDINGS_URI` | Override URI for `embeddings.json` (default: GitHub release asset — `embeddings.json` is too large for git). Set to your own URL to use a fork or alternate location |
| `FCA_HANDBOOK_GIT_TOKEN` | GitHub token with read access to the KB repo (required for private KB repos) |
| `OPENAI_API_KEY` | For semantic search query embedding |

## How It Works

1. On first request, fetches `index.json` and `embeddings.json` from `{KB_URI}/data/...` (override `KB_URI` to point at a different branch/host)
2. Cached locally on first fetch; subsequent requests are served from the cache
3. Serves hybrid search (semantic 60% + keyword 40%) over the content; falls back to keyword-only when embeddings are unavailable

## Tools

| Tool | Description |
|------|-------------|
| `search_handbook(query)` | Hybrid keyword + semantic search |
| `get_handbook_section(path)` | Fetch section content by path |
| `list_sourcebooks()` | List available sourcebooks |
| `list_chapters(sourcebook)` | List chapters within a sourcebook |

### Section path resolution

FCA Handbook section display numbers (e.g. "SUP 16.12") do **not** match the
API section IDs (e.g. `sup16s41`). The `get_handbook_section` tool handles this
automatically:

```
# Direct path (if you know the API section ID):
get_handbook_section("SUP/sup16/sup16s41.md")

# Display-number path (resolved via index title matching):
get_handbook_section("SUP/sup16/sup16s12.md")
→ resolves to sup16s41.md ("SUP 16.12 Integrated Regulatory Reporting")
```

The `.md` extension is optional — it will be added if missing.

If a chapter directory is passed instead of a section file (e.g.
`SUP/sup16` rather than `SUP/sup16/sup16s41.md`), the tool returns a
JSON listing of the available sections in that chapter rather than
crashing with `IsADirectoryError`. This helps the calling agent recover
from a confused tool call.

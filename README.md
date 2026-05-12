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
| `FCA_HANDBOOK_GIT_TOKEN` | GitHub token for downloading KB release assets |
| `FCA_HANDBOOK_KB_REPO` | KB repo (default: itsbigspark/the-one-fca-handbook-kb) |
| `OPENAI_API_KEY` | For semantic search query embedding |

## How It Works

1. On first request, downloads `index.json` + `embeddings.json` from the KB repo's latest GitHub release
2. If local files already exist in `data/`, uses those directly (for local dev)
3. Serves hybrid search (semantic 60% + keyword 40%) over the content

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

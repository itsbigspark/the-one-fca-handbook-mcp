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

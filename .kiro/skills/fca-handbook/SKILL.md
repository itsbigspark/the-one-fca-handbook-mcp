---
name: fca-handbook
description: How to use the FCA Handbook MCP server. Use when answering questions about UK financial regulation, FCA rules, or consumer protection principles.
---

# FCA Handbook MCP Server

## What This Serves

The FCA (Financial Conduct Authority) Handbook — the complete rulebook for UK financial services firms. Covers conduct, prudential requirements, consumer protection, and market integrity.

## Tools

1. **get_ontology()** — Read first. Returns a navigational map of all sourcebooks, what they cover, and who they apply to.
2. **get_system_prompt()** — Consumer-facing prompt for chatbot use.
3. **list_sourcebooks()** — List all 65 sourcebooks (PRIN, COBS, SYSC, etc.)
4. **list_chapters(sourcebook)** — List chapters within a sourcebook.
5. **get_section(reference)** — Get content by path e.g. `PRIN/prin2/prin2s1`
6. **search_handbook(query)** — Keyword search across all content.

## Workflow

1. Call `get_ontology()` to understand the structure
2. Use `search_handbook()` to find relevant sections
3. Use `get_section()` to read specific content

## Key Sourcebooks

- **PRIN** — The 12 Principles for Businesses (foundation of everything)
- **COBS** — Conduct of Business (how to treat customers)
- **SYSC** — Senior Management Arrangements (governance)
- **MCOB** — Mortgages and Home Finance
- **ICOBS** — Insurance Conduct of Business
- **CONC** — Consumer Credit

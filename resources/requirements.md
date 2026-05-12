# Demo Requirements — FCA Regulatory Reporting Modernisation

## Context

This demo is for FCA stakeholders. It shows how the FCA can move from web-form-based
data collection (XML/CSV uploads via RegData) to a modern, API-led, data-element-wise
collection system.

## Two Core Capabilities

### Capability 1: Determine a Firm's Reporting Obligations

**Source**: FCA Handbook SUP 16 (all of it, especially SUP 16.12 tables)
- URL: https://handbook.fca.org.uk/handbook/sup16

**Input**: Firm metadata from FCA's database (see `firm_input_json.json`)
- Firm characteristics / metadata
- Permissions & activities
- (Revenue can affect frequency but may not be in the input JSON)

**Output**:
- Which **data items** the firm must report
- At what **frequency** (quarterly, half-yearly, annually)
- Note: frequency can vary based on firm size/revenue thresholds

**Logic**: SUP 16.12 contains tables mapping firm categories to data items.
The rules use firm type, permissions, and activities to determine obligations.

### Capability 2: Unified Ontology of Data Elements

**Source**: FCA Data Reference Guides (DRGs)
- URL: https://regdata.fca.org.uk/#/layout/resources
- Format: XSD files and Excel spreadsheets
- Content: Field-level data requirements and validation rules per data item

**Process**:
1. Parse DRG schemas to extract data elements per data item
2. Map each data element to a standard ontology
3. Candidate standard: FIBO (https://spec.edmcouncil.org/fibo/)
4. Fallback: Create a bespoke ontology if FIBO doesn't fit

**Output**: A unified, extensible ontology where:
- Every data element from every data item is mapped to a concept
- Industry participants can understand the semantic meaning behind fields
- Data items are no longer isolated "datasets" but part of a connected graph

## Combined Outcome

Given a firm → determine obligations → for each data item → resolve to individual
data elements → collect via API at the element level.

Supports:
- **No-human-in-the-loop**: Fully automated collection via API
- **Human-submits-data**: Manual submission through the same API

## Key Sources

| Source | What It Provides |
|--------|-----------------|
| SUP 16 (Handbook) | Rules mapping firm characteristics → data items + frequency |
| DRGs (RegData) | XSD/Excel schemas defining fields within each data item |
| FIBO (EDM Council) | Candidate standard ontology for semantic mapping |
| Firm input JSON | Sample firm metadata from FCA's database |

## Open Questions

1. What does the firm input JSON look like? (file not yet received)
2. Which data items to include in the demo scope? (all, or a subset?)
3. Demo format: CLI? Web UI? MCP tools? Notebook?
4. Do we have access to download DRG XSDs programmatically?
5. FIBO coverage: does it cover regulatory reporting concepts sufficiently?

## FIBO Notes

- Published by EDM Council, standardised by OMG
- OWL-based ontology (machine-readable)
- Covers: business entities, financial instruments, contracts, indices, securities
- Mission explicitly mentions "improve efficiency in regulatory reporting"
- Available on GitHub: https://github.com/edmcouncil/fibo
- May need extension for FCA-specific regulatory reporting concepts

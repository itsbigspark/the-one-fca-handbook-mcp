# Firm Input JSON — Analysis

## Sample Firm: East Renfrewshire Credit Union Ltd (FRN 213761)

### Firm Classification Signals

| Field | Value | Significance for SUP 16 |
|-------|-------|------------------------|
| LegalStatusName | "Registered under I&PS Act 1965 and CU Act 1979" | **Credit Union** — specific reporting category in SUP 16.12 |
| FirmStatusName | "Authorised" | Active, must report |
| MifidClassification | "N" | Not MiFID — simpler reporting |
| ExemptBIPRUCommoditiesInd | false | Not exempt |
| ExemptCADFirmInd | false | Not CAD exempt |
| AnnualRegulatedRevenue | 0 | May affect frequency thresholds |
| NotForProfitInd | "N" | Not a not-for-profit |
| AccountingReferenceDate | "2004-09-30" | ARD = 30 September — determines reporting periods |

### Permissions & Activities (the key inputs for SUP 16 matching)

| # | Category | Activity | Investment Type |
|---|----------|----------|-----------------|
| 1 | Designated Investment Business | Advising on P2P agreements | — |
| 2 | Insurance Distribution | Arranging deals in investments | Non-investment insurance contracts |
| 3 | Insurance Distribution | Making arrangements for transactions | Non-investment insurance contracts |
| 4 | Insurance Distribution | Advising on investments | Non-investment insurance contracts |
| 5 | **Accepting deposits** | Accepting Deposits | Deposit |
| 6 | AIFMD | Management of AIFs | — |

### Group Memberships

- UK Consolidation group (active since 2017)
- Ring-fenced Group (expired 2021)

### Key Observations for SUP 16 Matching

1. **Credit Union with deposit-taking** — SUP 16.12 has specific tables for credit unions (likely SUP 16.12.5R or similar)
2. **Insurance distribution** — triggers insurance intermediary reporting (RMAR likely)
3. **AIFMD permission** — triggers AIFMD reporting requirements
4. **P2P advising** — may trigger specific P2P data items
5. **Revenue = 0** — likely means annual reporting frequency (not quarterly)

### Input Schema Summary

```
Firm Metadata
├── Identity (FRN, name, legal status, country)
├── Classification flags (BIPRU exempt, CAD exempt, MiFID, etc.)
├── Financial (AnnualRegulatedRevenue, AccountingReferenceDate)
├── Groups[] (consolidation, ring-fenced)
├── Permissions[]
│   ├── Status, Country, Directive, PassportDirection
│   └── Activity
│       ├── CategoryName (e.g. "Accepting deposits")
│       ├── ActivityTypeName (e.g. "Accepting Deposits")
│       ├── CustomerTypes[] (retail, professional, etc.)
│       └── InvestmentTypes[] (deposits, insurance, etc.)
├── Exemptions[]
├── Waivers[]
├── FirmLiquidity[]
└── FirmCRD[]
```

### What SUP 16 Needs to Determine

Given this input, the obligation engine must determine:
1. Which **firm category** this maps to in SUP 16.12 tables (e.g. "Credit union")
2. Which **data items** are required for that category
3. What **frequency** applies (annual vs quarterly vs half-yearly)
4. What **due dates** apply relative to the ARD
5. Whether any **exemptions or waivers** modify the obligations

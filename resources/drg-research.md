# FCA Data Reference Guides (DRGs) — Research Notes

## What Are DRGs?

Data Reference Guides are published by the FCA at https://regdata.fca.org.uk/#/layout/resources

They contain:
- **XML specifications** for each data item
- **Validation rules** applied to submissions
- **Field-level definitions** of every data element within each data item

They apply only to FCA data items (not PRA/COREP/FINREP).

## What Is RegData?

RegData is the FCA's data collection platform. Firms use it to:
- Submit regulatory data (web forms, XML/CSV upload, or web service)
- View their tailored reporting schedule
- View submission history
- Print data item forms

Access: https://myfca.fca.org.uk (Mon-Fri 7am-10pm, Sat-Sun 8am-5pm)

## Current Data Items (from FAQs page)

Examples of FSA-era data items still in use:
- **FSA001** — Balance sheet
- **FSA002** — Income statements
- **FSA015** — Sectoral information (credit quality)
- **FSA017** — Interest rate gap
- **FSA030** — Profit and loss account
- **FSA038** — Volumes and types of business (funds under management)
- **FSA039** — Client money and client assets
- **FSA040** — CFTC data (limited firms)

Recently removed: FSA006, FSA007, FSA018, FSA045

## Key Insight for the Demo

The DRGs at regdata.fca.org.uk define the **schema** (data elements) for each data item.
SUP 16 in the Handbook defines **which firms** must submit **which data items** and **when**.

The demo needs to bridge these two:
1. Given a firm's characteristics → SUP 16 tells us what they must report
2. Given a data item → DRG tells us what fields/elements are required
3. Combined → API can collect individual data elements rather than monolithic forms

## RegData Technical Submission Methods (Current)

1. Web form (manual entry in browser)
2. XML upload
3. CSV upload  
4. Web service submission (XBRL)

The proposed system replaces all of these with a unified API-led approach.

# Business Statement

## Problem

FCA requires an automated way to collect regulatory reporting data from regulated firms. This needs to support both:

1. **Fully automated** — "no-human-in-the-loop" collection
2. **Human-submits-data** — manual submission

...in a unified manner.

## Technical Problem (Two Parts)

### Part 1: Determine What a Firm Must Report

Use the FCA Handbook's **SUP 16** (Reporting Requirements) to determine what a certain regulated firm has to return to the FCA and when, using the firm's:
- Information (metadata / characteristics)
- Permissions & activities

### Part 2: Unified Ontology of Reporting Requirements

Use the FCA **Data Reference Guides (DRGs)** to create a unified ontology of reporting requirements by mapping the data elements within the data items defined by the DRGs.

Source: https://regdata.fca.org.uk/#/layout/resources

## Outcome

Together these enable the FCA to move beyond the current web-form based (XML/CSV uploads) data item collection to a **modern API-led, data-element-wise collection** of data — where ontology-mapped concepts/fields within relevant data items are collected individually rather than as monolithic form submissions.

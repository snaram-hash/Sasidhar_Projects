# ADR 004: Spatial-Aware Regex over Standard OCR Flattening

## Status
Accepted

## Context
Extracting data from Audited Financial Statements (PDFs) is difficult because the meaning of a number depends on its physical location (e.g., is this $10,000 under "Direct Expenses" or "Indirect Expenses"?).

## Decision
We will use PDF text extractors combined with Spatial-Aware Regular Expressions (capturing specific text blocks bounded by known headers) rather than flat text searching.

## Why We Chose It (Rationale)
Standard extraction (like `PyMuPDF` default text output) flattens the page, destroying the visual hierarchy. By designing regex that first captures the "Zone" (e.g., everything between "Purchases" and "Gross Profit"), we can accurately isolate and sum Direct Expenses, regardless of how many rows exist in that zone.

## Trade-offs
- High maintenance overhead if a CA firm submits a radically different accounting layout that lacks standard anchor keywords.

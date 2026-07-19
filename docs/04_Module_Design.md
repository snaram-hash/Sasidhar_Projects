# Module Design

The platform is divided into independent micro-services (Engines) to ensure high cohesion and loose coupling.

## 1. Financial Intelligence Engine
- **Responsibility:** Parses Audited Financials (P&L, Balance Sheet).
- **Key Feature:** Dynamically identifies Direct/Manufacturing Expenses vs. Indirect Expenses to correctly calculate Tangible Net Worth and Cost of Sales.

## 2. Banking Analytics Engine
- **Responsibility:** Parses multi-bank statements.
- **Key Feature:** Detects Inward/Outward Return (Bounce) rates and categorizes cash flows to flag diversion risks.

## 3. Tax & Bureau Engines (GST / CIBIL)
- **Responsibility:** Extracts monthly GST sales and credit bureau scores.
- **Key Feature:** Feeds data into the Reconciliation Service to verify that borrower-reported audited sales match government-filed GST sales.

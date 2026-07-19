# Database Design

CUIS utilizes a normalized relational schema to guarantee data integrity across the underwriting lifecycle.

## Core Tables
- `borrowers`: Stores entity metadata (Legal Name, PAN, Industry).
- `financial_statements`: Stores year-over-year balance sheet and P&L metrics.
- `bank_transactions`: Stores granular, line-by-line bank ledger entries for temporal cash-flow analysis.
- `risk_scores`: Stores the historical outputs of the Credit Policy Engine.
- `cam_records`: A materialized view / summary table used exclusively for generating the final Excel and Dashboard outputs.

## Technology Choice
For v1.0, the system uses **SQLite**. This ensures the platform is 100% portable and can run on an analyst's local machine without requiring cloud infrastructure. The database interface is abstracted, allowing a seamless migration to PostgreSQL in future cloud-hosted versions.

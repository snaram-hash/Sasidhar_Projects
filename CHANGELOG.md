# Changelog

All notable changes to the Credit Underwriting Intelligence Suite (CUIS) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to Semantic Versioning.

## [1.1.0] - Enterprise Portfolio Release
### Added
- **Dynamic 3-Year Historical Reconciliations:** Dashboard now computes and renders 3-year historical Balance Sheet summaries and Key Ratios (Current, D/E, Leverage, Margins).
- **Direct Expense Parsing:** Upgraded `FinancialParser` to extract granular manufacturing and operating expenses from Trading Accounts.
- **Capital Realignment:** Adjusted TNW calculations to strictly reflect Closing Capital + PAT across all fiscal years.
- **Premium UI Overhaul:** Upgraded dashboard CSS with glassmorphism, dynamic gradients, and modern Inter/Outfit typography.
- **Documentation Overhaul:** Implemented a massive 4-volume Engineering Book documenting business logic and architecture.

## [1.0.0] - Foundation Release
### Added
- SQLite database initialization (`db_manager.py`).
- Baseline Pydantic models for `Financial`, `Borrower`, and `Transaction`.
- Modular folder structure for Clean Architecture (`engines/`, `parsers/`, `services/`).
- Excel CAM Generation service integration.

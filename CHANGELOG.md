# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-07-17
### Added
- Initial repository structure and Python environment configurations.
- Centralized environment configuration loader (`settings.py`).
- SQLite database connection manager and empty table initializations (`db_manager.py`).
- Pydantic data models for Borrower, FinancialStatement, BankTransaction, CreditAssessment, RiskScore, and CAMRecord.
- Rotating file logging framework.
- Smoke tests configured via pytest.

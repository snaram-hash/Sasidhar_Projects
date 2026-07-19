# Testing Strategy

To ensure enterprise reliability, CUIS implements a multi-tiered testing strategy using `pytest`.

## 1. Unit Testing
- **Parsers:** Mocked PDF text strings are fed to the regex engines to ensure correct data extraction across edge cases (e.g., missing "Direct Expenses" headers).
- **Policy Engine:** Artificial `Financial` objects with extremely high leverage are passed to the engine to verify that the correct Risk Alerts are triggered.

## 2. Integration Testing
- Ensures the `Extraction Service` correctly writes to the SQLite database and that the `Reconciliation Service` can read and join those tables.

## 3. E2E (Smoke) Testing
- A full pipeline execution using a sample borrower (e.g., Harika Shipping) to verify that a valid Excel CAM and HTML dashboard are successfully written to the disk.

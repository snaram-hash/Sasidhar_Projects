# Risk Policy Engine

The Risk Policy Engine is the defining feature that elevates CUIS from a simple "PDF Extractor" to an "Intelligence Suite."

## Design Philosophy
Business logic must never live inside a UI or a data parser. The Risk Engine acts as a centralized brain that accepts reconciled facts and outputs deterministic decisions.

## Execution Flow
1. Receives a `cam_record` object from the database.
2. Passes the object through a series of configurable threshold checks:
   - *Is Current Ratio < 1.33?*
   - *Is Debt/Equity > 3.0?*
   - *Is the Bank Bounce Rate > 2%?*
3. Generates a list of explicit `Risk Alerts` and a final aggregated `Risk Score`.

Because these rules are isolated, Credit Risk Managers can update lending policies without breaking the underlying extraction algorithms.

# System Architecture

CUIS is built on **Clean Architecture** principles, strictly decoupling the parsing infrastructure, business rules, and presentation layers.

## High-Level Pipeline
1. **Ingestion Layer:** Raw documents (ITR, GST, Bank Statements, CIBIL) are fed into the system.
2. **Parsing Infrastructure:** Highly specialized, spatial-aware regex engines extract tabular and unstructured data.
3. **Intelligence Core:** Extracted data is saved to a central SQLite database. The Reconciliation Service harmonizes the data (e.g., cross-checking Audited Sales vs. GST Sales).
4. **Policy Engine:** The reconciled data is evaluated against configurable banking mandates.
5. **Presentation Layer:** The system generates a formatted Excel CAM and a self-contained HTML Dashboard.

*(See the main README for visual Mermaid diagrams of this flow).*

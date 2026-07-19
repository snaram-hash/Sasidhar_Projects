# Financial Intelligence Engine

## 🎯 Purpose
The Financial Intelligence Engine is responsible for extracting tabular and unstructured data from Audited Financial Statements (Income Tax Returns) and converting it into a standardized, mathematically verified Pydantic model (`Financial`).

## 📥 Inputs
- **Raw PDFs:** Multi-page scanned or digital Income Tax Returns (ITR-3, ITR-4, etc.)
- **Format:** Unstructured text with varying spatial tabular layouts.

## 📤 Outputs
- Reconciled `Financial` object containing exact figures for Sales, Cost of Sales, Gross Profit, Operating Expenses, PAT, Tangible Net Worth, and Working Capital components.

## 🏗️ Architecture
The engine relies on a custom **Layout-Aware Regex Parser**. Because accounting formats vary wildly across Chartered Accountants, we do not rely on fixed line numbers. 
Instead, we define "Anchor Zones" (e.g., the text block between "Purchases" and "Gross Profit") and apply targeted extraction rules only within those zones.

## ⚙️ Algorithms & Business Logic
**The Creditor Days Correction Algorithm:**
A common failure point in legacy underwriting is calculating Creditor Days based purely on "Raw Purchases". For service or logistics companies (e.g., Shipping), raw purchases are minimal, leading to distorted ratios.
Our engine dynamically scans for "Direct Expenses" (Vessel Charges, Godown Rents) and aggregates them into the Cost of Sales denominator, ensuring an accurate, bank-compliant working capital cycle calculation.

## 🔮 Future Improvements
- Integration with OCR for low-quality handwritten scans.
- Support for US-style GAAP financial layouts.

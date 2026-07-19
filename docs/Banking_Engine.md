# Banking Analytics Engine

## 🎯 Purpose
The Banking Analytics Engine processes vast amounts of unstructured bank statement data to identify cash flow patterns, diversion risks, and exact credit/debit summations.

## 📥 Inputs
- **Raw PDFs:** Multi-month Bank Statements (e.g., HDFC, ICICI, AU Bank).

## 📤 Outputs
- Structured `Transaction` models representing month-by-month cash flows, total credits, total debits, and flagged high-risk transactions.

## 🏗️ Architecture
The parser uses Python's PDF processing libraries to strip headers and footers from each page, isolating the transaction tables. It then applies line-by-line regex parsing to identify Dates, Narrations, and Withdrawal/Deposit amounts.

## ⚙️ Algorithms & Business Logic
**Inward/Outward Return (Bounce) Detection:**
The engine scans transaction narrations for keywords like "RTN", "BOUNCE", "REJECT", and "INSUFF FUNDS". It then automatically calculates the Bounce Rate (Bounces per 100 transactions) which is a critical metric for assessing immediate short-term liquidity risk.

## 🔮 Future Improvements
- Fuzzy matching to automatically identify top suppliers and buyers by grouping similar transaction narrations.
- ML-driven anomaly detection for sudden spikes in cash withdrawals.

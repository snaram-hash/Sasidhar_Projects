# Volume I: Business Domain

## Understanding Credit Underwriting

At its core, commercial credit underwriting is about answering one question: **"If the bank lends this company $1 Million, will they pay it back?"**

To answer this, underwriters rely on a standardized document called the **Credit Assessment Memo (CAM)**. The CAM aggregates data from multiple distinct sources to form a holistic picture of the borrower's financial health.

### The Problem with Manual Underwriting
1. **Data Silos:** Underwriters must look at Income Tax Returns (ITR), Goods & Services Tax (GST) filings, and Bank Statements.
2. **Time Consumption:** A typical SME borrower might submit a 30-page audited financial PDF, a 50-page bank statement, and 12 monthly GST returns. Extracting numbers from these PDFs and typing them into Excel takes hours.
3. **Complex Reconciliations:** Sales reported in the audited financials rarely match GST sales exactly. Discrepancies must be identified and explained.

## The Financial Ratios that Matter

CUIS automates the calculation of standard banking ratios:
* **Current Ratio (Current Assets / Current Liabilities):** Measures short-term liquidity. (Bank target: > 1.33)
* **Debt to Equity (Total Debt / Tangible Net Worth):** Measures leverage. High D/E means the business is running on borrowed money.
* **Working Capital Cycle (Debtor Days + Stock Days - Creditor Days):** Measures how long cash is tied up in operations.

### Harika Shipping Case Study
During the development of CUIS, we encountered a classic underwriting challenge with Harika Shipping & Logistics. The initial model calculated an absurdly high "Creditor Days" (19,000+ days) because it was dividing creditors by raw purchases (which were very low for a logistics company). 
By redesigning our `FinancialParser` to dynamically hunt for "Direct / Manufacturing Expenses" (like godown rents and vessel charges), we corrected the Cost of Sales denominator, bringing Creditor Days to a bank-compliant 107 Days.

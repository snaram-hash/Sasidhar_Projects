# Volume IV: Interview Guide

If you are an engineering manager or CTO reviewing this repository, here are some conversational starting points regarding the design of CUIS.

### Q: Why did you build this?
**A:** "In commercial lending, highly paid credit analysts spend days doing data entry from unstructured PDFs into Excel CAMs. I wanted to build a platform that automates the extraction, reconciliation, and output generation, cutting underwriting time from days to minutes while eliminating human error in complex ratio calculations."

### Q: How did you handle the messy reality of OCR and PDFs?
**A:** "PDF parsers like PyMuPDF return flattened text. But in accounting, spatial layout is everything. I built layout-aware Regex parsing logic. For example, to find 'Direct Expenses', I don't just search for the word; I capture the specific text block bounded by the 'Purchases' and 'Gross Profit' lines in the Trading Account, and then sum the values inside that block."

### Q: Why SQLite instead of a 'real' database?
**A:** "In version 1.0, the goal was rapid prototyping and extreme portability. A banker can pull this repository and run it locally without configuring a Dockerized PostgreSQL container. Because the application is built with Clean Architecture, swapping SQLite for Postgres is a 10-line configuration change in the `db_manager.py` file."

### Q: How does the Rule Engine work?
**A:** "Instead of embedding business logic in the UI or parsers, I created a central `policy_engine.py`. It takes the reconciled facts (from the database) and runs them through configurable thresholds. If the Current Ratio falls below 1.33, it flags an alert. This separation of concerns means business analysts can update lending policies without requiring a software developer to touch the core pipeline."

### Q: What was the hardest bug you solved?
**A:** "During testing on a logistics company, the Working Capital 'Creditor Days' gauge broke, showing 19,000+ days. I traced it back to the denominator: Cost of Sales. The parser was only extracting raw goods 'Purchases', which are near zero for a service company, ignoring millions in 'Vessel Charges' and 'Godown Rents'. I had to rewrite the parser to capture 'Manufacturing/Direct Expenses', which instantly realigned the calculations to the bank's audited standards."

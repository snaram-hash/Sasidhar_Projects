# Volume II: Enterprise Architecture

## Clean Architecture Principles

CUIS is not a script; it is a platform built using strict Clean Architecture principles. This ensures that the system is modular, testable, and highly scalable.

### Layer 1: Core Domain (Models)
The `models/` directory contains Pydantic schemas that define the absolute truth of our data. A `Financial` object looks the same whether it came from a high-quality digital PDF, a scanned image, or a manual API override.

### Layer 2: Parsers (Infrastructure)
The `parsers/` directory contains the messy logic of reading PDFs. We use `pdfplumber` and `PyPDF2` combined with spatial-aware Regular Expressions. 
* **Design Decision:** By isolating parsers, if the government changes the format of the GSTR-3B form tomorrow, we only need to update `gst_parser.py`. The rest of the application remains untouched.

### Layer 3: Services (Application Logic)
The `services/` directory orchestrates the flow. `extraction_service.py` is responsible for grabbing a PDF, passing it to the right Parser, and saving the result to the Database.

### Layer 4: Intelligence Engines
The `engines/` directory contains the `policy_engine.py`. 
* **Design Decision:** Instead of hardcoding `if debt_equity > 3.0: print("High Risk")` into the UI, we built a centralized Rule Engine. This allows Credit Risk Officers to dynamically configure risk thresholds across the entire portfolio without requiring a software developer to rewrite code.

## Why SQLite?
For an enterprise tool, why use SQLite instead of PostgreSQL or SQL Server? 
In v1.0, portability is key. CUIS needs to run on standard banker laptops without requiring Docker or a massive IT infrastructure setup. SQLite provides full ACID compliance and relational integrity while allowing the entire database to exist as a single `.db` file. Migration to PostgreSQL in v4.0 will be trivial due to our ORM-like schema definitions.

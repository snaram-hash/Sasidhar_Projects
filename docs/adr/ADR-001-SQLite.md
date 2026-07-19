# ADR 001: Use SQLite for v1.0 Data Storage

## Status
Accepted

## Context
The platform requires a relational database to store parsed financial records, bank transactions, and borrower metadata. 

## Decision
We will use SQLite as the primary database for version 1.0 of the platform.

## Why We Chose It (Rationale)
1. **Zero-Infrastructure Portability:** Credit analysts often work on highly secured banking laptops where installing Docker or a PostgreSQL server is blocked by IT. SQLite requires zero setup and lives entirely within a single `.db` file.
2. **ACID Compliance:** Unlike JSON or CSV storage, SQLite provides full relational integrity, which is mandatory for financial data.
3. **Migration Path:** Because we use an abstracted DB manager, migrating to PostgreSQL in the future will require minimal code changes.

## Trade-offs
- Lack of concurrent multi-user write support (acceptable for a single-user batch processing tool).

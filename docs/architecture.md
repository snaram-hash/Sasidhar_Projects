# CUIS Architecture Specification - Sprint 1

This document outlines the foundation layer architecture for the **Credit Underwriting Intelligence Suite (CUIS)**.

## Layer Structure

1. **Centralized Configuration Layer**: Managed by `config/settings.py` - controls environmental parameters and base folders.
2. **Data Model Layer**: Implemented via Pydantic v2 schemas in `models/` - guarantees type safety and strict schema validation for internal communication.
3. **Database Layer**: Managed by `database/db_manager.py` - uses SQLite for local relational storage, initializing 7 core tables with references and constraints.
4. **Utility Layer**: Holds helpers and core exceptions (like custom underwriting and document validation exceptions).
5. **Testing Layer**: Pytest framework configurations for smoke and unit test automation.

# ADR 002: Implement a Configurable Rule Engine over Machine Learning

## Status
Accepted

## Context
We need a mechanism to evaluate a borrower's financial health (e.g., working capital cycles, leverage) and output a risk assessment.

## Decision
We will build a deterministic, rules-based Credit Policy Engine rather than training a Machine Learning (ML) classification model.

## Why We Chose It (Rationale)
1. **Explainability & Auditability:** In commercial lending, regulatory bodies require banks to explicitly state *why* a loan was rejected. An ML black-box cannot easily provide legal justification. A rule engine (e.g., "Rejected because Current Ratio < 1.33") is 100% auditable.
2. **Configurability:** Business policies change frequently based on macroeconomic factors. A rule engine allows Risk Managers to update thresholds instantly without retraining a model.

## Trade-offs
- Inability to discover hidden, non-linear risk patterns that an ML model might identify.

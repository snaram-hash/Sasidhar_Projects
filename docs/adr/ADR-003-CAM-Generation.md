# ADR 003: Excel Injection via OpenPyXL

## Status
Accepted

## Context
The final output of the platform must be a Credit Assessment Memo (CAM) in Excel format. Bank templates contain highly complex cell merging, proprietary color themes, and embedded formulas.

## Decision
We will use `openpyxl` to open a pre-existing `CAM_Template.xlsx` and inject data into specific cell coordinates, rather than using `pandas.to_excel()` or `xlsxwriter` to build the file from scratch.

## Why We Chose It (Rationale)
Building complex banking templates programmatically is brittle and time-consuming. By injecting data into a blank template, we guarantee that the final output perfectly matches the Credit Committee's visual expectations. It also allows business users to update the visual design of the template without requiring code changes.

## Trade-offs
- The system is tightly coupled to the exact cell coordinates (e.g., `B44`) of the specific template version.

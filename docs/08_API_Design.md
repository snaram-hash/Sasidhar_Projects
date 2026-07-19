# API Design & Integrations

While v1.0 of CUIS operates as a local batch-processing pipeline, the architecture is designed to expose a RESTful API for v2.0 SaaS deployments.

## Proposed Endpoints
- `POST /api/v1/ingest`: Accepts multipart form-data (PDFs) and queues them for the Extraction Service.
- `GET /api/v1/borrowers/{id}/financials`: Retrieves the standardized financial model.
- `GET /api/v1/borrowers/{id}/risk-score`: Executes the Policy Engine and returns the JSON risk assessment.
- `GET /api/v1/borrowers/{id}/export/dashboard`: Returns the compiled HTML dashboard string.

This API-first design ensures CUIS can eventually integrate directly with core banking systems like Finacle or Flexcube.

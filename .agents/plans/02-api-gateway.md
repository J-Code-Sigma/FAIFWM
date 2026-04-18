# Plan: 02. API Gateway (FastAPI)

## Overview
Implement the API Gateway to handle event-driven ingestion, returning job IDs, and streaming status updates back to the React client.

## Tasks
- [ ] Initialize `FastAPI` application for the API Gateway.
- [ ] Create `POST /api/v1/encode` Endpoint:
  - Accept multipart `.wav` uploads.
  - Validate 44.1kHz and 16-bit/24-bit PCM format.
  - Save file reliably to local shared volume or S3/MinIO bucket.
  - Launch internal orchestration routing and respond immediately with a `Job_ID`.
- [ ] Create `GET /api/v1/stream/{job_id}` Endpoint:
  - Implement Server-Sent Events (SSE) using FastAPI's `StreamingResponse`.
  - Stream continuous PGD status to the React frontend.

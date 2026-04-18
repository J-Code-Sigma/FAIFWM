# FastAPI & SSE Best Practices

## Fast, Asynchronous Endpoints
- Since the PGD loop takes 5-15 minutes, **do not** block the FastAPI event loop. Ensure all heavy processing is offloaded to the gRPC GPU workers and never runs synchronous intensive tasks on the FastAPI application thread.
- Use `async def` endpoints carefully: only await on asynchronous I/O operations.

## Audio File Handling
- When accepting `multipart/form-data`, stream files chunk-by-chunk using `UploadFile.read(size)` directly into storage to prevent memory overflow on large audio files.
- Validate WAV headers quickly in the gateway, ensuring 44.1kHz 16-bit or 24-bit PCM format before accepting the payload.

## Server-Sent Events (SSE)
- Use standard `StreamingResponse` from FastAPI for SSE.
- Format all payloads strictly following the HTML5 SSE specification:
  ```text
  event: status_update
  data: {"job_id": "123", "current_step": 45, "loss": 0.12}
  ```
- Make sure exceptions or connection drops gracefully abort the stream and clear references so memory leaks do not occur over a 15-minute connection loop.

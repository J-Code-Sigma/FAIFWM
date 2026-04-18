from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import uuid
import logging
from typing import AsyncGenerator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="FAIFWM API Gateway", version="0.1.0")
security = HTTPBearer()

async def verify_supabase_jwt(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Middleware to verify Supabase JWT.
    TODO: Integrate PyJWT with Supabase project keys.
    """
    token = credentials.credentials
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # Stub: Return a mock user_id
    return "mock-user-id"

@app.post("/api/v1/encode")
async def encode_audio(file: UploadFile = File(...), user_id: str = Depends(verify_supabase_jwt)) -> dict[str, str]:
    """
    Receives multipart .wav upload, saves to Volume, and returns Job_ID.
    """
    if file.content_type not in ["audio/wav", "audio/x-wav"]:
        raise HTTPException(status_code=400, detail="Only .wav files are supported")
    
    job_id = str(uuid.uuid4())
    logger.info(f"[{job_id}] Received audio upload from {user_id}")
    
    # TODO: Write chunk-by-chunk to Shared Volume / S3
    
    # TODO: Launch gRPC request asynchronously
    
    return {"job_id": job_id, "status": "accepted"}

@app.get("/api/v1/stream/{job_id}")
async def stream_status(job_id: str) -> StreamingResponse:
    """
    Server-Sent Events endpoint to stream PGD loop status from gRPC worker.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        # TODO: Await responses from Gateway gRPC client broker
        yield f"data: {{\"job_id\": \"{job_id}\", \"status\": \"PENDING\"}}\n\n"
        
    return StreamingResponse(event_generator(), media_type="text/event-stream")

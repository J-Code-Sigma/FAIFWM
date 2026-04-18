import grpc
import logging
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

class OrchestrationClient:
    def __init__(self, target_host: str = "worker:50051", use_tls: bool = True):
        self.target_host = target_host
        self.use_tls = use_tls
        
    async def get_channel(self) -> grpc.aio.Channel: # type: ignore
        """
        Produce an async channel to the worker.
        """
        if self.use_tls:
            # TODO: Load real certs from a secure location
            credentials = grpc.ssl_channel_credentials()
            return grpc.aio.secure_channel(self.target_host, credentials)
        else:
            return grpc.aio.insecure_channel(self.target_host)

    async def trigger_protection(self, job_id: str, file_path: str, user_id: str) -> AsyncGenerator[dict, None]: # type: ignore
        """
        Calls ProtectAudio streaming RPC and yields dictionaries compatible with SSE.
        """
        channel = await self.get_channel()
        try:
            # TODO: Add protobuf compiled module bindings
            # stub = orchestration_pb2_grpc.OptimizationServiceStub(channel)
            # request = orchestration_pb2.ProtectionRequest(...)
            
            # async for response in stub.ProtectAudio(request):
            #    yield response_to_dict(response)
            
            logger.info(f"[{job_id}] Triggered gRPC workflow")
            yield {"status": "STUB"}
        finally:
            await channel.close()

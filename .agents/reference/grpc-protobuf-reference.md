# gRPC & Protobuf Best Practices

## Protobuf Standards
- Precompile all `*.proto` files using standard standard protobuf compilation tools (`grpcio-tools`). Keep the generated files cleanly separated in the project tree.
- The core payload for monitoring is the `OptimizationStatus` message. It should carry distinct scalar types and enums where advantageous.

## Server Streaming over gRPC
- Project Antigravity relies heavily on **Server Streaming**. The Gateway sends one request containing the path to the Wav file in the shared volume, and the GPU Worker responds with a stream of `OptimizationStatus` messages until completion.
- Ensure that the Python gRPC server is instantiated with the `asyncio` gRPC module (`grpc.aio`), preventing lockups of the PyTorch optimization loop or thread pool starvation.

## Resiliency
- Handle temporary internal network partitions between the API Gateway and the GPU Workers gracefully. Connect with `try...except grpc.RpcError` logic and implement realistic timeout bounds.

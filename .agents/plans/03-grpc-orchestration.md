# Plan: 03. gRPC Orchestration & Data Harvesting

## Overview
Implement internal heavy-compute routing from the API Gateway to distributed Linux GPU nodes using gRPC, and archive the resulting stems for future model training.

## Tasks
- [ ] Define `.proto` files for internal orchestration:
  - Include an `OptimizationStatus` message detailing `status`, `current_step`, and `loss_metrics`.
- [ ] Implement gRPC Server on the GPU Node(s):
  - Receive encoding task.
  - Start the PyTorch PGD loop and yield `OptimizationStatus` periodically (Server Streaming).
- [ ] Implement gRPC Client on the FastAPI Gateway:
  - Connect to the GPU worker asynchronously and broker event streams back to the SSE endpoints.
- [ ] Implement Data Harvesting Pipeline:
  - Upon completion, securely pair and archive `[Clean_Stem.wav]` with `[Protected_Stem.wav]`.
  - Ensure perfect alignment is maintained into an isolated directory for the future U-Net VST.

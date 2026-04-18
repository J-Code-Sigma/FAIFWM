# Product Requirements Document: FAIFWM (Backend)

## 1. Executive Summary
FAIFWM (Fuck AI Fucking With Music) is a distributed ML engine designed to proactively protect vocal stems from unauthorized AI voice cloning. By implementing the MMMC algorithm, FAIFWM injects imperceptible adversarial noise into audio payloads, disrupting the training and inference of cloning models like RVC and So-VITS. The backend operates outside of standard BaaS infrastructure to handle heavy compute and long-running execution times (5–15 minutes) required for Phase 1 Projected Gradient Descent (PGD).

## 2. Technical Architecture & Stack
* **Language/Framework:** Python 3.11+ (Dependency management via `uv`).
* **ML Core:** PyTorch 2.x, `torchaudio` (CUDA 12.8 support).
* **API Gateway:** FastAPI with Supabase JWT Auth Middleware.
* **Internal Comm:** gRPC (Server Streaming) with TLS encryption.
* **Client Streaming:** Server-Sent Events (SSE) for real-time progress.
* **Storage:** Local shared volumes for Dev; S3/MinIO for Prod.

## 3. Infrastructure & Environment Strategy
The system is designed to detect hardware at runtime and adjust execution strategy to balance speed and memory safety.

| Feature | Development (ROG Laptop) | Production (Dedicated Cloud) |
| :--- | :--- | :--- |
| **Primary GPU** | NVIDIA RTX 4060 (8GB VRAM) | NVIDIA RTX 3090/4090 (24GB VRAM) |
| **Precision** | `float32` | `bfloat16` (Speed Optimized) |
| **Execution** | **Chunked Mode:** 30s sliding windows | **Global Mode:** Full waveform tensor |
| **Networking** | Local Network / WSL2 | Dedicated Fiber / 1Gbps Symmetric |

## 4. Phase 1: Core Protection Engine (The "Shield")
The ML core executes adversarial noise generation directly on the raw waveform.

### 4.1. Adaptive VRAM Optimization
The Worker node implements an `AdaptiveShield` logic:
* **Low VRAM Mode (<12GB):** Automatically triggers a "Sliding Window" optimization to prevent `CUDA Out of Memory` errors on consumer-grade hardware.
* **High VRAM Mode (>=16GB):** Processes the entire 1D waveform globally to maximize adversarial consistency and eliminate stitching artifacts.

### 4.2. Multi-Objective Loss Specification
The backward pass computes a weighted loss to balance human intelligibility with AI disruption:
* **Reconstruction Loss ($L_r$, Weight 0.29):** Mean Squared Error between clean and protected stems.
* **Perceptual Loss ($L_p$, Weight 0.29):** Differentiable PESQ/STOI wrapper to maintain vocal quality.
* **Distortion Loss ($L_d$, Weight 0.02):** Inverted MSE against the surrogate clone output.
* **Opinion Loss ($L_o$, Weight 0.65):** DNSMOS predictor to force semantic degradation in AI models.

## 5. Phase 2: Distributed Event-Driven Architecture
Orchestrates the asynchronous routing of large audio payloads and real-time state updates.

### 5.1. File Ingestion & Gateway (FastAPI)
* **Endpoint:** `POST /api/v1/encode`
* **Security:** Validates Supabase JWT before writing to disk.
* **Flow:** Returns a `Job_ID` and hands off the file path to the Worker via gRPC.
* **Status:** `GET /api/v1/stream/{job_id}` initializes the SSE `StreamingResponse`.

### 5.2. Internal Orchestration (gRPC)
* **Protocol:** gRPC Server Streaming.
* **Worker Response:** Yields `OptimizationStatus` messages containing `current_step`, `total_steps`, and `loss_metrics`.
* **Gateway Role:** Translates gRPC messages into SSE JSON packets for the React frontend.

## 6. Phase 3 Preparation: Data Harvesting
Upon completion of the PGD loop, the worker node archives a 1:1 pairing of `[Clean_Stem.wav]` and `[Protected_Stem.wav]`.
* **Harvesting:** Automatically indexed by `User_ID` and `Timestamp`.
* **Future Utility:** This dataset provides the ground truth required to train the real-time U-Net VST/AU plugin (Phase 3).
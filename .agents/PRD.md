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

| Tier | Hardware Context | Execution Strategy | Role in Pipeline |
| :--- | :--- | :--- | :--- |
| **Development** | ROG Laptop (RTX 4060 - 8GB) | Chunked (30s windows), `float32` | Local API/ML core development. |
| **Staging/Harvester** | Bare Metal (RTX 3050 - 8GB) | Chunked (30s windows), `float32` | 24/7 continuous dataset harvesting and VRAM edge-case testing. |
| **Production** | Cloud Dedicated (RTX 3090 - 24GB) | Global (Full Waveform), `bfloat16` | Public-facing gRPC worker; high-speed artist fulfillment. |

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

### 5.2. Internal Orchestration & Client Streaming
* **Protocol:** gRPC Server Streaming between the Gateway and isolated GPU Workers.
* **Worker Response:** Yields `OptimizationStatus` messages containing `current_step`, `total_steps`, and `loss_metrics`.
* **Universal API Hand-off:** The Gateway translates gRPC messages into universal SSE JSON packets. This ensures real-time feedback is identical whether the request originates from the React Web Client or the FAIFWM Desktop App.

## 6. Phase 3 Preparation: The Data Flywheel
Upon completion of the PGD loop, the worker node archives a bit-perfect 1:1 pairing of `[Clean_Stem.wav]` and `[Protected_Stem.wav]`.
* **Harvesting:** Automatically indexed securely via `User_ID` and `Timestamp`.
* **Amortized Optimization:** This dataset provides the ground truth required to train a fast, predictive U-Net. 
* **The Endgame:** By training a lightweight inference model on this proprietary dataset, FAIFWM will eventually shift from a 15-minute cloud compute bottleneck to a 10-millisecond local desktop process, ensuring total data sovereignty for the artist.
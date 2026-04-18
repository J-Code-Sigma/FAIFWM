# Product Requirements Document: FAIFWM (Backend)

## 1. Executive Summary
FAIFWM (Fuck AI Fucking With Music) is a distributed ML engine designed to proactively protect vocal stems from unauthorized AI voice cloning. By implementing a clean-room MMMC algorithm, FAIFWM injects imperceptible adversarial noise into audio payloads, disrupting the training and inference of cloning models like RVC and So-VITS. It is a distributed machine learning engine and API gateway designed to proactively protect vocal stems against unauthorized AI voice cloning. Implementing a clean-room version of the "My Music My Choice" (MMMC) algorithm, the backend operates entirely outside of standard BaaS infrastructure to handle the heavy compute and long-running execution times (5–15 minutes) required for Phase 1 Projected Gradient Descent (PGD).

## 2. Technical Architecture & Stack
* **Language/Framework:** Python 3.11+, PyTorch 2.x, `torchaudio`.
* **API Gateway:** FastAPI.
* **Internal Microservices:** gRPC (Server Streaming).
* **Client-Facing Streaming:** Server-Sent Events (SSE).
* **File Storage:** Local shared volumes or dedicated S3/MinIO bucket.
* **Hardware:** Distributed multi-node GPU worker setup.

## 3. Phase 1: Core Protection Engine (The "Shield")
The ML core executes the adversarial noise generation directly on the raw waveform.

### 3.1. The PGD Optimization Loop
* **Target:** Frozen surrogate models (RVC v2, So-VITS-SVC).
* **Input:** Uncompressed 16-bit or 24-bit `.wav` files (44.1kHz).
* **Mechanism:** 500-1000 step iterative PGD on the audio tensor ($requires\_grad=True$).
* **Constraint:** Must operate in 1D space. Spectrogram transformations are strictly prohibited to protect high-frequency phase and vibrato data.

### 3.2. Multi-Objective Loss Specification
The backward pass computes a weighted loss to balance human intelligibility with AI disruption:
* **Reconstruction Loss ($L_r$, Weight 0.29):** Mean Squared Error between the clean and protected stem.
* **Perceptual Loss ($L_p$, Weight 0.29):** Differentiable PESQ/STOI wrapper.
* **Distortion Loss ($L_d$, Weight 0.02):** Inverted MSE against the surrogate clone output.
* **Opinion Loss ($L_o$, Weight 0.65):** Mean Opinion Score (MOS) predictor (e.g., DNSMOS) to force semantic degradation.

## 4. Phase 2: Distributed Event-Driven Server Architecture
This phase orchestrates the asynchronous routing of large audio payloads and real-time state updates using standard multi-node topologies.

### 4.1. File Ingestion & API Gateway (FastAPI)
* **Endpoint:** `POST /api/v1/encode`
* **Action:** Receives multipart `.wav` uploads from the React client, writes the file to the dedicated storage volume, and instantly returns a `Job_ID`.
* **Streaming Endpoint:** `GET /api/v1/stream/{job_id}` initializes the `StreamingResponse` for Server-Sent Events (SSE).

### 4.2. Internal Orchestration (gRPC)
* **Protocol:** gRPC Server Streaming.
* **Flow:** The FastAPI gateway opens a gRPC channel to the isolated Linux GPU nodes.
* **Protobuf Definition:** The GPU worker yields `OptimizationStatus` messages containing `status`, `current_step`, and `loss_metrics` back to the Gateway during the PGD loop.

### 4.3. The Data Harvesting Pipeline
Upon completion of the PGD loop, the worker node must archive the exact 1:1 pairing of `[Clean_Stem.wav]` and `[Protected_Stem.wav]` to an isolated directory. This passively generates the perfectly aligned dataset required to train the real-time U-Net VST in the future.
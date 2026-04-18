# Plan: 01. Core Protection Engine (The "Shield")

## Overview
Implement the PyTorch-based core engine responsible for Project Antigravity. This involves protecting vocal stems via adversarial noise generation on raw waveforms, without spectrogram transformations.

## Tasks
- [ ] Initialize Python 3.11 environment with PyTorch 2.x and `torchaudio`.
- [ ] Load frozen surrogate models (RVC v2, So-VITS-SVC) to be used as optimization targets.
- [ ] Implement the PGD Optimization Loop:
  - Operate entirely in 1D space.
  - Read uncompressed 16-bit or 24-bit `.wav` files (44.1kHz).
  - Apply 500-1000 step iterative PGD on the audio tensor (`requires_grad=True`).
- [ ] Implement Multi-Objective Loss Calculation:
  - **Reconstruction Loss ($L_r$, Weight 0.29):** MSE between clean and protected stem.
  - **Perceptual Loss ($L_p$, Weight 0.29):** Differentiable PESQ/STOI wrapper.
  - **Distortion Loss ($L_d$, Weight 0.02):** Inverted MSE against the surrogate clone output.
  - **Opinion Loss ($L_o$, Weight 0.65):** Mean Opinion Score (MOS) predictor (e.g., DNSMOS).

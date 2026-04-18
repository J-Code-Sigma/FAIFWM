# PyTorch Audio Protection Best Practices

## Restrictions on Audio Operations
- The Antigravity core operates completely in **1D Space** (waveform domain).
- **STRICT PROHIBITION:** Do not use spectrogram-based transformations (like STFT wrappers, mel-spectrogram inverse passes) during the optimization steps. Masking on a 2D spectrogram destroys high-frequency phase and subtle vibrato data, causing unacceptable phasing artifacts to human listeners.
- Optimization targets the audio tensor directly. It must have `requires_grad=True`.

## PGD Constraint Details
- Utilize Projected Gradient Descent iteratively for 500-1000 steps.
- Ensure optimization values are clamped within native bit-depth bounds (e.g., `-1.0` to `1.0` for normalized floating point) to prevent clipping distortion on the final product.

## Gradient Propagation through Loss Objs
- **Perceptual Loss**: Implement non-differentiable metrics (PESQ/STOI) very carefully. You may need to train a differentiable neural wrapper to approximate PESQ/STOI scores or construct the computational graph strictly using surrogate models.
- **Opinion Loss**: If wrapping metrics like DNSMOS, ensure the backward pass evaluates correctly and shapes the gradient natively towards semantic degradation for AI instead of just injecting white noise.

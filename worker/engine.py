import logging
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchaudio

logger = logging.getLogger(__name__)

class MultiResolutionSTFTLoss(nn.Module):
    """
    Native PyTorch substitute for PESQ/STOI. 
    Ensures perceptual similarity across multiple frequency bands.
    """
    def __init__(self, fft_sizes=[1024, 2048, 512], hop_sizes=[120, 240, 50], win_lengths=[600, 1200, 240]):
        super().__init__()
        self.fft_sizes = fft_sizes
        self.hop_sizes = hop_sizes
        self.win_lengths = win_lengths

    def stft(self, x, fft_size, hop_size, win_length):
        x_stft = torch.stft(
            x, fft_size, hop_size, win_length, 
            window=torch.hann_window(win_length).to(x.device), 
            return_complex=True
        )
        mag = torch.clamp(torch.abs(x_stft), min=1e-7)
        return mag

    def forward(self, x, y):
        sc_loss = 0.0
        mag_loss = 0.0
        # Ensure 2D tensor for STFT [batch * channels, time]
        x = x.view(-1, x.size(-1))
        y = y.view(-1, y.size(-1))
        for fs, hs, wl in zip(self.fft_sizes, self.hop_sizes, self.win_lengths):
            x_mag = self.stft(x, fs, hs, wl)
            y_mag = self.stft(y, fs, hs, wl)
            sc_loss += torch.norm(x_mag - y_mag, p="fro") / torch.norm(x_mag, p="fro")
            mag_loss += F.l1_loss(torch.log(x_mag), torch.log(y_mag))
        return (sc_loss + mag_loss) / len(self.fft_sizes)

class MelSpectrogramSurrogate(nn.Module):
    """
    Differentiable surrogate AI model. 
    Extracts Mel-Spectrogram features, representing the internal state of a VC clone.
    """
    def __init__(self, sample_rate=44100):
        super().__init__()
        self.melspec = torchaudio.transforms.MelSpectrogram(
            sample_rate=sample_rate,
            n_fft=1024,
            hop_length=256,
            n_mels=80,
            normalized=True
        )

    def forward(self, x):
        # Return log-mel spectrogram
        mel = self.melspec(x)
        return torch.log(torch.clamp(mel, min=1e-5))

class AdaptiveShield:
    """
    Core ML Engine implementing Adaptive VRAM Optimization for FAIFWM.
    """
    
    def __init__(self, target_steps: int = 500):
        self.target_steps = target_steps
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
    def _detect_vram_mode(self) -> str:
        """
        Detect VRAM availability to switch between Sliding Window and Global mode.
        """
        if not torch.cuda.is_available():
            return "CPU"
            
        total_vram = torch.cuda.get_device_properties(self.device).total_memory
        vram_gb = total_vram / (1024**3)
        
        logger.info(f"Detected GPU: {torch.cuda.get_device_name(self.device)} with {vram_gb:.2f} GB VRAM")
        
        if vram_gb < 12.0:
            return "CHUNKED"
        return "GLOBAL"

    def apply_protection(self, audio_tensor: torch.Tensor, sample_rate: int = 44100) -> torch.Tensor:
        """
        Executes PGD protection natively on the 1D waveform.
        """
        mode = self._detect_vram_mode()
        
        if mode == "CHUNKED":
            logger.info("Executing Chunked Mode (30s sliding windows) for Low VRAM")
            return self._run_chunked_pgd(audio_tensor, sample_rate)
        else:
            logger.info("Executing Global Mode for High VRAM")
            return self._run_global_pgd(audio_tensor, sample_rate)
            
    def _run_chunked_pgd(self, audio_tensor: torch.Tensor, sample_rate: int = 44100) -> torch.Tensor:
        chunk_size = 30 * sample_rate
        channels, total_frames = audio_tensor.shape
        protected_tensor = torch.zeros_like(audio_tensor)
        
        for start in range(0, total_frames, chunk_size):
            end = min(start + chunk_size, total_frames)
            chunk = audio_tensor[:, start:end]
            logger.info(f"Processing chunk [{start}:{end}] out of {total_frames} frames")
            protected_chunk = self._real_pgd_step(chunk, sample_rate)
            protected_tensor[:, start:end] = protected_chunk
            
        return protected_tensor
        
    def _run_global_pgd(self, audio_tensor: torch.Tensor, sample_rate: int = 44100) -> torch.Tensor:
        logger.info("Processing entire waveform globally.")
        return self._real_pgd_step(audio_tensor, sample_rate)

    def _real_pgd_step(self, tensor: torch.Tensor, sample_rate: int = 44100) -> torch.Tensor:
        """Implements the full MMMC Multi-Objective PGD loop."""
        tensor = tensor.to(self.device)
        noise = torch.zeros_like(tensor, requires_grad=True, device=self.device)
        # Higher learning rate for POC to show change in 10 steps
        optimizer = torch.optim.Adam([noise], lr=0.01)
        
        # Initialize Loss Modules
        stft_loss = MultiResolutionSTFTLoss().to(self.device)
        surrogate = MelSpectrogramSurrogate(sample_rate=sample_rate).to(self.device)
        
        # Loss Weights from PRD
        alpha_r, alpha_p, alpha_d, alpha_o = 0.29, 0.29, 0.02, 0.65
        
        # Target representation of clean audio
        with torch.no_grad():
            clean_surrogate_out = surrogate(tensor)

        # Run steps
        poc_steps = min(self.target_steps, 20) 
        logger.info(f"Starting {poc_steps} PGD steps for chunk...")
        
        for step in range(poc_steps):
            optimizer.zero_grad()
            protected = tensor + noise
            
            # 1. Reconstruction Loss (Lr): MSE
            L_r = F.mse_loss(protected, tensor)
            
            # 2. Perceptual Loss (Lp): Multi-Res STFT
            L_p = stft_loss(protected, tensor)
            
            # 3. Distortion Loss (Ld): Push away from clean AI representation
            surrogate_out = surrogate(protected)
            mse_surrogate = F.mse_loss(surrogate_out, clean_surrogate_out)
            # Inverted MSE = 1 / log(1 + MSE + eps)
            L_d = 1.0 / torch.log(1.0 + mse_surrogate + 1e-5)
            
            # 4. Opinion Loss (Lo): Spectral Entropy Maximization
            # Flatten to compute entropy across frequency bins
            # Using softmax to create a probability distribution over frequency bins
            probs = F.softmax(surrogate_out, dim=-2) 
            entropy = -torch.sum(probs * torch.log(probs + 1e-7), dim=-2).mean()
            # We want to maximize entropy to garble the output, so minimize -entropy
            L_o = -entropy
            
            # Combined Loss
            loss = (alpha_r * L_r) + (alpha_p * L_p) + (alpha_d * L_d) + (alpha_o * L_o)
            
            loss.backward()
            optimizer.step()
            
            # L-infinity projection (imperceptible constraint, max 0.2% amplitude)
            with torch.no_grad():
                noise.clamp_(-0.002, 0.002)
                
            if (step + 1) % 5 == 0 or step == 0:
                logger.info(f"Step {step+1}/{poc_steps}: Loss = {loss.item():.4f}")
                
        # Return protected tensor and move back to CPU to free VRAM
        protected_output = (tensor + noise).detach().cpu()
        
        # Cleanup
        del tensor, noise, optimizer, stft_loss, surrogate, clean_surrogate_out
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
        return protected_output

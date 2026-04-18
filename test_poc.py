import os
import math
import time
import torch
import torchaudio
import logging

from worker.engine import AdaptiveShield

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def generate_synthetic_wav(filepath: str, duration_sec: int = 40, sample_rate: int = 44100):
    """Generates a simple 440Hz sine wave to act as our test audio."""
    logger.info(f"Generating synthetic {duration_sec}s sine wave at {filepath}")
    t = torch.linspace(0, duration_sec, int(sample_rate * duration_sec))
    # 440 Hz sine wave, amplitude 0.5 to leave room for noise
    waveform = 0.5 * torch.sin(2 * math.pi * 440.0 * t).unsqueeze(0) # [1, frames]
    torchaudio.save(filepath, waveform, sample_rate)
    return waveform, sample_rate

def main():
    test_file = "test_input.wav"
    output_file = "protected_output.wav"
    
    # 1. Generate or load test file
    if not os.path.exists(test_file):
        # Generate a file longer than 30s to test chunking (e.g. 45s)
        generate_synthetic_wav(test_file, duration_sec=45)
    
    logger.info(f"Loading {test_file}")
    waveform, sample_rate = torchaudio.load(test_file)
    logger.info(f"Loaded waveform with shape {waveform.shape} and sample rate {sample_rate}")
    
    # 2. Initialize the ML Engine
    shield = AdaptiveShield(target_steps=10)
    
    # 3. Run protection
    logger.info("Applying FAIFWM protection...")
    start_time = time.time()
    
    # Pass sample rate to handle chunk calculations correctly
    protected_waveform = shield.apply_protection(waveform, sample_rate)
        
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Protection complete in {duration:.2f} seconds. Output shape: {protected_waveform.shape}")
    
    # 4. Save output
    logger.info(f"Saving to {output_file}")
    torchaudio.save(output_file, protected_waveform, sample_rate)
    logger.info("POC Test Complete! Check protected_output.wav")

if __name__ == "__main__":
    main()

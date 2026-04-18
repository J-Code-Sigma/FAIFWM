# FAIFWM

## Installation (Ubuntu 24.04 / Fresh Install)

To set up the backend ML engine on a fresh Ubuntu server, you need to install python virtual environments, pip, and PyTorch.

1. **Install System Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3-pip python3-venv ffmpeg -y
   ```

2. **Create and Activate Virtual Environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python Packages**
   ```bash
   pip install fastapi uvicorn python-multipart grpcio grpcio-tools PyJWT supabase
   # Install PyTorch with CUDA 12.8 support (or default depending on your system)
   pip install torch torchaudio
   # Install audio loading and processing dependencies
   pip install numpy soundfile torchcodec
   ```

# JINBEIBLETON - Local MusicGen MLX Weights Downloader
# This script downloads the full PyTorch/MLX weights from Hugging Face to allow offline local sample generation.

import os
import sys

# Ensure working directory is the server directory so .hf_cache is created in the right place
server_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(server_dir)

# Redirect HF Cache
def _get_hf_cache_dir():
    from pathlib import Path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    local_cache = os.path.join(script_dir, ".hf_cache")
    if os.path.exists(local_cache) and os.access(script_dir, os.W_OK):
        return local_cache
    home_cache = os.path.join(str(Path.home()), ".jinbeibleton", ".hf_cache")
    os.makedirs(home_cache, exist_ok=True)
    return home_cache

os.environ["HF_HOME"] = _get_hf_cache_dir()

print("==================================================================")
print("🧠 [JINBEIBLETON] Starting Local MusicGen MLX Model Downloader...")
print("==================================================================")
print("This script will download the full high-fidelity stereo models")
print("(facebook/musicgen-stereo-medium) directly from Hugging Face.")
print("This is a one-time download of approximately 3-4 GB.")
print("Please make sure your Mac is connected to the internet.")
print("------------------------------------------------------------------")

try:
    print("📦 Step 1: Importing local MLX sound engine...")
    try:
        from mlx_audiocraft.models import MusicGen
    except ImportError:
        from audiocraft_mlx.models import MusicGen
    
    print("🚀 Step 2: Downloading and caching weights (this may take a few minutes)...")
    # This will trigger huggingface_hub to fetch the real, full large files (not just 76-byte pointers)
    model = MusicGen.get_pretrained("facebook/musicgen-stereo-medium")
    
    print("------------------------------------------------------------------")
    print("🎉 SUCCESS!!!")
    print("Local MusicGen MLX model has been fully downloaded and verified!")
    print("You can now generate samples OFFLINE using the LOCAL engine!")
    print("==================================================================")
    
except Exception as e:
    import traceback
    print("\n❌ DOWNLOAD FAILED!")
    traceback.print_exc()
    print("==================================================================")
    sys.exit(1)

#!/bin/bash
# 🏎️ JINBEIBLETON - Real App Launcher

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE_DIR"

echo "🚀 Launching JINBEIBLETON Desktop..."

# Check root dependencies
if [ ! -d "node_modules" ]; then
    echo "📦 Initializing root components..."
    npm install
fi

# Check client dependencies (Vite, etc.)
if [ ! -d "client/node_modules" ]; then
    echo "📦 Initializing frontend components..."
    cd client && npm install && cd ..
fi

# Check Python venv - test if core packages work
VENV_PYTHON="server/venv/bin/python"
VENV_CHECK="import httpx; import ollama; import fastapi"

# On Mac, also require mlx-whisper for local voice recognition
if [ "$(uname)" = "Darwin" ]; then
    VENV_CHECK="$VENV_CHECK; import mlx_whisper"
fi

if [ ! -f "$VENV_PYTHON" ] || ! "$VENV_PYTHON" -c "$VENV_CHECK" &>/dev/null; then
    echo "📦 Python environment incomplete. Rebuilding..."
    rm -rf server/venv
    cd server
    python3 -m venv venv
    ./venv/bin/pip install --upgrade pip setuptools

    echo "📦 [1/3] Installing core server packages..."
    ./venv/bin/pip install -r requirements.txt

    echo "📦 [2/3] Installing optional AI models..."
    ./venv/bin/pip install -e git+https://github.com/openmirlab/mt3-infer.git#egg=mt3_infer 2>/dev/null || echo "⚠️  mt3-infer skipped"
    ./venv/bin/pip install basic-pitch static-ffmpeg 2>/dev/null || echo "⚠️  basic-pitch/ffmpeg skipped"
    ./venv/bin/pip install piano-transcription-inference 2>/dev/null || echo "⚠️  piano-transcription skipped"
    ./venv/bin/pip install audiocraft 2>/dev/null || echo "⚠️  audiocraft skipped"

    echo "📦 [3/3] Installing platform-specific packages..."
    if [ "$(uname)" = "Darwin" ]; then
        ./venv/bin/pip install mlx mlx-lm coremltools 2>/dev/null || echo "⚠️  MLX packages skipped"
        echo "📦 Installing local speech recognition (mlx-whisper)..."
        ./venv/bin/pip install mlx-whisper 2>/dev/null || echo "⚠️  mlx-whisper skipped"
        if [ -d "musicgen-mlx-main" ]; then
            ./venv/bin/pip install ./musicgen-mlx-main 2>/dev/null || echo "⚠️  musicgen-mlx skipped"
        fi
    else
        echo "📦 Installing local speech recognition (faster-whisper)..."
        ./venv/bin/pip install faster-whisper 2>/dev/null || echo "⚠️  faster-whisper skipped"
    fi

    cd ..
    echo "✅ Python environment ready."
fi

# Check if the packaged production app exists
PRODUCTION_APP="dist-app/mac-arm64/JINBEIBLETON.app"

if [ -d "$PRODUCTION_APP" ]; then
    echo "🏎️ Launching JINBEIBLETON Packaged Production App..."
    echo "💡 Bypassing macOS Sandbox by executing binary directly to inherit Terminal's mic permissions!"
    # Execute the raw binary inside the .app bundle
    "$PRODUCTION_APP/Contents/MacOS/JINBEIBLETON"
else
    echo "💡 Production package not found. Running in Development mode..."
    # Run in dev mode (force development env)
    NODE_ENV=development npm run dev
fi

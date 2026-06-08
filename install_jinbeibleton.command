#!/bin/bash

# ==========================================
# JINBEIBLETON Installer Script
# ==========================================

echo "=========================================="
echo "    JINBEIBLETON Installer"
echo "=========================================="
echo "This script installs the required system tools"
echo "(Homebrew, ffmpeg) and copies JINBEIBLETON"
echo "to the Applications folder."
echo ""

# ==========================================
# Request administrator password ONCE upfront
# ==========================================
echo "🔑 Administrator password is required for installation."
echo "   You will only need to enter it once."
echo ""
sudo -v

if [ $? -ne 0 ]; then
    echo "❌ Error: Administrator password is required to install."
    echo "   Please re-run this script and enter your password."
    read -p "Press Enter to exit..."
    exit 1
fi

# Keep sudo alive in the background for the duration of this script
while true; do sudo -n true; sleep 50; kill -0 "$$" || exit; done 2>/dev/null &
SUDO_KEEPALIVE_PID=$!

# ==========================================
# 1. Check for Homebrew
# ==========================================
if ! command -v brew &> /dev/null; then
    echo "📦 Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add brew to PATH for this script based on architecture
    if [ -d "/opt/homebrew/bin" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -d "/usr/local/bin" ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrew is already installed."
fi

# ==========================================
# 2. Check for ffmpeg
# ==========================================
if ! command -v ffmpeg &> /dev/null; then
    echo "📦 ffmpeg not found. Installing via Homebrew..."
    brew install ffmpeg
else
    echo "✅ ffmpeg is already installed."
fi

# ==========================================
# 3. Install the App
# ==========================================
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_SOURCE="$DIR/JINBEIBLETON.app"
APP_DEST="/Applications/JINBEIBLETON.app"

# If we are in the development workspace, the app might be in dist-app/mac-arm64
if [ ! -d "$APP_SOURCE" ] && [ -d "$DIR/dist-app/mac-arm64/JINBEIBLETON.app" ]; then
    APP_SOURCE="$DIR/dist-app/mac-arm64/JINBEIBLETON.app"
fi

if [ -d "$APP_SOURCE" ]; then
    echo "📦 Copying JINBEIBLETON to /Applications..."
    # Remove existing
    sudo rm -rf "$APP_DEST"
    # Copy new
    sudo cp -R "$APP_SOURCE" "$APP_DEST"
    
    # ==========================================
    # 4. Remove quarantine attribute (Bypass Gatekeeper)
    # ==========================================
    echo "🔐 Clearing Gatekeeper security restrictions..."
    sudo xattr -cr "$APP_DEST"
    
    # ==========================================
    # 5. Launch
    # ==========================================
    echo ""
    echo "✅ Installation complete! Launching JINBEIBLETON..."
    open -a "$APP_DEST"
else
    echo "❌ Error: 'JINBEIBLETON.app' not found in the same folder as this installer."
    echo "   Please run this script from the folder containing JINBEIBLETON.app."
fi

# Stop the sudo keepalive background process
kill "$SUDO_KEEPALIVE_PID" 2>/dev/null

echo ""
echo "✅ Done! You can close this Terminal window."
echo "(* From now on, you can open JINBEIBLETON directly"
echo "   by double-clicking the app in your Applications folder.)"
echo ""
read -p "Press Enter to exit..."
exit 0

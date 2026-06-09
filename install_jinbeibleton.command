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
# 1. Check for Homebrew (Homebrew will ask for password internally if needed)
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
    
    # Try to copy without sudo first
    rm -rf "$APP_DEST" 2>/dev/null
    cp -R "$APP_SOURCE" "$APP_DEST" 2>/dev/null
    
    # Check if copy succeeded
    if [ $? -ne 0 ] || [ ! -d "$APP_DEST" ]; then
        echo "🔒 Copying requires administrator privileges. Please enter your password:"
        sudo rm -rf "$APP_DEST"
        sudo cp -R "$APP_SOURCE" "$APP_DEST"
        
        # Ensure the owner remains the current user even if copied with sudo
        CURRENT_USER=$(whoami)
        sudo chown -R "$CURRENT_USER" "$APP_DEST"
    fi
    
    # ==========================================
    # 4. Remove quarantine attribute & Ad-hoc sign the app
    # ==========================================
    echo "🔐 Clearing Gatekeeper security restrictions..."
    xattr -cr "$APP_DEST" 2>/dev/null || sudo xattr -cr "$APP_DEST"
    
    echo "✍️  Signing application components (bypassing 'Open anyway' prompts)..."
    # Ad-hoc sign the app as current user. If it fails, ignore and proceed to launch
    # instead of triggering sudo prompts.
    codesign --force --deep --sign - "$APP_DEST" 2>/dev/null || true
    
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

echo ""
echo "✅ Done! You can close this Terminal window."
echo "(* From now on, you can open JINBEIBLETON directly"
echo "   by double-clicking the app in your Applications folder.)"
echo ""
read -p "Press Enter to exit..."
exit 0

#!/bin/bash
# JINBEIBLETON - App Launcher & Gatekeeper Bypass
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="/Applications/JINBEIBLETON.app"

# Set terminal title
printf "\033]0;JINBEIBLETON Launch Helper\007"
clear

echo "========================================="
echo " JINBEIBLETON Launch Helper"
echo "========================================="
echo "This script automatically bypasses macOS Gatekeeper"
echo "warnings (e.g. 'damaged and can't be opened') and launches"
echo "the JINBEIBLETON application."
echo "========================================="
echo ""

# 1. Check if the app is copied to Applications folder
if [ ! -d "$APP_PATH" ]; then
    echo "⚠️  Error: JINBEIBLETON is not in your Applications folder."
    echo ""
    echo "[How to Fix]"
    echo "Please drag and drop JINBEIBLETON from the DMG window"
    echo "into the Applications folder first, then run this helper again."
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

# 2. Bypass Gatekeeper quarantine & Ad-hoc sign the app
echo "🔒 Clearing macOS security restrictions..."
xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null
xattr -cr "$APP_PATH" 2>/dev/null

echo "✍️  Signing application components (bypassing 'Open anyway' prompts)..."
# Ad-hoc sign the entire app recursively to satisfy Apple Silicon arm64 code signature requirements.
# This eliminates "Developer cannot be verified" dialogs for internal Python/Node executables.
codesign --force --deep --sign - "$APP_PATH" 2>/dev/null

echo "✅ Security restrictions cleared successfully."

# 3. Launch App
echo ""
echo "🚀 Launching JINBEIBLETON..."
open "$APP_PATH"

echo ""
echo "✅ Done! You can close this Terminal window."
echo "(* From now on, you can open JINBEIBLETON directly"
echo "   by double-clicking the app in your Applications folder.)"
echo ""
sleep 3
exit 0

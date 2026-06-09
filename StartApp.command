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
echo "warnings and launches JINBEIBLETON."
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

# 2. Bypass Gatekeeper quarantine (No sudo needed)
echo "🔒 Clearing macOS security restrictions..."
xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null
xattr -cr "$APP_PATH" 2>/dev/null
echo "✅ Security restrictions cleared."

# 3. Launch App
echo ""
echo "🚀 Launching JINBEIBLETON..."
open "$APP_PATH"

echo ""
echo "✅ Done! You can close this Terminal window."
echo ""
sleep 2
exit 0

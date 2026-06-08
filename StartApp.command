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

# 2. Bypass Gatekeeper quarantine (single sudo prompt for all operations)
echo "🔒 Clearing macOS security restrictions..."
echo "   (You may be asked for your password once.)"
echo ""

# Request sudo credentials once upfront — all subsequent sudo calls
# will reuse the cached credentials within the timeout window.
sudo -v 2>/dev/null

if [ $? -eq 0 ]; then
    # sudo was successful — use it for full quarantine removal
    sudo xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null
    sudo xattr -cr "$APP_PATH" 2>/dev/null
    echo "✅ Security restrictions cleared successfully."
else
    # Fallback to non-sudo (may not work for all files)
    echo "⚠️  Running without administrator privileges (may be incomplete)."
    xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null
    xattr -cr "$APP_PATH" 2>/dev/null
fi

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

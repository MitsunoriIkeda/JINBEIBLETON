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
echo "This helper script clears macOS security restrictions"
echo "and ad-hoc signs JINBEIBLETON to bypass all"
echo "'Open anyway' prompts and launch the app."
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

# 2. Request Administrator privileges ONCE to bypass TCC restrictions and sign files
echo "🔑 Please enter your administrator password to authorize security clearance."
echo "   (You will only need to enter it once here, and no more prompts will appear.)"
echo ""
sudo -v

if [ $? -ne 0 ]; then
    echo "❌ Error: Administrator password is required to bypass macOS Gatekeeper."
    read -p "Press Enter to exit..."
    exit 1
fi

# 3. Bypass Gatekeeper quarantine & Ad-hoc sign the app using sudo (guarantees success)
echo ""
echo "🔒 Clearing macOS security restrictions (Gatekeeper)..."
sudo xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null
sudo xattr -cr "$APP_PATH" 2>/dev/null

echo "✍️  Applying ad-hoc code signatures to all nested components..."
sudo codesign --force --deep --sign - "$APP_PATH" 2>/dev/null

# 4. Ensure correct file ownership
CURRENT_USER=$(whoami)
sudo chown -R "$CURRENT_USER" "$APP_PATH"

echo "✅ Security restrictions cleared successfully!"

# 5. Launch App
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

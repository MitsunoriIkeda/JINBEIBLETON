#!/bin/bash
# JINBEIBLETON - App Launcher & Gatekeeper Bypass
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="/Applications/JINBEIBLETON.app"

# Set terminal title
printf "\033]0;JINBEIBLETON Launch Helper\007"
clear

echo "================================================="
echo "  JINBEIBLETON LAUNCH HELPER [CHIHUAHUA EDITION]"
echo "================================================="
echo "Checking and clearing macOS security restrictions..."
echo "================================================="
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
echo "   (You will only need to enter it once here.)"
echo ""
sudo -v

if [ $? -ne 0 ]; then
    echo "❌ Error: Administrator password is required to bypass macOS Gatekeeper."
    read -p "Press Enter to exit..."
    exit 1
fi

# 3. Bypass Gatekeeper quarantine & Ad-hoc sign the app using sudo (guarantees success)
echo ""
echo "🔒 [1/3] Clearing macOS Gatekeeper quarantine..."
sudo xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null
sudo xattr -cr "$APP_PATH"

echo ""
echo "✍️  [2/3] Applying ad-hoc code signatures..."
# We remove 2>/dev/null so that if codesign fails, the exact error is visible in the terminal
sudo codesign --force --deep --sign - "$APP_PATH"

# 4. Ensure correct file ownership
echo ""
echo "🔑 [3/3] Restoring user file ownership..."
CURRENT_USER=$(whoami)
sudo chown -R "$CURRENT_USER" "$APP_PATH"

echo ""
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

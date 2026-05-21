#!/bin/bash
# ============================================================
# JINBEIBLETON - AbletonJS Remote Script Installer
# ============================================================
# This script installs the AbletonJS MIDI Remote Script
# required for JINBEIBLETON to communicate with Ableton Live.
# ============================================================

set -e

echo ""
echo "🐕 JINBEIBLETON - Remote Script Installer"
echo "==========================================="
echo ""

# Find the midi-script source
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Check multiple possible locations for the midi-script
MIDI_SCRIPT_SRC=""
if [ -d "$SCRIPT_DIR/midi-script" ]; then
    MIDI_SCRIPT_SRC="$SCRIPT_DIR/midi-script"
elif [ -d "$SCRIPT_DIR/../server/node_bridge/node_modules/ableton-js/midi-script" ]; then
    MIDI_SCRIPT_SRC="$SCRIPT_DIR/../server/node_bridge/node_modules/ableton-js/midi-script"
fi

if [ -z "$MIDI_SCRIPT_SRC" ]; then
    echo "❌ Error: midi-script folder not found."
    echo "   Please make sure you're running this from the JINBEIBLETON directory."
    exit 1
fi

echo "📂 Found MIDI script source: $MIDI_SCRIPT_SRC"

# Detect Ableton version
ABLETON_APP=""
REMOTE_SCRIPTS_DIR=""

# Check common Ableton Live installation paths
for app in "/Applications/Ableton Live 12 Suite.app" \
           "/Applications/Ableton Live 12 Standard.app" \
           "/Applications/Ableton Live 12 Intro.app" \
           "/Applications/Ableton Live 11 Suite.app" \
           "/Applications/Ableton Live 11 Standard.app" \
           "/Applications/Ableton Live 11 Intro.app"; do
    if [ -d "$app" ]; then
        ABLETON_APP="$app"
        REMOTE_SCRIPTS_DIR="$app/Contents/App-Resources/MIDI Remote Scripts"
        break
    fi
done

# Also check User Library path
USER_REMOTE_SCRIPTS="$HOME/Music/Ableton/User Library/Remote Scripts"

if [ -z "$ABLETON_APP" ]; then
    echo "⚠️  Ableton Live not found in /Applications."
    echo "   Will install to User Library instead."
    REMOTE_SCRIPTS_DIR="$USER_REMOTE_SCRIPTS"
fi

echo "📍 Target: $REMOTE_SCRIPTS_DIR/AbletonJS"
echo ""

# Check if already installed
if [ -d "$REMOTE_SCRIPTS_DIR/AbletonJS" ]; then
    echo "⚠️  AbletonJS is already installed."
    read -p "   Overwrite? (y/N): " CONFIRM
    if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
        echo "   Skipped. Existing installation kept."
        echo ""
        echo "✅ Setup complete! See below for Ableton configuration."
        echo ""
        echo "==========================================="
        echo "📋 ABLETON LIVE SETTINGS"
        echo "==========================================="
        echo "1. Open Ableton Live"
        echo "2. Go to Settings (Cmd + ,)"
        echo "3. Click 'Link, Tempo & MIDI' tab"
        echo "4. Under 'Control Surface', select 'AbletonJS'"
        echo "5. Input/Output: No need to set (it uses UDP, not MIDI)"
        echo "6. Close Settings"
        echo "7. Launch JINBEIBLETON app"
        echo "==========================================="
        exit 0
    fi
    rm -rf "$REMOTE_SCRIPTS_DIR/AbletonJS"
fi

# Create target directory if needed
mkdir -p "$REMOTE_SCRIPTS_DIR"

# Copy midi-script to target
cp -R "$MIDI_SCRIPT_SRC" "$REMOTE_SCRIPTS_DIR/AbletonJS"

echo "✅ AbletonJS Remote Script installed successfully!"
echo ""
echo "==========================================="
echo "📋 NEXT STEPS - ABLETON LIVE SETTINGS"
echo "==========================================="
echo ""
echo "1. Open (or restart) Ableton Live"
echo "2. Go to Settings (Cmd + ,)"
echo "3. Click 'Link, Tempo & MIDI' tab"
echo "4. Under 'Control Surface', select 'AbletonJS'"
echo "5. Input/Output: No need to set (it uses UDP, not MIDI)"
echo "6. Close Settings"
echo "7. Launch JINBEIBLETON app"
echo ""
echo "🐕 Enjoy JINBEIBLETON!"
echo ""

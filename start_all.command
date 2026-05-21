#!/bin/bash
# Ableton AI Cockpit - One-Click Launcher (Enhanced)

# Get the directory where the script is located
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🚀 Starting Ableton AI Cockpit..."

# 0. Clean up old processes to avoid "Address already in use"
echo "🧹 Cleaning up old sessions..."
lsof -ti:8002,8005 | xargs kill -9 2>/dev/null
sleep 1

# 1. Start Node Bridge
osascript -e "tell application \"Terminal\" to do script \"cd '$BASE_DIR/server/node_bridge' && node index.js\""
echo "✅ Node Bridge starting in new window..."

# 2. Start Python Server
osascript -e "tell application \"Terminal\" to do script \"cd '$BASE_DIR/server' && ./venv/bin/python main.py\""
echo "✅ Python Server starting in new window..."

# 3. Start Frontend (Vite)
osascript -e "tell application \"Terminal\" to do script \"cd '$BASE_DIR/client' && npm run dev\""
echo "✅ Frontend starting in new window..."

echo ""
echo "✨ All systems go! You can close this window and watch the others."
echo "Keep the terminal windows open while using the controller."

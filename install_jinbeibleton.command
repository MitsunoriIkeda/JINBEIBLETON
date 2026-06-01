#!/bin/bash

# ==========================================
# JINBEIBLETON Installer Script
# ==========================================

echo "=========================================="
echo "    JINBEIBLETON インストーラー"
echo "=========================================="
echo "このスクリプトは、JINBEIBLETONを動作させるために"
echo "必要なシステムツール(Homebrew, ffmpeg)を自動でインストールし、"
echo "アプリをアプリケーションフォルダに配置します。"
echo ""

# Request administrator privileges upfront if necessary, though Homebrew prefers not to be run as root.
# We will just run commands normally; Homebrew will ask for password if needed.

# 1. Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "📦 Homebrewが見つかりませんでした。インストールを開始します..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add brew to PATH for this script based on architecture
    if [ -d "/opt/homebrew/bin" ]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [ -d "/usr/local/bin" ]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
else
    echo "✅ Homebrewは既にインストールされています。"
fi

# 2. Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "📦 ffmpegが見つかりませんでした。Homebrew経由でインストールします..."
    brew install ffmpeg
else
    echo "✅ ffmpegは既にインストールされています。"
fi

# 3. Install the App
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
APP_SOURCE="$DIR/JINBEIBLETON.app"
APP_DEST="/Applications/JINBEIBLETON.app"

# If we are in the development workspace, the app might be in dist-app/mac-arm64
if [ ! -d "$APP_SOURCE" ] && [ -d "$DIR/dist-app/mac-arm64/JINBEIBLETON.app" ]; then
    APP_SOURCE="$DIR/dist-app/mac-arm64/JINBEIBLETON.app"
fi

if [ -d "$APP_SOURCE" ]; then
    echo "📦 JINBEIBLETON アプリケーションを /Applications にコピーしています..."
    # Remove existing
    rm -rf "$APP_DEST"
    # Copy new
    cp -R "$APP_SOURCE" "$APP_DEST"
    
    # 4. Remove quarantine attribute (Bypass Gatekeeper)
    echo "🔐 セキュリティブロック（Gatekeeper）を解除しています..."
    xattr -cr "$APP_DEST"
    
    # 5. Launch
    echo "🚀 インストールが完了しました！ JINBEIBLETONを起動します..."
    open -a "$APP_DEST"
else
    echo "❌ エラー: インストーラーと同じフォルダに 'JINBEIBLETON.app' が見つかりませんでした。"
    echo "ZIPファイルを解凍したフォルダ内でこのスクリプトを実行してください。"
fi

echo ""
echo "完了しました。このウィンドウは閉じて構いません。"

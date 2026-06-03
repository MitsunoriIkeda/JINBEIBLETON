#!/bin/bash
# JINBEIBLETON Launch & Gatekeeper Bypass Script
BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_PATH="/Applications/JINBEIBLETON.app"

# Terminal appearance settings (optional but nice)
printf "\033]0;JINBEIBLETON 起動アシスタント\007"
clear

echo "========================================="
echo " JINBEIBLETON 起動アシスタント"
echo "========================================="
echo "このスクリプトは、macOSのセキュリティ制限による"
echo "「破損しているため開けません」という警告を自動解除します。"
echo "========================================="
echo ""

# 1. アプリケーションフォルダにアプリがあるか確認
if [ ! -d "$APP_PATH" ]; then
    echo "⚠️  エラー: アプリが「アプリケーション」フォルダにコピーされていません。"
    echo ""
    echo "【対策】"
    echo "DMG（ディスクイメージ）ウィンドウ内の「JINBEIBLETON」アイコンを"
    echo "「Applications（アプリケーション）」フォルダへドラッグ＆ドロップして"
    echo "コピーしてから、もう一度このアシスタントを実行してください。"
    echo ""
    read -p "Enterキーを押して終了します..."
    exit 1
fi

# 2. Gatekeeperのブロックを解除
echo "🔒 セキュリティ制限の自動解除コマンドを実行しています..."
echo "xattr -d com.apple.quarantine $APP_PATH"
xattr -d com.apple.quarantine "$APP_PATH" 2>/dev/null
xattr -cr "$APP_PATH" 2>/dev/null

# 3. アプリの起動
echo "🚀 JINBEIBLETONを起動しています..."
open "$APP_PATH"

echo ""
echo "✅ 制限の解除と起動処理が完了しました！"
echo "このターミナルウィンドウは閉じて構いません。"
echo "（次回からは、アプリケーションフォルダのJINBEIBLETONアプリを"
echo "  ダブルクリックするだけで直接起動できるようになります）"
echo ""
sleep 3
exit 0

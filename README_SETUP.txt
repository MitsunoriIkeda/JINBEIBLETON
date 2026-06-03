========================================================================
JINBEIBLETON v1.1.0 - Setup Guide & Manual / セットアップガイド & マニュアル
========================================================================

【日本語 (Japanese)】
JINBEIBLETONをご利用いただきありがとうございます！
本アプリがAbleton Liveと通信し、AIでコントロールするためには、以下のセットアップが必要です。

■ ステップ 1: アプリケーションの配置
1. 「JINBEIBLETON-1.1.0-arm64.dmg」を開きます。
2. 開いたウィンドウ内の「JINBEIBLETON」アプリを、Macの「アプリケーション (Applications)」フォルダにドラッグ＆ドロップしてコピーしてください。

■ ステップ 2: アプリの起動とセキュリティ制限の解除
1. アプリケーションフォルダに配置した「JINBEIBLETON」アプリを起動します。

   ⚠️ 【重要】初回起動時のセキュリティ警告について：
   macOSのセキュリティ保護（Gatekeeper）により、起動時に「"JINBEIBLETON"は破損しているため開けません。ゴミ箱に入れる必要があります」や「開発元が未確認のため開けません」という警告ダイアログが表示されることがあります。
   これはアプリが実際に壊れているわけではなく、インターネットから取得した未署名アプリに対するmacOSの一般的な保護動作です。
   以下の手順で安全に起動できます：
     ① 警告が出たら「キャンセル」をクリックして閉じます（※ゴミ箱には移動しないでください）。
     ② Macの「システム設定」＞「プライバシーとセキュリティ」を開きます。
     ③ 画面を下へスクロールし、セキュリティ欄にある「"JINBEIBLETON"は開発元を確認できないため、開くのがブロックされました」という表示の右側にある【このまま開く】ボタンをクリックします。
     ④ パスワードまたはTouch IDで許可し、再度現れる警告画面で【開く】をクリックします。
     （※ この操作は初回のみ必要で、2回目以降は通常通り起動できます）

2. **【自動化】** アプリが起動すると、Ableton Liveに必要な接続スクリプト（AbletonJS）が自動的にユーザーの「User Library/Remote Scripts」に配置されます！手動でコピーする必要はありません。
3. 次に、Ableton Live を起動（または再起動）してください。
4. 設定画面を開きます（Mac: Cmd + , ）。
5. 左側のタブから「Link, Tempo & MIDI」を選択します。
6. 「Control Surface（コントロールサーフェス）」の空いている行のドロップダウンメニューから「AbletonJS」を選択してください。
   ※ Input / Output は「なし（None）」のままで問題ありません。
7. 設定画面を閉じます。自動的にアプリ画面の右上に「✅ Ableton Connected」と表示されれば接続成功です！

■ ステップ 3: ローカルAIモデル（MLX MusicGen）の初回利用について
- 初めて「LOCAL」エンジンでサンプル生成を行う際、アプリが自動的にHugging FaceからローカルAIモデルのウェイト（約3.5GB）をバックグラウンドでダウンロードします。
- 初回のみダウンロードに数分かかりますが、2回目以降はオフラインモードとなり、インターネット接続なしで瞬時に生成が完了するようになります。

------------------------------------------------------------------------

【English】
Welcome to JINBEIBLETON v1.1.0!
To allow the AI to control Ableton Live, you need to set up the connection by following these steps:

■ Step 1: Install JINBEIBLETON
1. Open "JINBEIBLETON-1.1.0-arm64.dmg".
2. Drag and drop "JINBEIBLETON" into your Mac's "Applications" folder.

■ Step 2: Launch App & Resolve Security Warning
1. Launch the "JINBEIBLETON" app from the Applications folder.

   ⚠️ [CRITICAL] Handling macOS Gatekeeper Warning:
   Because this app is self-signed, on first launch macOS may show a warning saying:
   ""JINBEIBLETON" is damaged and can't be opened. You should move it to the Trash." or
   ""JINBEIBLETON" cannot be opened because the developer cannot be verified."
   The app is NOT actually damaged. Please follow these steps to open it:
     ① Click [Cancel] on the dialog (do NOT move it to the Trash).
     ② Open your Mac's [System Settings] > [Privacy & Security].
     ③ Scroll down to the "Security" section, find the message about JINBEIBLETON being blocked, and click the 【Open Anyway】 button next to it.
     ④ Enter your password/Touch ID, and click 【Open】 on the final confirmation dialog.
     (Note: This is only required on the very first launch.)

2. **[Automated]** Upon launching, JINBEIBLETON will automatically copy the required AbletonJS MIDI Remote Script folder into your User Library. No manual script installation is needed!
3. Open (or restart) Ableton Live.
4. Open Settings / Preferences (Mac: Cmd + ,).
5. Go to the "Link, Tempo & MIDI" tab.
6. In an empty row under "Control Surface", select "AbletonJS" from the dropdown menu.
   * Note: Leave Input / Output as "None".
7. Close the Settings window. JINBEIBLETON will automatically connect and show "✅ Ableton Connected" in the top right.

■ Step 3: First-Use of Local AI Sampler (MLX MusicGen)
- When you generate a sample using the "LOCAL" engine for the first time, JINBEIBLETON will automatically download the required model weights (~3.5GB) from Hugging Face in the background.
- This download is a one-time process. Once cached, all subsequent generations will run fully offline and run instantly.

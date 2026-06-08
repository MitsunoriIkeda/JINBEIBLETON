========================================================================
JINBEIBLETON v1.1.0 - Setup Guide & Manual / セットアップガイド & マニュアル
========================================================================

【日本語 (Japanese)】
JINBEIBLETONをご利用いただきありがとうございます！
本アプリがAbleton Liveと通信し、AIでコントロールするためには、以下のセットアップが必要です。

■ ステップ 1: アプリケーションの配置
1. 「JINBEIBLETON-1.1.0-arm64.dmg」を開きます。
2. 開いたウィンドウ内の「JINBEIBLETON」アプリを、Macの「アプリケーション (Applications)」フォルダにドラッグ＆ドロップしてコピーしてください。

■ ステップ 2: 初回起動とセキュリティ制限の自動解除
1. アプリケーションフォルダにコピーした「JINBEIBLETON」アプリをダブルクリックして起動します。

   ⚠️ 【重要】「開発元を検証できないため開けません」や「破損しているため開けません」と表示される場合：
   macOSのセキュリティ仕様により、初回起動時にエラーが出て開けない場合があります。
   その場合は、以下の手順で自動的にセキュリティ解除を完了させて起動してください：

     ① 警告ダイアログを【キャンセル】で閉じます（※ゴミ箱に入れないでください）。
     ② DMGウィンドウ（この画面）に同梱されている『StartApp.command』をダブルクリックします。
     ③ ターミナル（黒い画面）が立ち上がり、自動的にセキュリティ解除とアプリへの内部署名が実行されます。
     ④ 署名が完了すると、自動的に「JINBEIBLETON」が何の設定もパスワード要求もなしで起動します。

     （※ この操作は最初の1回のみ必要です。2回目以降は、アプリケーションフォルダ内の「JINBEIBLETON」アプリをダブルクリックするだけで直接起動できます。システム設定の「このまま開く」や管理者パスワードの入力は不要です）

2. **【自動化】** アプリが起動すると、Ableton Liveに必要な接続スクリプト（AbletonJS）が自動的にユーザーの「User Library/Remote Scripts」に配置されます！手動でコピーする必要はありません。
3. 次に、Ableton Live を起動（または再起動）してください。
4. 設定画面を開きます（Mac: Cmd + , ）。
5. 左側のタブから「Link, Tempo & MIDI」を選択します。
6. 「Control Surface（コントロールサーフェス）」の空いている行のドロップダウンメニューから「AbletonJS」を選択してください。
   ※ Input / Output は「なし（None）」のままで問題ありません。
7. 設定画面を閉じます。自動的にアプリ画面의 右上に「✅ Ableton Connected」と表示されれば接続成功です！

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

■ Step 2: First Launch & Automatic Security Bypass
1. Double-click the "JINBEIBLETON" app in your Applications folder to launch it.

   ⚠️ [CRITICAL] If macOS says "cannot be opened because the developer cannot be verified" or "is damaged":
   Due to macOS security gatekeeper policies, you may be blocked on the first launch.
   To resolve this automatically, please follow these steps:

     ① Click [Cancel] on the warning dialog (do NOT move it to the Trash).
     ② Double-click the file named 『StartApp.command』 included in this DMG window.
     ③ A black Terminal window will open. It will automatically bypass Gatekeeper and apply local ad-hoc signatures to the app components.
     ④ Once signing is complete, JINBEIBLETON will launch automatically without asking for any password or requiring you to go to System Settings.

     (Note: This is a one-time setup. Afterwards, you can launch the JINBEIBLETON app directly from your Applications folder. No System Settings or password prompt is required.)

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

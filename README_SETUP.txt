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
1. アプリケーションフォルダにコピーした「JINBEIBLETON」アプリを起動します。

   ⚠️ 【重要】「開発元を検証できないため開けません」と表示される場合：
   macOSのセキュリティ仕様（Gatekeeper）により、そのままダブルクリックすると起動がブロックされます。
   以下の簡単な手順（macOS標準の回避策）で起動してください。

     ① アプリケーションフォルダ内の「JINBEIBLETON」アプリを【右クリック（または Control キーを押しながらクリック）】します。
     ② メニューから【開く】を選択します。
     ③ 「開発元を検証できませんが、開きますか？」というダイアログが表示されるので、【開く】ボタンをクリックします。

   ※この手順は【最初の1回のみ】必要です。起動すると、アプリ内部のプログラムが自身に対するセキュリティ解除（クアランティン属性の消去およびアドホック署名）を自動的に実行します。
   ※2回目以降は、アプリを通常通り【ダブルクリックするだけ】で、管理者パスワードの要求やセキュリティ警告も一切なしで直接起動するようになります。

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
1. Launch the "JINBEIBLETON" app in your Applications folder.

   ⚠️ [CRITICAL] If macOS says "cannot be opened because the developer cannot be verified":
   Due to macOS security policies (Gatekeeper), double-clicking the app directly for the first time will block the launch.
   Please use the standard macOS workaround to open it:

     ① [Right-click] (or hold Control and click) the "JINBEIBLETON" app icon in your Applications folder.
     ② Select 【Open】 from the context menu.
     ③ A dialog will appear asking "developer cannot be verified, are you sure you want to open it?". Click the 【Open】 button.

   * Note: This right-click workaround is only required for the [very first launch]. Once launched, the app automatically removes its own quarantine attributes and ad-hoc signs all nested helper binaries.
   * For all subsequent launches, you can open JINBEIBLETON by simply [double-clicking] it directly. No passwords or security warnings will appear.

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

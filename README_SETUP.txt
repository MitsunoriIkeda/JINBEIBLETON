========================================================================
JINBEIBLETON v1.1.0 - Setup Guide & Manual / セットアップガイド & マニュアル
========================================================================

【日本語 (Japanese)】
JINBEIBLETONをご利用いただきありがとうございます！
本アプリがAbleton Liveと通信し、AIでコントロールするためには、以下のセットアップが必要です。

■ ステップ 1: アプリケーションのインストール
1. ダウンロードした「JINBEIBLETON-1.1.0-arm64.pkg」を実行（ダブルクリック）します。

   ⚠️ 【重要】「開発元を検証できないため開けません」と表示される場合：
   macOSのセキュリティ制限によりブロックされることがあります。その場合は、以下の簡単な方法で実行してください。
     ① ダウンロードした「JINBEIBLETON-1.1.0-arm64.pkg」を【右クリック（または Control キーを押しながらクリック）】します。
     ② メニューから【開く】を選択します。
     ③ 警告が表示されますが、そのまま【開く】をクリックします。
        （または、「システム設定 ＞ プライバシーとセキュリティ」の一番下にある【このまま開く】をクリックします）

2. インストーラー画面（ウィザード）が起動しますので、画面の指示に従ってインストールを完了してください。
   （※インストール中に1度だけMacのログインパスワードの入力が求められます）

3. インストーラーが、自動的にアプリ（JINBEIBLETON.app）を「アプリケーション」フォルダに安全に配置し、バックグラウンドですべてのセキュリティ解除（アドホック署名）を完了させます。

■ ステップ 2: 初回起動と接続
1. Macの「アプリケーション」フォルダから「JINBEIBLETON」アプリをダブルクリックして起動します。
   （※インストーラーがすでにセキュリティ処理を完了しているため、エラー警告なしに1発で起動します！）

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
1. Open (double-click) the downloaded "JINBEIBLETON-1.1.0-arm64.pkg" file.

   ⚠️ [CRITICAL] If macOS says "cannot be opened because the developer cannot be verified":
   Gatekeeper might block it on the first launch. Please bypass this using the standard method:
     ① [Right-click] (or hold Control and click) the "JINBEIBLETON-1.1.0-arm64.pkg" file.
     ② Select 【Open】 from the context menu.
     ③ Click 【Open】 on the warning dialog.
        (Or click 【Open Anyway】 under "System Settings > Privacy & Security")

2. Follow the standard installation wizard. Enter your Mac login password when prompted.
3. The installer will copy JINBEIBLETON to your Applications folder and automatically whitelist and ad-hoc sign all nested binaries under root privileges.

■ Step 2: First Launch & Connection
1. Go to your "Applications" folder and double-click "JINBEIBLETON" to launch it directly. No warnings or "damaged" errors will appear.
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

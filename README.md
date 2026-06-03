# JINBEIBLETON
**AI-Powered Music Assistant & MIDI Controller for Ableton Live**  
**Ableton Live向け AIミュージックアシスタント ＆ MIDIコントローラー**

JINBEIBLETON is a macOS desktop application designed for Apple Silicon (M1/M2/M3/M4) that seamlessly bridges modern AI tools with Ableton Live. It offers high-precision local audio-to-MIDI transcription and an intelligent retro-arcade style music production advisor.

JINBEIBLETONは、最新のAIツールとAbleton Liveをシームレスに繋ぐ、macOS（Apple Silicon M1/M2/M3/M4）専用のデスクトップアプリケーションです。高精度なローカルでのオーディオ-MIDI変換機能と、レトロゲーム風の音楽制作AIアドバイザーを提供します。

---

## 🚀 Features / 主な機能

### 1. Audio to MIDI Transcription (AIオーディオMIDI変換)
- **MT3**: Multi-instrument automatic music transcription.
- **GiantMIDI-Piano**: High-precision piano transcription optimized for solo piano performances.
- **Fully Local**: Runs entirely on your Mac using PyTorch. No cloud uploads required, keeping your audio data private and secure.

- **MT3**: 複数楽器の同時音高検出に対応した自動MIDI変換。
- **GiantMIDI-Piano**: ソロピアノ演奏に最適化された高精度ピアノMIDI変換。
- **完全ローカル動作**: Macローカル上のPyTorchで処理されるため、音声データをクラウドにアップロードせず、安全かつ高速に変換できます。

### 2. Intelligent AI Advisor (AI音楽制作アドバイザー)
- Powered by **Gemini 3.5 Flash** (Cloud) or local response matching.
- **Instant Manual Lookup**: Bypasses the network to instantly answer Ableton Live shortcut and basic manual questions from a built-in dictionary.
- **Creative Copilot**: Ask the advisor for arrangement ideas, mixing tips, routing setups, or music theory help.

- **Gemini 3.5 Flash** (クラウド) またはローカル処理による対話型AIアシスタント。
- **マニュアル・ショートカットの即答**: Ableton Liveのショートカットやマニュアルに関する質問は、インターネット通信を介さず内蔵の辞書から一瞬で回答します。
- **制作アドバイザー**: アレンジのアイデア、ミキシングのコツ、複雑なルーティング、音楽理論などについてAIドッグにいつでも相談できます。

### 3. Ableton Live Integration (Ableton Live連携)
- Bi-directional control and state synchronization via a custom **MIDI Remote Script**.

- 専用の **MIDIリモートスクリプト** による、Ableton Liveとの双方向連携およびステート同期。

---

## 📋 Requirements / 動作環境

- **OS**: macOS 12+ (Apple Silicon M1/M2/M3/M4 Series)  
  *※Intel Macs are not supported. / Intel Macはサポートされていません。*
- **Host DAW**: Ableton Live 11 or Ableton Live 12
- **API Key**: Google Gemini API Key (Required for cloud AI features / クラウドAI機能の利用に必要)

---

## 🛠️ Installation & Setup / インストールと設定

### 1. Application Install / アプリのインストール
1. Download `JINBEIBLETON-1.1.0-arm64.dmg` from the [Releases](https://github.com/MitsunoriIkeda/for-ableton-AI-controller/releases) page.
2. Open the DMG file, and drag and drop `JINBEIBLETON.app` into your macOS **Applications** folder.
3. If macOS displays an error saying the app **"is damaged and can't be opened"**, double-click **`JINBEIBLETON起動アシスタント.command`** in the DMG volume. It will automatically bypass the Gatekeeper blocks and launch the app for you.
4. Read the `README_SETUP.txt` included in the DMG volume for details.

1. [Releases](https://github.com/MitsunoriIkeda/for-ableton-AI-controller/releases) ページから `JINBEIBLETON-1.1.0-arm64.dmg` をダウンロードします。
2. DMGファイルを開き、`JINBEIBLETON.app` を macOS の **「アプリケーション」** フォルダにドラッグ＆ドロップしてコピーします。
3. 初回起動時に **「"JINBEIBLETON"は破損しているため開けません」** というエラーが出る（またはシステム設定に「このまま開く」が表示されない）場合は、DMGに同梱されている **`JINBEIBLETON起動アシスタント.command`** をダブルクリックして起動してください。セキュリティブロックを自動解除してアプリを立ち上げます。
4. 詳細はDMGに同梱されている `README_SETUP.txt` をご確認ください。

### 2. MIDI Remote Script Setup / MIDIスクリプトの設定
JINBEIBLETON seamlessly automates the MIDI Remote Script installation:
JINBEIBLETONは、接続に必要なMIDIリモートスクリプトの配置を完全に自動化しています：

- **Automatic Setup / 自動セットアップ**:
  Simply launch the installed `JINBEIBLETON` app. Upon booting up, it will automatically copy the required `AbletonJS` MIDI Remote Script directly into your User Library (`~/Music/Ableton/User Library/Remote Scripts/AbletonJS`). No manual scripts or terminal command executions are required!
  インストールした `JINBEIBLETON` アプリを起動するだけで、接続スクリプトである `AbletonJS` フォルダが自動的にユーザーライブラリ（`~/Music/Ableton/User Library/Remote Scripts/AbletonJS`）に配置されます。手動でのコピーやコマンド実行は一切不要です！

### 3. Ableton Live Preferences / Ableton Live側の設定
1. Open (or restart) Ableton Live.
2. Open Preferences/Settings (`Command + ,`) and go to the **Link/Tempo/MIDI** tab.
3. Under **Control Surface**, select **`AbletonJS`** from the dropdown list.
4. Input and Output columns can be left as **None** (JINBEIBLETON communicates directly using UDP sockets, not standard MIDI).
5. Close Settings. The top-right indicator should display `✅ Ableton Connected`.

1. Ableton Live を起動（または再起動）します。
2. Ableton Liveの **環境設定** (`Command + ,`) を開き、**Link/Tempo/MIDI** タブを選択します。
3. **コントロールサーフェス** の一覧から、**`AbletonJS`** を選択します。
4. 入力（Input）および出力（Output）のポートは **「なし (None)」** のままで構いません（JINBEIBLETONはMIDIではなくUDPソケット経由で通信します）。
5. 設定画面を閉じます。アプリの右上に `✅ Ableton Connected` と表示されれば接続完了です！

### 4. Local AI Music Gen (MLX Engine) First-Use / ローカルAI生成の初回利用について
- When you run sample generation in **LOCAL (MLX)** engine for the first time, JINBEIBLETON will automatically download the high-fidelity weights (~3.5GB) from Hugging Face to `~/.jinbeibleton/.hf_cache` in the background.
- This is a one-time download. Once cached, all subsequent local music generations run 100% offline and execute instantly.

- **LOCAL (MLX)** エンジンでのサンプル生成を初めて行う際、バックグラウンドで自動的にHugging Faceから高精度モデル（約3.5GB）を `~/.jinbeibleton/.hf_cache` へダウンロードします。
- このダウンロードは初回1回のみです。一度キャッシュされれば、2回目以降は完全オフライン・通信なしで瞬時に生成が行われます。

---

## 📝 License & Notes / ライセンスと注意点
- This software is optimized for Apple Silicon Macs.
- Please obtain your own Google Gemini API key to use the cloud AI features.

- 本ソフトウェアは Apple Silicon (M1以上) のMacに最適化されています。
- クラウドAI機能を利用するには、ご自身でGoogle Gemini APIキーを取得し、アプリの設定に入力してください。

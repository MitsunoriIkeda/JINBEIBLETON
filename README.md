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
1. Download `JINBEIBLETON-arm64.zip` from the [Releases](https://github.com/MitsunoriIkeda/for-ableton-AI-controller/releases) page.
2. Unzip the file to find the `JINBEIBLETON_vX.Y.Z` folder.
3. Drag and drop `JINBEIBLETON.app` into your macOS **Applications** folder.

1. [Releases](https://github.com/MitsunoriIkeda/for-ableton-AI-controller/releases) ページから `JINBEIBLETON-arm64.zip` をダウンロードします。
2. ZIPファイルを解凍し、`JINBEIBLETON_vX.Y.Z` フォルダを取り出します。
3. `JINBEIBLETON.app` を macOS の **「アプリケーション」** フォルダにドラッグ＆ドロップしてコピーします。

### 2. MIDI Remote Script Setup / MIDIスクリプトの設定
To sync the app with Ableton Live, you need to install the custom MIDI Remote Script.
アプリとAbleton Liveを同期するために、専用のMIDIリモートスクリプトを配置する必要があります。

- **Automatic Install / 自動インストール**:
  Run the `install_midi_script.sh` included in the unzipped folder.
  解凍したフォルダ内にある `install_midi_script.sh` を実行すると自動で配置されます。

- **Manual Install / 手動インストール**:
  Copy the `midi-script/JINBEIBLETON` folder to the following location depending on your Live version:  
  お使いのLiveのバージョンに合わせて、`midi-script/JINBEIBLETON` フォルダを以下の場所に直接コピーしてください：
  
  - **Ableton Live 11**:  
    `/Applications/Ableton Live 11 Suite.app/Contents/App-Resources/MIDI Remote Scripts/`  
    *(Right-click Ableton Live app -> "Show Package Contents" to navigate / アプリを右クリックして「パッケージの内容を表示」から開きます)*
  - **Ableton Live 12**:  
    `/Users/[YourUsername]/Music/Ableton/User Library/Remote Scripts/`

### 3. Ableton Live Preferences / Ableton Live側の設定
1. Open Ableton Live's **Preferences** (`Command + ,`) and go to the **Link/Tempo/MIDI** (or **MIDI**) tab.
2. Under **Control Surfaces**, select **`JINBEIBLETON`** from the dropdown list.
3. Set the Input and Output ports to the virtual MIDI port automatically created by the JINBEIBLETON app.

1. Ableton Liveの **環境設定** (`Command + ,`) を開き、**Link/Tempo/MIDI**（または **MIDI**）タブを選択します。
2. **コントロールサーフェス** の一覧から、**`JINBEIBLETON`** を選択します。
3. 入力および出力を、JINBEIBLETONアプリが自動生成する仮想MIDIポートに設定します。

---

## 📝 License & Notes / ライセンスと注意点
- This software is optimized for Apple Silicon Macs.
- Please obtain your own Google Gemini API key to use the cloud AI features.

- 本ソフトウェアは Apple Silicon (M1以上) のMacに最適化されています。
- クラウドAI機能を利用するには、ご自身でGoogle Gemini APIキーを取得し、アプリの設定に入力してください。

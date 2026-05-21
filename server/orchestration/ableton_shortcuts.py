"""
Ableton Live 11 & 12 Keyboard Shortcuts Database (macOS)
Official Manual Complete Version.
Structured for keyword-based search by the Dog Advisor engine.
"""

ABLETON_SHORTCUTS = [
    # ===== ESSENTIALS (復元) =====
    {"keywords": ["保存", "save", "セーブ"], "shortcut": "⌘+S", "description": "Liveセットを保存"},
    {"keywords": ["書き出し", "export", "エクスポート", "レンダリング", "render", "バウンス", "bounce", "wav", "mp3"], "shortcut": "⌘+Shift+R", "description": "オーディオ/ビデオをエクスポート（書き出し）"},
    {"keywords": ["元に戻す", "undo"], "shortcut": "⌘+Z", "description": "操作を元に戻す"},
    {"keywords": ["やり直す", "redo"], "shortcut": "⌘+Shift+Z", "description": "操作をやり直す"},

    # ===== 41.1 Showing and Hiding Views =====
    {"keywords": ["フルスクリーン", "全画面", "full screen"], "shortcut": "⌘+Ctrl+F", "description": "フルスクリーン表示の切り替え"},
    {"keywords": ["セカンドウィンドウ", "ダブルウィンドウ", "second window"], "shortcut": "⌘+Shift+W", "description": "セカンドウィンドウを開く/閉じる"},
    {"keywords": ["セッション", "アレンジメント", "ビュー切替", "tab"], "shortcut": "Tab", "description": "セッションビューとアレンジメントビューの切り替え"},
    {"keywords": ["デバイス", "クリップ", "切替", "detail", "detail view"], "shortcut": "Shift+Tab or F12", "description": "デバイスビューとクリップビューの切り替え"},
    {"keywords": ["ホットスワップ", "hot swap", "差し替え"], "shortcut": "Q", "description": "ホットスワップモードのオン/オフ"},
    {"keywords": ["ドラムラック", "パッド", "drum rack"], "shortcut": "D", "description": "ドラムラックの最後に選択したパッドを表示"},
    {"keywords": ["info", "インフォ", "情報", "help"], "shortcut": "Shift+?", "description": "インフォビューの表示/非表示"},
    {"keywords": ["ビデオ", "video"], "shortcut": "⌘+Option+V", "description": "ビデオウィンドウの表示/非表示"},
    {"keywords": ["ブラウザ", "browser", "サイドバー"], "shortcut": "⌘+Option+B", "description": "ブラウザーの表示/非表示"},
    {"keywords": ["概要", "オーバービュー", "overview"], "shortcut": "⌘+Option+O", "description": "オーバービューの表示/非表示"},
    {"keywords": ["入出力", "I/O", "io", "ルーティング"], "shortcut": "⌘+Option+I", "description": "I/Oセクションの表示/非表示"},
    {"keywords": ["センド", "send"], "shortcut": "⌘+Option+S", "description": "センドセクションの表示/非表示"},
    {"keywords": ["ミキサー", "mixer"], "shortcut": "⌘+Option+M", "description": "ミキサーの表示/非表示"},
    {"keywords": ["クリップビュー", "clip view"], "shortcut": "⌘+Option+3", "description": "クリップビューの表示/非表示"},
    {"keywords": ["デバイスビュー", "device view"], "shortcut": "⌘+Option+4", "description": "デバイスビューの表示/非表示"},
    {"keywords": ["グルーヴプール", "groove pool"], "shortcut": "⌘+Option+6", "description": "グルーヴプールの表示/非表示"},
    {"keywords": ["環境設定", "設定", "preferences", "プリファレンス"], "shortcut": "⌘+,", "description": "環境設定を開く"},

    # ===== 41.2 Keyboard Focus and Navigation =====
    {"keywords": ["コントロールバー", "control bar", "フォーカス"], "shortcut": "Option+0", "description": "コントロールバーにフォーカス移動"},
    {"keywords": ["セッションビュー", "focus session"], "shortcut": "Option+1", "description": "セッションビューにフォーカス移動"},
    {"keywords": ["アレンジメントビュー", "focus arrangement"], "shortcut": "Option+2", "description": "アレンジメントビューにフォーカス移動"},
    {"keywords": ["ブラウザフォーカス", "focus browser"], "shortcut": "Option+5", "description": "ブラウザーにフォーカス移動"},

    # ===== 41.4 Working with Devices and Plug-Ins =====
    {"keywords": ["グループ", "group", "グループ化"], "shortcut": "⌘+G", "description": "デバイスのグループ化（ラック作成）"},
    {"keywords": ["グループ解除", "ungroup"], "shortcut": "⌘+Shift+G", "description": "デバイスのグループ解除"},
    {"keywords": ["プラグイン", "plugin", "窓"], "shortcut": "⌘+Option+P", "description": "プラグインウィンドウの表示/非表示"},
    {"keywords": ["有効", "無効", "オンオフ", "activator", "バイパス"], "shortcut": "0", "description": "選択したデバイスのオン/オフ"},

    # ===== 41.5 Editing =====
    {"keywords": ["カット", "切り取り", "cut"], "shortcut": "⌘+X", "description": "選択項目をカット"},
    {"keywords": ["コピー", "copy"], "shortcut": "⌘+C", "description": "選択項目をコピー"},
    {"keywords": ["ペースト", "貼り付け", "paste"], "shortcut": "⌘+V", "description": "クリップボードからペースト"},
    {"keywords": ["複製", "duplicate"], "shortcut": "⌘+D", "description": "選択項目を複製"},
    {"keywords": ["削除", "消す", "delete"], "shortcut": "Backspace / Delete", "description": "選択項目を削除"},
    {"keywords": ["元に戻す", "undo"], "shortcut": "⌘+Z", "description": "操作を元に戻す"},
    {"keywords": ["やり直す", "redo"], "shortcut": "⌘+Shift+Z", "description": "操作をやり直す"},
    {"keywords": ["全選択", "select all"], "shortcut": "⌘+A", "description": "すべてを選択"},
    {"keywords": ["結合", "コンソリデート", "consolidate"], "shortcut": "⌘+J", "description": "選択範囲をクリップに結合"},
    {"keywords": ["分割", "split"], "shortcut": "⌘+E", "description": "選択位置でクリップを分割"},
    {"keywords": ["クオンタイズ", "quantize"], "shortcut": "⌘+U", "description": "MIDIノートのクオンタイズ"},
    {"keywords": ["クオンタイズ設定", "quantize settings"], "shortcut": "⌘+Shift+U", "description": "クオンタイズ設定画面を開く"},
    {"keywords": ["タイム挿入", "insert silence", "空白挿入"], "shortcut": "⌘+I", "description": "選択範囲に無音を挿入"},
    {"keywords": ["midiトラック挿入", "new midi track"], "shortcut": "⌘+Shift+T", "description": "新規MIDIトラックを挿入"},
    {"keywords": ["オーディオトラック挿入", "new audio track"], "shortcut": "⌘+T", "description": "新規オーディオトラックを挿入"},
    {"keywords": ["リターントラック挿入", "new return track"], "shortcut": "⌘+Option+T", "description": "新規リターントラックを挿入"},
    {"keywords": ["名前変更", "rename", "リネーム"], "shortcut": "⌘+R", "description": "選択項目の名前を変更"},

    # ===== 41.7 Breakpoint Envelopes (Fades/Automation) =====
    {"keywords": ["フェード", "fade", "フェードイン", "フェードアウト", "クロスフェード"], "shortcut": "⌘+Option+F", "description": "【Live12】フェード/クロスフェードを作成"},
    {"keywords": ["フェードハンドル", "fade handles"], "shortcut": "F", "description": "フェードハンドルの表示/非表示切り替え"},
    {"keywords": ["カーブ", "curve", "オートメーションカーブ"], "shortcut": "Option+ドラッグ", "description": "オートメーションにカーブをつける"},
    {"keywords": ["グリッド無視", "ignore grid"], "shortcut": "⌘+ドラッグ", "description": "グリッドを無視してオートメーションを描画"},

    # ===== 41.8 Loop Brace and Markers =====
    {"keywords": ["ループオンオフ", "loop toggle"], "shortcut": "⌘+L", "description": "ループのオン/オフ切り替え"},
    {"keywords": ["ループ倍", "double loop"], "shortcut": "⌘+上矢印", "description": "ループの長さを2倍にする"},
    {"keywords": ["ループ半分", "halve loop"], "shortcut": "⌘+下矢印", "description": "ループの長さを半分にする"},

    # ===== 41.9 Zooming, Display and Selections =====
    {"keywords": ["ズームイン", "拡大", "zoom in"], "shortcut": "+", "description": "時間軸をズームイン"},
    {"keywords": ["ズームアウト", "縮小", "zoom out"], "shortcut": "-", "description": "時間軸をズームアウト"},
    {"keywords": ["選択範囲ズーム", "zoom selection"], "shortcut": "Z", "description": "選択範囲をズームアップ"},
    {"keywords": ["全体ズームアウト", "zoom out fully"], "shortcut": "X", "description": "全体を表示するまでズームアウト"},
    {"keywords": ["高さ最適化", "optimize height"], "shortcut": "H", "description": "トラックの高さを画面に合わせる"},
    {"keywords": ["幅最適化", "optimize width"], "shortcut": "W", "description": "トラックの幅を画面に合わせる"},

    # ===== 41.11 Clip View Sample Editor =====
    {"keywords": ["リバース", "reverse", "逆再生"], "shortcut": "R", "description": "選択したオーディオクリップをリバース"},
    {"keywords": ["ワープマーカー挿入", "warp marker"], "shortcut": "⌘+I", "description": "ワープマーカーを挿入"},

    # ===== 41.12 Clip View MIDI Note Editor =====
    {"keywords": ["ノート分割", "chop notes"], "shortcut": "⌘+E", "description": "【Live12】選択したノートをグリッドで分割"},
    {"keywords": ["ノート結合", "join notes"], "shortcut": "⌘+J", "description": "選択したノートを結合"},
    {"keywords": ["ノートフィット", "fit notes"], "shortcut": "⌘+Option+J", "description": "【Live12】選択したノートを指定の時間範囲にフィットさせる"},
    {"keywords": ["ノート無効", "deactivate note"], "shortcut": "0", "description": "選択したノートのオン/オフ"},
    {"keywords": ["移調", "transpose", "半音"], "shortcut": "上/下矢印", "description": "ノートを半音ずつ移動"},
    {"keywords": ["オクターブ移調", "transpose octave"], "shortcut": "Shift+上/下矢印", "description": "ノートをオクターブずつ移動"},
    {"keywords": ["ベロシティ調整", "velocity drag"], "shortcut": "⌘+ドラッグ", "description": "選択したノートのベロシティを調整"},

    # ===== 41.13 Grid Snapping and Drawing =====
    {"keywords": ["描画モード", "draw mode", "鉛筆"], "shortcut": "B", "description": "描画モードのオン/オフ"},
    {"keywords": ["グリッド狭く", "narrow grid"], "shortcut": "⌘+1", "description": "グリッドを狭くする"},
    {"keywords": ["グリッド広く", "widen grid"], "shortcut": "⌘+2", "description": "グリッドを広くする"},
    {"keywords": ["三連符", "triplet"], "shortcut": "⌘+3", "description": "三連符グリッドの切り替え"},
    {"keywords": ["スナップ", "snap", "グリッド吸着"], "shortcut": "⌘+4", "description": "グリッドスナップのオン/オフ"},
    {"keywords": ["固定グリッド", "fixed grid"], "shortcut": "⌘+5", "description": "固定グリッドとアダプティブグリッドの切り替え"},

    # ===== 41.15 Transport & 41.16 Recording =====
    {"keywords": ["再生", "プレイ", "play", "ストップ", "停止", "再生ボタン", "再生の"], "shortcut": "Space", "description": "再生と停止の切り替え"},
    {"keywords": ["再開", "resume"], "shortcut": "Shift+Space", "description": "停止位置から再生を再開"},
    {"keywords": ["録音", "record", "録音ボタン", "録音の"], "shortcut": "F9", "description": "録音のオン/オフ"},
    {"keywords": ["アレンジメント戻る", "back to arrangement"], "shortcut": "F10", "description": "アレンジメントに戻るボタンをオンにする"},
    {"keywords": ["キャプチャ", "capture midi"], "shortcut": "⌘+Shift+C", "description": "MIDIキャプチャ（弾いた内容を後から記録）"},

    # ===== 41.22 Browser & 41.23 Similar Search =====
    {"keywords": ["ブラウザ検索", "search browser"], "shortcut": "⌘+F", "description": "ブラウザー内の検索フィールドへ移動"},
    {"keywords": ["プレビュー", "preview"], "shortcut": "Shift+Enter", "description": "ブラウザーで選択中のアイテムを試聴"},
    {"keywords": ["カラー割り当て", "assign colors"], "shortcut": "1 - 7", "description": "選択したアイテムにコレクションカラーを割り当て"},
    {"keywords": ["類似ファイル表示", "show similar files"], "shortcut": "⌘+Shift+F", "description": "【Live12】類似したサウンドのファイルを表示"},
    {"keywords": ["類似スワップ次", "next similar"], "shortcut": "⌘+右矢印", "description": "【Live12】次の類似サンプルにスワップ"},
    {"keywords": ["類似スワップ前", "prev similar"], "shortcut": "⌘+左矢印", "description": "【Live12】前の類似サンプルにスワップ"},

    {"keywords": ["モーメンタリー", "ラッチング", "momentary"], "shortcut": "キーを押し続ける", "description": "【Live12】A, B, S, Z などのキーを押し続けている間だけその機能を使用可能"},

    # ===== COMMON MANUAL CONCEPTS (INSTANT ANSWERS) =====
    {"keywords": ["コンプレッサー", "compressor", "コンプ"], "shortcut": "音の大小を均一にするエフェクト", "description": "大きな音を抑えて全体の音量を揃える（スレッショルドで基準を決め、レシオで圧縮率を決める）"},
    {"keywords": ["イコライザー", "eq", "eq eight"], "shortcut": "周波数帯域の調整", "description": "特定の高さの音（低音や高音）をカットしたりブーストしたりする"},
    {"keywords": ["リバーブ", "reverb", "残響"], "shortcut": "空間の響きを追加", "description": "お風呂やコンサートホールのような残響音（エコー）を加える"},
    {"keywords": ["ディレイ", "delay", "やまびこ"], "shortcut": "やまびこ効果", "description": "入力された音を遅らせて繰り返し再生する（フィードバックで回数を調整）"},
    {"keywords": ["オートメーション", "automation", "動き"], "shortcut": "時間経過によるパラメータ変化", "description": "ボリュームやエフェクトのかかり具合を、曲の進行に合わせて自動で変化させる機能"},
    {"keywords": ["ワープ", "warp", "テンポ合わせ"], "shortcut": "オーディオのテンポ同期", "description": "オーディオサンプルのテンポを、プロジェクトのBPMに自動で合わせる機能"},
    {"keywords": ["ルーティング", "routing", "入出力"], "shortcut": "信号の通り道を設定", "description": "音声やMIDIがどのトラックから入って、どこへ出力されるかを決める設定"},
    {"keywords": ["センド", "リターン", "send", "return"], "shortcut": "エフェクトの共有", "description": "複数のトラックから共通のエフェクト（リバーブなど）に音を送って効率的に処理する仕組み"},
    {"keywords": ["マスタリング", "mastering", "マスター"], "shortcut": "最終的な音圧と音質調整", "description": "マスタートラックにリミッターやEQを挿して、曲全体の音量とバランスを市販曲レベルに整える工程"},
]

# Utility: search shortcuts by query text
def search_shortcuts(query: str, max_results: int = 5) -> list:
    """Search the shortcuts database using keyword matching."""
    noise_words = ["ショートカット", "shortcut", "教えて", "ください", "の", "は", "？", "か", "を", "って", "どうやる", "どうする", "やり方", "方法", "ボタン", "する", "したい"]
    clean_query = query.lower()
    for word in noise_words:
        clean_query = clean_query.replace(word, "")
    
    clean_query = clean_query.strip()
    if not clean_query:
        return []

    results = []
    
    for entry in ABLETON_SHORTCUTS:
        score = 0
        for kw in entry["keywords"]:
            kw_lower = kw.lower()
            # Precise matching
            if kw_lower == clean_query:
                score += 10 # Exact match
            elif kw_lower in clean_query or clean_query in kw_lower:
                score += 3
            else:
                # Sub-token matching (e.g. "やり直" matches "やり直す")
                if len(clean_query) >= 2 and len(kw_lower) >= 2:
                    if clean_query[:2] == kw_lower[:2]:
                        score += 1
                        
        if score > 0:
            results.append({"score": score, **entry})
    
    # Sort by score DESC, then by keyword length (to prioritize specific matches)
    results.sort(key=lambda x: (x["score"], len(x["keywords"])), reverse=True)
    return results[:max_results]

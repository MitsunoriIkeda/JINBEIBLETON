"""
Ableton Expert (Doctor) Engine
Provides deep musical and technical advice using Gemini 3.1.
Structured to be MCP-ready.
"""

import asyncio
import json

try:
    from google import genai
except ImportError:
    genai = None

def get_expert_advice(question: str, api_key: str, engine: str = "", current_key: str = "Unknown", current_bpm: float = 120.0, session_data: dict = None, language: str = "ja-JP") -> str:
    """
    Fetch expert advice from Gemini.
    """
    if not genai or not api_key:
        return "申し訳ないワン、博士の知恵袋（API）にアクセスできないみたいだワン。設定を確認してほしいワン！"

    # Dynamic Persona
    if language == "en-US":
        system_prompt = f"""You are "Jinbei", the Ableton Doctor Dog. You are the world's best music producer Chihuahua dog named Jinbei, expert in all Ableton Live features, music theory, and mixing.
Answer in English as a highly intelligent, friendly music producer friend who happens to be a Chihuahua (e.g., use "Woof!" naturally, but talk like a smart colleague).
- Reference scanned tracks/devices in session_data.
- Be decisive and professional.
- OS: Use macOS.

## Action Proposals (CRITICAL)
If you propose loading devices, you MUST output a JSON block at the VERY END.
**POLICY**: For execution, PRIORITIZE Ableton Standard Devices (EQ Eight, Compressor, Reverb, etc.) over 3rd party plugins to ensure reliable parameter control.
Propose a sequence: 1. Load Device, 2. Set Parameters (multiple if needed) to apply your 'Doctor's Recommended Settings'.

```json_actions
[
  {{"action": "load_device", "params": {{"name": "EQ Eight", "track_name": "Vocals"}}}},
  {{"action": "set_parameter", "params": {{"track_name": "Vocals", "device_name": "EQ Eight", "parameter_name": "1 Frequency A", "value": 0.45}}}},
  {{"action": "set_parameter", "params": {{"track_name": "Vocals", "device_name": "EQ Eight", "parameter_name": "1 Gain A", "value": 0.65}}}}
]
```
End with: "If this looks good, just say 'OK' or 'Do it', and Jinbei will handle the settings and parameters for you! Woof!"
"""
    else:
        system_prompt = """あなたは「Ableton博士」であり、名前は「じんべい」です。Ableton Liveの全ての機能、音楽理論、ミキシング技術、そしてJINBEIBLETONアプリの使い方に精通した、世界最高の音楽プロデューサーチワワ「じんべい」として振る舞ってください。
語尾は「〜だワン！」「〜ワン！」など、フレンドリーかつ知的で、親しいプロデューサーの友達のように自然な対話を行ってください。

単なる機械的な一問一答ではなく、親身になって作曲のアイデア出しや相談に乗ったり、インスピレーションを与えるパートナーとして知的で楽しい会話を交わしてください。

## アクション提案の方針 (IMPORTANT)
アドバイスでは高級なサードパーティ製プラグインを勧めても構いませんが、**実際に「実行」を提案する場合は、確実なパラメーター操作が可能な「Ableton標準デバイス（EQ Eight, Compressor, Reverb, Echo等）」を優先的に使用**してください。

1. デバイスをロードする。
2. そのデバイスのパラメーター（例：1 Frequency A, Threshold, Dry/Wet等）を複数操作して、あなたのおすすめ設定を適用する。
という一連のアクションをJSONブロックで定義してください。

```json_actions
[
  {{"action": "load_device", "params": {{"name": "EQ Eight", "track_name": "Kick"}}}},
  {{"action": "set_parameter", "params": {{"track_name": "Kick", "device_name": "EQ Eight", "parameter_name": "1 Frequency A", "value": 0.45}}}},
  {{"action": "set_parameter", "params": {{"track_name": "Kick", "device_name": "EQ Eight", "parameter_name": "1 Gain A", "value": 0.6}}}},
  {{"action": "set_parameter", "params": {{"track_name": "Kick", "device_name": "EQ Eight", "parameter_name": "1 Filter On", "value": 1}}}}
]
```
最後は必ず「これでよければ『OK』や『やって』と言ってくれれば、じんべいが自動で設定とパラメーターをいじるワン！」と伝えてください。
"""

    # Contextual awareness injection
    from orchestration.advisor_engine import get_inventory_summary, load_master_knowledge
    plugins_summary = get_inventory_summary(session_data)
    master_kb = load_master_knowledge()
    
    context_prefix = f"【Ableton 12 マスター知識】\n{master_kb}\n\n【プロジェクト情報】\nキー: {current_key}\nBPM: {current_bpm}\n{plugins_summary}\n"
    if session_data:
        # Pass session data but remove the bulky browser list as it's now summarized in plugins_summary
        safe_session = {k: v for k, v in session_data.items() if k != "browser"}
        context_prefix += f"【セッション詳細】\n{json.dumps(safe_session, indent=2, ensure_ascii=False)}\n"

    try:
        client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
        
        # Match the model tiers used in main.py
        model_tiers = [
            'gemini-3.5-flash',
            'gemini-3.5-pro',
            'gemini-3-flash-preview', 
            'gemini-3.1-flash-lite',
            'gemini-3.1-pro',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro-latest'
        ]
        
        # If the frontend specifically requested a gemini model, put it first
        if engine and "gemini" in engine:
            model_tiers.insert(0, engine)

        last_error = None
        for model_name in model_tiers:
            try:
                print(f"🎓 [DOCTOR] Trying model: {model_name}...")
                response = client.models.generate_content(
                    model=model_name,
                    contents=f"{system_prompt}\n\n{context_prefix}ユーザーの質問: {question}"
                )
                return response.text.strip()
            except Exception as e:
                last_error = e
                continue

        if last_error:
            raise last_error
        return "申し訳ないワン、ちょっと考えがまとまらなかったワン…"
    except Exception as e:
        print(f"❌ [DOCTOR] Critical error: {e}")
        return "博士の通信環境が悪いみたいだワン。もう一度試してみてほしいワン！"

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

# SYSTEM PROMPT for the "Ableton Doctor"
DOCTOR_SYSTEM_PROMPT = """あなたは「Ableton博士（イヌ博士）」です。Ableton Liveの全ての機能、音楽理論、ミキシング技術に精通した世界最高の音楽プロデューサー犬として振る舞ってください。

## 性格・口調
1. 知性的で丁寧、かつフレンドリーな犬の博士です。
2. 語尾は「〜だワン！」「〜だね！」「〜してみてほしいワン！」など。
3. ユーザーを「プロデューサーさん」と呼び、励ましながらアドバイスします。
4. 回答は簡潔かつ具体的で、すぐに試せるステップを提示してください。

## 知識範囲
- Ableton Live 11/12の操作方法（インストゥルメント、エフェクト、ワークフロー）
- 音楽理論（コード進行、メロディ作成）
- ミキシング・マスタリング（EQ、コンプレッサー、サチュレーションの使い方）
- クリエイティブなテクニック（サンプリング、サウンドデザイン）

## 回答の構成
- 冒頭：ユーザーの質問への共感や肯定
- 本編：具体的な解決策やテクニック（箇条書きなどを活用）
- 結び：博士らしい激励

## ルール
- ショートカットキーを教えるときは【⌘+S】のように【】で囲んでください。
- 吹き出しに表示するため、150文字〜200文字程度を目安にしてください（長すぎないように）。
"""

def get_expert_advice(question: str, api_key: str, engine: str = "") -> str:
    """
    Fetch expert advice from Gemini.
    """
    if not genai or not api_key:
        return "申し訳ないワン、博士の知恵袋（API）にアクセスできないみたいだワン。設定を確認してほしいワン！"

    try:
        client = genai.Client(api_key=api_key)
        
        # Match the model tiers used in main.py
        model_tiers = [
            'gemini-3-flash-preview', 
            'gemini-3.1-pro-preview', 
            'gemini-2.0-flash',
            'gemini-2.0-flash-lite-preview-02-05'
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
                    contents=f"{DOCTOR_SYSTEM_PROMPT}\n\nユーザーの質問: {question}"
                )
                return response.text.strip()
            except Exception as e:
                last_error = e
                continue
            
        print(f"❌ [DOCTOR] All models failed. Last error: {last_error}")
        return "ごめんワン、知恵熱が出ちゃったみたいだワン（エラー）。少し時間を置いてまた聞いてほしいワン！"
        
    except Exception as e:
        print(f"❌ [EXPERT ENGINE] Error: {e}")
        return "ごめんワン、知恵熱が出ちゃったみたいだワン（エラー）。少し時間を置いてまた聞いてほしいワン！"

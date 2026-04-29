"""
Ableton Dog Advisor Engine
Answers user questions about Ableton Live shortcuts and usage tips.
Uses keyword matching first, then falls back to Ollama for complex questions.
"""

from orchestration.ableton_shortcuts import search_shortcuts, ABLETON_SHORTCUTS
from orchestration.expert_engine import get_expert_advice


def get_random_advice() -> str:
    """Return a random shortcut advice from the database."""
    import random
    entry = random.choice(ABLETON_SHORTCUTS)
    return f"【{entry['shortcut']}】を使えば、{entry['description']}ができるワン！"


def get_advice(question: str, api_key: str = "", engine: str = "") -> str:
    """
    Main entry: given a user question, return a friendly dog-style answer.
    0. If empty question, return random
    1. Try keyword matching from the shortcuts DB
    2. If high-score match found, return shortcut (preserving legacy feature)
    3. If no exact shortcut match, or query seems like a "how-to", use Expert Doctor (Gemini)
    4. Fall back to local Ollama only if needed
    """
    if not question or len(question.strip()) < 1:
        return get_random_advice()
    
    # --- Step 1: Keyword Search (Shortcuts) ---
    matches = search_shortcuts(question)
    
    # If we have a very strong shortcut match (score >= 10 is exact keyword match),
    # prioritize the shortcut for speed and reliability.
    if matches and matches[0]["score"] >= 10:
        best = matches[0]
        answer = f"その操作なら【{best['shortcut']}】だワン！（{best['description']}）"
        return answer
    
    # --- Step 2: Ableton Doctor Mode (Expert Advice) ---
    # If we have a Gemini key, we go to the Doctor for better advice.
    if api_key:
        print(f"🎓 [ADVISOR] Consulting the Ableton Doctor (Gemini)...")
        return get_expert_advice(question, api_key, engine)
    
    # --- Step 3: Ollama Fallback (Local) ---
    # If no API key, fall back to local model or weak shortcut match
    if matches and matches[0]["score"] >= 1:
        best = matches[0]
        answer = f"【{best['shortcut']}】かもしれないワン！（{best['description']}）"
        return answer

    try:
        return _ask_ollama(question)
    except Exception as e:
        print(f"❌ [ADVISOR] Ollama fallback failed: {e}")
        return "ごめんワン、ちょっとわからないワン…もう少し具体的に聞いてくれると博士も助かるワン！"


def _ask_ollama(question: str) -> str:
    """Use Ollama (Gemma4) with shortcut context to answer complex questions."""
    import ollama
    
    # Build a compact context from the shortcuts DB
    shortcut_context = "\n".join(
        f"- {e['shortcut']}: {e['description']} (キーワード: {', '.join(e['keywords'][:3])})"
        for e in ABLETON_SHORTCUTS
    )
    
    system_prompt = f"""あなたはAbleton Liveの使い方に詳しい、フレンドリーな犬のアドバイザーです。
以下のショートカット一覧を参考に、ユーザーの質問に簡潔に答えてください。

## ルール
1. 回答は日本語で、犬っぽい親しみやすい口調で答えること（例：「〜だよ！」「〜だワン！」）
2. ショートカットキーは必ず【】で囲むこと（例：【⌘+S】）
3. 回答は2-3文以内に収めること（吹き出しに表示するため短く）
4. macOSのショートカットで答えること
5. わからない場合は正直に「わからない」と答えること

## Ableton Live ショートカット一覧
{shortcut_context}
"""
    
    response = ollama.chat(
        model="gemma4:latest",
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': question}
        ]
    )
    
    answer = response['message']['content'].strip()
    
    # Ensure it's not too long for a speech bubble (max ~100 chars)
    if len(answer) > 150:
        # Truncate intelligently at sentence boundary
        sentences = answer.split('。')
        short = sentences[0] + '。'
        if len(sentences) > 1 and len(short + sentences[1]) < 150:
            short += sentences[1] + '。'
        answer = short
    
    return answer

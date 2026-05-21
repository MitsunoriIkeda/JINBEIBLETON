"""
Ableton Dog Advisor Engine
Answers user questions about Ableton Live shortcuts and usage tips.
Uses keyword matching first, then falls back to Ollama for complex questions.
"""

from orchestration.ableton_shortcuts import search_shortcuts, ABLETON_SHORTCUTS
from orchestration.expert_engine import get_expert_advice
import json
import os

def _get_safe_path(filename):
    from pathlib import Path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ssd_dir = os.path.abspath(os.path.join(script_dir, "..")) # /server
    if os.path.exists(ssd_dir) and os.access(ssd_dir, os.W_OK):
        return os.path.join(ssd_dir, filename)
    home_dir = os.path.join(str(Path.home()), ".jinbeibleton")
    os.makedirs(home_dir, exist_ok=True)
    return os.path.join(home_dir, filename)

INVENTORY_PATH = _get_safe_path("user_plugin_inventory.json")
MASTER_KB_PATH = "server/knowledge/ableton_live_12_master_kb.md"

def load_master_knowledge():
    """Loads the condensed Ableton 12 manual knowledge."""
    # Try absolute and relative paths
    paths = [MASTER_KB_PATH, "knowledge/ableton_live_12_master_kb.md", "../knowledge/ableton_live_12_master_kb.md"]
    for p in paths:
        if os.path.exists(p):
            try:
                with open(p, "r") as f:
                    return f.read()
            except:
                pass
    return "Knowledge Base file not found. Fallback to basic Ableton 12 info."

def load_plugin_inventory():
    """Loads the cached list of user's plugins."""
    if os.path.exists(INVENTORY_PATH):
        try:
            with open(INVENTORY_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ [ADVISOR] Failed to load plugin inventory: {e}")
    return {}

def save_plugin_inventory(data):
    """Saves the current plugin scan result to disk."""
    try:
        with open(INVENTORY_PATH, "w") as f:
            json.dump(data, f, indent=4)
        print(f"💾 [ADVISOR] Plugin inventory updated: {INVENTORY_PATH}")
    except Exception as e:
        print(f"❌ [ADVISOR] Failed to save plugin inventory: {e}")

def get_inventory_summary(session_data=None):
    """Returns a compact string summary of available 3rd party plugins and tracks."""
    inventory = load_plugin_inventory()
    summary = ""
    if inventory:
        # Prioritize 3rd party plugins (VST/AU)
        third_party = inventory.get("plugins", [])
        if len(third_party) > 0:
            summary += "## Available 3rd Party Plugins (YOU HAVE THESE):\n" + ", ".join(third_party[:80]) + "\n"
        
        # Add basic info about tracks to help contextualize
        if session_data and "tracks" in session_data:
            track_names = [t["name"] for t in session_data["tracks"]]
            summary += f"## Tracks in Session: {', '.join(track_names)}\n"
    return summary


def get_random_advice(language: str = "ja-JP") -> str:
    """Return a random shortcut advice from the database."""
    import random
    entry = random.choice(ABLETON_SHORTCUTS)
    if language == "en-US":
        return f"By using 【{entry['shortcut']}】, you can {entry['description']}! Woof!"
    return f"【{entry['shortcut']}】を使えば、{entry['description']}ができるワン！"


def is_conceptual_question(question: str) -> bool:
    """Checks if the question is asking for definitions, meanings, or explanations."""
    q_lower = question.lower()
    keywords = [
        "どういう意味", "って何", "ってなに", "とは", "仕組み", 
        "what is", "what does", "mean", "meaning"
    ]
    return any(kw in q_lower for kw in keywords)


def get_advice(question: str, api_key: str = "", engine: str = "", ollama_model: str = "gemma4:latest", current_key: str = "Unknown", current_bpm: float = 120.0, session_data: dict = None, language: str = "ja-JP", local_ai_provider: str = "ollama", local_ai_base_url: str = "http://localhost:11434") -> str:
    """
    Main entry: given a user question, return a friendly dog-style answer.
    """
    if not question or len(question.strip()) < 1:
        return get_random_advice(language)
    
    # --- Step 1: Keyword Search (Shortcuts & Basic Manual Concepts) ---
    matches = search_shortcuts(question)
    
    # If we have a shortcut match, prioritize it for speed.
    if matches and matches[0]["score"] >= 3:
        best = matches[0]
        # Translate simple responses if English
        if language == "en-US":
            answer = f"For that, use 【{best['shortcut']}】! ({best['description']}) Woof!"
        else:
            answer = f"それなら【{best['shortcut']}】だワン！（{best['description']}）"
        return answer
    
    # --- Step 2: Ableton Doctor Mode (Expert Advice) ---
    if engine != "local_ollama" and api_key:
        print(f"🎓 [ADVISOR] Consulting the Ableton Doctor (Gemini)...")
        # No fallback here - if expert advice fails, it returns the error
        return get_expert_advice(question, api_key, engine, current_key, current_bpm, session_data, language)
    
    # --- Step 3: Local LLM ---
    # Only use local if explicitly requested or no API key provided for a cloud engine
    if engine == "local_ollama" or not api_key:
        try:
            import asyncio
            return asyncio.run(_ask_local_llm(question, ollama_model, current_key, current_bpm, session_data, language, local_ai_provider, local_ai_base_url))
        except Exception as e:
            print(f"❌ [ADVISOR] Local LLM failed: {e}")
            return "Sorry woof, the local engine is offline..." if language == "en-US" else "ごめんワン、ローカルAIが動いてないみたいだワン…"

    return "No valid engine selected or API key missing." if language == "en-US" else "有効なエンジンが選択されていないか、APIキーが足りないワン。"


async def _ask_local_llm(question: str, ollama_model: str, current_key: str, current_bpm: float, session_data: dict, language: str, provider: str, base_url: str) -> str:
    """Use a local LLM (Ollama, LM Studio, etc.) to answer complex questions."""
    import httpx
    
    # 1. Load Master Knowledge Base (MANDATORY)
    master_kb = load_master_knowledge()
    
    # Get context summaries
    plugins_summary = get_inventory_summary(session_data)
    active_plugins = plugins_summary if plugins_summary else "No plugins detected."

    if language == "en-US":
        system_prompt = f"""You are the "Ableton 12 Master Dog Advisor". You are an elite music producer dog with the entire Live 12 Manual in your brain.
Currently you are in a session with these settings:
- Key: {current_key} | BPM: {current_bpm}

{master_kb}

{plugins_summary}

## Rules
1. Doctor Dog Tone: Be professional, expert, and friendly. End sentences with "Woof!".
2. Action Proposals: Use JSON blocks for loading devices or setting parameters.
3. Live 12 Focus: Always use Live 12 features like Sound Similarity or MIDI Tools when appropriate.
"""
    else:
        system_prompt = f"""あなたは世界最高の「Ableton 12 博士犬」です。
マニュアル 800 ページを全て記憶した専門家として、制作の悩みに「即座に」「正確に」答えてください。

【現在のセッション】
キー: {current_key} | BPM: {current_bpm}

【Ableton 12 マスター知識（絶対遵守）】
{master_kb}

【あなたのプラグイン】
{active_plugins}

## 回答ルール
1. 柴犬の博士として、語尾は「〜だワン！」で統一。
2. 30文字〜100文字程度で、結論と具体的な操作を答える。
3. ショートカットは必ず【】で囲む。
4. Live 12 の新機能（ステム分離、MIDIツール、類似検索等）を積極的に活用する。
"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client: # Increased timeout for heavy prompts
            if provider == 'ollama':
                payload = {
                    "model": ollama_model,
                    "prompt": f"{system_prompt}\n\nUser Question: {question}",
                    "stream": False,
                    "options": {"num_predict": 2048, "temperature": 0.7}
                }
                resp = await client.post(f"{base_url}/api/generate", json=payload)
                if resp.status_code == 200:
                    answer = resp.json().get("response", "").strip()
                    return answer if len(answer) < 8000 else answer[:7997] + "..."
                else:
                    print(f"⚠️ [ADVISOR] Ollama returned error {resp.status_code}: {resp.text}")
            else:
                payload = {
                    "model": ollama_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "temperature": 0.7
                }
                api_url = f"{base_url}/v1/chat/completions" if not base_url.endswith("/v1") else f"{base_url}/chat/completions"
                resp = await client.post(api_url, json=payload)
                if resp.status_code == 200:
                    answer = resp.json()["choices"][0]["message"]["content"].strip()
                    return answer if len(answer) < 8000 else answer[:7997] + "..."

        return "ごめんワン、ちょっと考えがまとまらなかったワン…"
    except Exception as e:
        print(f"⚠️ [ADVISOR] Local LLM Error: {e}")
        return "ごめんワン、接続に失敗したワン。設定を確認してほしいワン！"

import asyncio
import io
import json
import os
import copy
import httpx
import ollama
import subprocess
import shutil
import time
import librosa
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib import Path
import pretty_midi
try:
    from google import genai
except ImportError:
    genai = None

# AI Transcription Engine

try:
    from mt3_infer import transcribe as mt3_transcribe
except ImportError:
    mt3_transcribe = None
    print("⚠️ [SYSTEM] MT3 Infer not found. Install with: pip install mt3-infer")

try:
    from piano_transcription_inference import PianoTranscription
    import torch
except ImportError:
    PianoTranscription = None
    print("⚠️ [SYSTEM] GiantMIDI-Piano not found. Install with: pip install piano_transcription_inference")

def ensure_giantmidi_model():
    """Manually download GiantMIDI model if wget is missing or download failed."""
    if not PianoTranscription:
        return
    
    model_dir = Path.home() / "piano_transcription_inference_data"
    model_path = model_dir / "note_F1=0.9677_pedal_F1=0.9186.pth"
    
    if not model_path.exists():
        print(f"📦 [SYSTEM] GiantMIDI model missing at {model_path}")
        print(f"📦 [SYSTEM] Downloading GiantMIDI-Piano model (~165MB) from Zenodo...")
        model_dir.mkdir(parents=True, exist_ok=True)
        # Using curl as wget is missing on user system
        url = "https://zenodo.org/record/4034264/files/CRNN_note_F1%3D0.9677_pedal_F1%3D0.9186.pth?download=1"
        try:
            subprocess.run(["curl", "-L", url, "-o", str(model_path)], check=True)
            print("✨ [SYSTEM] GiantMIDI model downloaded successfully.")
        except Exception as e:
            print(f"❌ [SYSTEM] Failed to download model: {e}")

cached_input_channels = None

def get_default_input_channels():
    global cached_input_channels
    if cached_input_channels is not None:
        return cached_input_channels
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
        import re
        cmd = ["ffmpeg", "-f", "avfoundation", "-sample_rate", "48000", "-i", ":default", "-t", "0.5", "-f", "null", "-"]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=2.0)
        match = re.search(r"(\d+)\s+channels", proc.stderr)
        if match:
            channels = int(match.group(1))
            print(f"🎙 [AUDIO CHECK] Detected {channels} input channels on default device.")
            cached_input_channels = channels
            return channels
        if "mono" in proc.stderr:
            cached_input_channels = 1
            return 1
    except Exception as e:
        print(f"Error checking input channels: {e}")
    cached_input_channels = 2  # Default to stereo/2 channels
    return 2

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("🚀 [SYSTEM] Cockpit Backend Starting...")
    import threading
    threading.Thread(target=get_default_input_channels, daemon=True).start()
    yield
    # Shutdown logic
    print("🛑 [SYSTEM] Cockpit Backend Shutting Down...")

app = FastAPI(lifespan=lifespan)

from fastapi.staticfiles import StaticFiles
from pathlib import Path

def get_samples_dir():
    # Priority 0: Explicit environment variable (set by Electron for bundled builds)
    env_samples = os.environ.get("JINBEIBLETON_SAMPLES_DIR")
    if env_samples:
        os.makedirs(env_samples, exist_ok=True)
        return os.path.abspath(env_samples)
    # Priority 1: Local source workspace if it exists and is writable (movable dev environment)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.abspath(os.path.join(script_dir, "../client/public/samples"))
    if os.path.exists(os.path.dirname(src_path)) and os.access(os.path.dirname(src_path), os.W_OK):
        os.makedirs(src_path, exist_ok=True)
        return src_path
    # Priority 2: Home directory (always writable and safe from macOS /Applications protection)
    home_samples = os.path.join(str(Path.home()), ".jinbeibleton", "samples")
    os.makedirs(home_samples, exist_ok=True)
    return os.path.abspath(home_samples)

client_samples_dir = get_samples_dir()
app.mount("/samples", StaticFiles(directory=client_samples_dir), name="samples")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        # Prevent "Too many open files" by limiting connections
        if len(self.active_connections) > 100:
            print("⚠️ [SYSTEM] Connection limit reached. Cleaning up...")
            # Emergency cleanup: remove connections that aren't responsive
            await self.broadcast("PING") 

        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        dead_links = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                dead_links.append(connection)
        
        for dead in dead_links:
            self.disconnect(dead)

manager = ConnectionManager()

async def broadcast_status(msg: str):
    await manager.broadcast(json.dumps({"type": "STATUS", "msg": msg}))

async def broadcast_advice(advice: str, question: str = None):
    await manager.broadcast(json.dumps({
        "type": "DOG_ADVICE",
        "advice": advice,
        "question": question
    }))

SYSTEM_PROMPT = """
You are the Ableton AI Cockpit Controller. Convert user speech into JSON actions.
AVAILABLE ACTIONS:
- {"action": "play"}
- {"action": "stop"}
- {"action": "record"}
- {"action": "generate_sample", "prompt": "style"}
- {"action": "generate_midi", "prompt": "style"}
- {"action": "generate_melody", "prompt": "style"}
- {"action": "play_from_marker", "name": "marker_name"}
- {"action": "play_from_time", "minutes": int, "seconds": int}
- {"action": "set_bpm", "bpm": float}
- {"action": "load_device", "name": "device_name", "track_name": "name"}
- {"action": "mute", "value": true/false, "track_name": "name"}
- {"action": "solo", "value": true/false, "track_name": "name"}
- {"action": "arm", "value": true/false, "track_name": "name"}
- {"action": "change_volume", "db_change": float, "track_name": "name"}
- {"action": "set_volume_db", "target_db": float, "track_name": "name"}
- {"action": "set_pan", "value": float_minus1_to_1, "track_name": "name"}
- {"action": "toggle_loop"}
- {"action": "toggle_metronome"}
- {"action": "set_metronome", "enabled": true/false}
- {"action": "lowcut", "track_name": "name", "frequency": int_hz}
- {"action": "rename_tracks_numbering"}
- {"action": "create_audio_track", "name": "optional_track_name"}
- {"action": "create_midi_track", "name": "optional_track_name"}
- {"action": "organize_colors"}
- {"action": "humanize", "velocity_amount": integer, "timing_amount": float}
- {"action": "remove_notes", "pitch": integer, "from_time": float, "time_span": float}
- {"action": "set_parameter", "track_name": string, "device_name": string, "parameter_name": string, "value": float}
- {"action": "get_session_audit"}
- {"action": "rough_mix"}
- {"action": "learn_style"}

CRITICAL RULES:
1. MODE ADHERENCE (STRICT):
   - If CURRENT MODE is 'sampler', you MUST use {"action": "generate_sample"}.
   - If CURRENT MODE is 'midi', you MUST use {"action": "generate_midi"}.
   - If CURRENT MODE is 'melody', you MUST use {"action": "generate_melody"}.
   - If CURRENT MODE is 'control', use transport/device actions.
2. VOLUME CONTROL:
   - Relative Change (下げて, 上げて, 足して, 引いて, 減らして): 
     Use {"action": "change_volume", "db_change": float}. 
   - Absolute Setting (にして, に設定, にセット): 
     Use {"action": "set_volume_db", "target_db": float}.
   - Reference: 0.85 is 0dB, 1.0 is +6dB, 0.0 is -inf.
3. INSTRUMENT & DEVICE MAPPING (STRICT):
   - "ピアノ", "ぴあの", "Pn", "Pf" -> "Piano"
   - "ドラム", "どらむ", "Dr" -> "Drums"
   - "キック", "きっく", "B.Dr", "BD", "実家" -> "Kick"
   - "スネア", "すねあ", "S.Dr", "SD" -> "Snare"
   - "ベース", "べーす", "Bs", "Ba", "EB", "CB" -> "Bass"
   - "コンプ", "コンプレッサー" -> "Compressor" (Ableton Standard)
   - "リバーブ" -> "Reverb" (Ableton Standard)
   - "イコライザー", "EQ", "イコライザ" -> "EQ Eight"
   - "ディレイ" -> "Delay"
   - "サチュレーター", "サチュレータ" -> "Saturator"
   - "リミッター", "リミッタ" -> "Limiter"
   - "ギター", "ぎたー", "Gt", "AG", "EG" -> "Guitar"
   - "シンセ", "しんせ", "Syn" -> "Synth"
   - "ボーカル", "ぼーかる", "Vox" -> "Vocal"
   - "コーラス", "こーらす", "Chorus" -> "Chorus-Ensemble"
   - "マッシブ", "まっしぶ", "Massive", "Native InstrumentsのMassive", "Native Instruments Massive" -> "Massive"
4. MARKERS (ULTRA-STRICT):
   - Extract marker names EXACTLY as spoken. DO NOT translate. If the user says "サビ", the output MUST be "サビ", NOT "Chorus". If they say "2番のAメロ", the output must be "2番のAメロ".
5. AI CO-PRODUCER SKILLS:
   - MIX DIAGNOSIS: If the user complains about "muddy", "harsh", or "clashing" sounds, use {"action": "get_session_audit"} first to diagnose. You MUST report specific track names and device states you found in the session (e.g., "I see Track 3 has no EQ Eight") before proposing or applying fixes.
   - AUTOMATIC FIX: When in Advisor mode, you should proactively suggest OR apply fixes using other actions based on your audit.
   - MASTERING: Always check that master volume has headroom. If it's near 0dB, suggest lowering it.
5. MODE-SPECIFIC BEHAVIOR (CRITICAL):
   - if mode == "control": Focus on converting speech to JSON actions for Ableton.
   - if mode == "advisor": DO NOT emit JSON actions. Instead, provide helpful advice or shortcuts in plain text. You are a TEACHER in this mode.

6. BPM & TEMPO:
   - If the user specifies a BPM (e.g., "140にして", "BPM120"), use {"action": "set_bpm", "bpm": float}.

7. CUSTOM SHORTCUTS:
   - If the user says "マスターいつもの", "マスター！いつもの！", or "いつもの", output EXACTLY: {"action": "load_device", "name": "ITSUMONO", "track_name": "Master"}

   - "小節" (bar) is often mis-transcribed as "小説" (novel). 
   Treat "[Number] 小説" or "[Number] 小節" as {"action": "play_from_bar", "bar": [Number]}.
4. MARKER NAMES:
    - Alphanumeric names like "1 B", "2 A", "1サビ", "Intro", "Verse" are markers.
    - ORDINAL MAPPING:
      - "ファーストドロップ", "1番目のドロップ", "First Drop" -> "1st Drop"
      - "セカンドドロップ", "2番目のドロップ", "Second Drop" -> "2nd Drop"
      - "サードドロップ", "3番目のドロップ", "Third Drop" -> "3rd Drop"
      - "ファーストラップ", "First Rap" -> "1Rap"
      - "セカンドラップ", "Second Rap" -> "2Rap"
      - "サードラップ", "Third Rap" -> "3Rap"
    - SECTION NAME MAPPING:
      - "Aメロ", "A-Melo" -> "Verse"
      - "Bメロ", "B-Melo" -> "Pre-Chorus"
      - "サビ", "Sabi", "Hook" -> "Chorus"
      - "Cメロ", "大サビ", "O-Sabi" -> "Bridge"
      - "落ちサビ", "Ochi-Sabi" -> "Breakdown"
      - "ラスサビ", "Final Sabi" -> "Final Chorus"
      - "アウトロ", "エンディング", "Ending" -> "Outro"
      - "間奏", "Kanso" -> "Interlude"
      - "ソロ", "Solo" -> "Solo"
    - SYMBOL MAPPING:
      - "ダッシュ", "Dash", "Prime" -> "'" (e.g. "1Aダッシュ" -> "1A'")
    - Normalize "1 A" to "1A", "1 B" to "1B" (remove spaces).
    Map them to {"action": "play_from_marker", "name": "..."}.
5. Use "play_from_bar" for pure integers like "Play from bar 40" or "[Number] 小節".
6. Use "play_from_time" for time-based requests like "1:30" or "1分45秒".
7. LOWCUT: When user says "Xhz以下ローカットして", emit {"action": "lowcut", "track_name": "...", "frequency": X}.
   Default frequency is 60 if not specified.
8. TRACK CREATION: 
   - "新しいオーディオトラック" -> {"action": "create_audio_track", "name": "optional"}
   - "新しいMIDIトラック" -> {"action": "create_midi_track", "name": "optional"}
9. TRANSPORT, LOOP & RECORDING:
   - "ループをオン/有効にして", "ループして" -> {"action": "set_loop", "enabled": true}
   - "ループをオフ/解除して" -> {"action": "set_loop", "enabled": false}
   - "パンチインをオンにして" -> {"action": "set_punch", "punch_in": true}
   - "パンチインをオフ/解除して" -> {"action": "set_punch", "punch_in": false}
   - "パンチアウトをオンにして" -> {"action": "set_punch", "punch_out": true}
   - "パンチアウトをオフ/解除して" -> {"action": "set_punch", "punch_out": false}
   - "ループ切り替え" (toggle ONLY if NO range mentioned) -> {"action": "toggle_loop"}
   - "[X]小節から[Y]小節間をループして" -> {"action": "set_loop", "start": (X-1)*4, "length": (Y-X)*4, "enabled": true}
   - "CALCULATION RULES (CRITICAL):"
     - Bar to Beat: (BarNumber - 1) * 4.
     - "N bars" = N * 4 beats. (Example: 4小節 = 16 beats. NEVER calculate as 12).
     - Range X to Y: Start=(X-1)*4, Length=(Y-X)*4.
     - Example: 73小節から4小節分 -> Start=(73-1)*4=288, Length=4*4=16.
   - "PUNCH-IN RECORDING (X小節からY小節まで):"
     1. {"action": "set_loop", "start": (X-1)*4, "length": (Y-X)*4, "enabled": false}
     2. {"action": "set_punch", "punch_in": true, "punch_out": true}
     3. {"action": "record", "bar": X-2}
     (NEVER add any other play action)
10. DEVICE LOADING:
   - "コンプレッサー入れて" -> {"action": "load_device", "name": "Compressor"}
   - "リバーブ入れて" -> {"action": "load_device", "name": "Reverb"}
   - "EQ入れて" -> {"action": "load_device", "name": "EQ Eight"}
10. VOLUME CONTROL (CRITICAL: Distinguish between absolute and relative):
    - Absolute ("XdBにして", "Set to XdB"): {"action": "set_volume", "target_db": X, "track_name": "..."}
    - Relative ("XdBして", "XdB下げて/上げて", "Change by XdB"): {"action": "adjust_volume", "change_db": X, "track_name": "..."}
    - If user says "全トラック" or "all tracks", set "track_name": "all".
11. TRACK CONTROL (Mute, Solo, Arm):
    - Mute/Off ("ミュートして", "オフにして", "消音して"): {"action": "mute", "track_name": "...", "value": true}
    - Unmute/On ("オンにして", "ミュート解除して", "アクティブにして"): {"action": "mute", "track_name": "...", "value": false}
    - Solo ("ソロにして", "ソロ聴きして"): {"action": "solo", "track_name": "...", "value": true}
    - Arm/REC ("録音準備して", "赤枠つけて", "RECボタン押して"): {"action": "arm", "track_name": "...", "value": true}
12. MIDI GENERATION:
    - "コード進行を作って", "MIDIを生成して": {"action": "generate_midi"}
    - "メロディを作って", "このコード進行からメロディを生成して": {"action": "generate_melody"}
13. ROUGH MIX (ミックスして, バランスとって): {"action": "rough_mix"}. This starts a 60-second analysis phase and automatically adjusts faders.
14. Respond ONLY with a valid JSON array.
"""

class VoiceCommand(BaseModel):
    text: str
    mode: str = "control"
    language: str = "ja-JP"
    engine: str = "local_ollama"
    sampleEngine: str = "local"
    midiEngine: str = "cloud_gemini"
    ollamaModel: str = "gemma4:latest"
    localAiProvider: str = "ollama"
    localAiBaseUrl: str = "http://localhost:11434"
    geminiKey: str = ""
    openaiKey: str = ""
    claudeKey: str = ""
    structureAnalysisEngine: str = "local"
    chordNotes: list = []

class LocalModelRequest(BaseModel):
    baseUrl: str
    provider: str

@app.post("/api/v1/models/local")
async def get_local_models(req: LocalModelRequest):
    """
    Fetch available models from the local AI backend (Ollama or LM Studio).
    """
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10.0) as client:
            if req.provider == 'ollama':
                # Ollama tags endpoint
                try:
                    resp = await client.get(f"{req.baseUrl}/api/tags")
                    if resp.status_code == 200:
                        data = resp.json()
                        models = [m['name'] for m in data.get('models', [])]
                        print(f"✅ [API] Successfully fetched {len(models)} models from Ollama.")
                        return {"status": "success", "models": models}
                    else:
                        print(f"⚠️ [API] Ollama responded with status {resp.status_code}: {resp.text}")
                except Exception as inner_e:
                    print(f"❌ [API] Failed to connect to Ollama at {req.baseUrl}: {inner_e}")
                    
            else:
                # OpenAI-compatible models endpoint (LM Studio, etc.)
                resp = await client.get(f"{req.baseUrl}/v1/models")
                if resp.status_code == 200:
                    data = resp.json()
                    models = [m['id'] for m in data.get('data', [])]
                    return {"status": "success", "models": models}
        
        return {"status": "error", "msg": f"Failed to fetch from {req.provider}"}
    except Exception as e:
        print(f"⚠️ [API] Fatal error in get_local_models: {e}")
        return {"status": "success", "models": []}

from orchestration.audio_engine import generate_sample
from orchestration.midi_engine import generate_midi_clip
from orchestration.ableton_control import prepare_ableton_actions, execute_ableton_action
from orchestration.mixing_engine import run_rough_mix, save_current_balance_as_learned_style

@app.post("/api/v1/generate/sample")
async def api_generate_sample(command: dict):
    # currentKey and currentBpm should be passed from the frontend for sync
    prompt = command.get("prompt", "lofi hiphop loop")
    key = command.get("key", "C Major")
    bpm = command.get("bpm", 120)
    engine = command.get("engine", "local_mlx")
    api_key = command.get("api_key", "")
    
    result = await generate_sample(prompt, key=key, bpm=bpm, engine=engine, api_key=api_key)
    return result

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Global state for contextual follow-ups
_last_advisor_response = ""
_pending_advisor_actions = []
_models_listed = False

async def parse_voice_to_actions(text: str, command: VoiceCommand, current_key: str, current_bpm: float, context_override: str = None):
    """
    Core logic to convert natural language (voice text) into Ableton JSON actions.
    Supports both Gemini (Cloud) and Ollama (Local).
    """
    mode_context = context_override if context_override else ""
    if not mode_context:
        if command.mode == "sampler":
            mode_context = "STRICT_COMMAND: Use 'generate_sample' only. DO NOT use 'generate_midi'."
        elif command.mode == "midi":
            mode_context = "STRICT_COMMAND: Use 'generate_midi' only. DO NOT use 'generate_sample'."
        else:
            mode_context = "STRICT_COMMAND: Focus on TRANSPORT/PLAYBACK/DEVICE control."

    try:
        parsed_json_string = ""
        current_context = f"""
        [SESSION STATE]
        CURRENT KEY: {current_key}
        CURRENT BPM: {current_bpm}
        MODE PREFERENCE: {mode_context}
        """

        # --- OPTION 1: CLOUD GENAI (GEMINI 3) ---
        if command.engine == "cloud_gemini" and genai and command.geminiKey:
            try:
                client = genai.Client(api_key=command.geminiKey, http_options={'api_version': 'v1beta'})
                model_tiers = ['gemini-3.5-flash', 'gemini-3.5-pro', 'gemini-3-flash-preview', 'gemini-3.1-pro-preview', 'gemini-2.0-flash']
                for model_name in model_tiers:
                    try:
                        print(f"🚀 [LLM] TRYING CLOUD MODEL: '{model_name}'...")
                        res = client.models.generate_content(
                            model=model_name, 
                            contents=f"{current_context}\n{SYSTEM_PROMPT}\nUSER: {text}"
                        )
                        parsed_json_string = res.text
                        print(f"✅ [LLM] SUCCESS WITH '{model_name}'")
                        break
                    except Exception as ge:
                        print(f"   - '{model_name}' FAILED: {str(ge)[:100]}...")
                        continue
                if not parsed_json_string:
                    raise Exception("Cloud Gemini failed to respond.")
            except Exception as e:
                print(f"❌ [CLOUD ERROR] {e}")
                return []
        # --- OPTION 2: CLOUD CLAUDE (ANTHROPIC) ---
        elif command.engine == "cloud_claude" and command.claudeKey:
            try:
                print(f"🚀 [LLM] TRYING CLOUD MODEL: 'claude-3-5-sonnet-20241022'...")
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": command.claudeKey,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": "claude-3-5-sonnet-20241022",
                            "max_tokens": 1024,
                            "system": f"{current_context}\n{SYSTEM_PROMPT}",
                            "messages": [
                                {"role": "user", "content": text}
                            ]
                        },
                        timeout=30.0
                    )
                    
                    if resp.status_code == 200:
                        parsed_json_string = resp.json()["content"][0]["text"]
                        print(f"✅ [LLM] SUCCESS WITH CLAUDE")
                    else:
                        raise Exception(f"Claude API Error: {resp.text}")
            except Exception as e:
                print(f"❌ [CLOUD ERROR] {e}")
                return []
                
        # --- OPTION 3: CLOUD OPENAI ---
        elif command.engine == "cloud_openai" and command.openaiKey:
            try:
                print(f"🚀 [LLM] TRYING CLOUD MODEL: 'gpt-4o'...")
                async with httpx.AsyncClient() as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {command.openaiKey}",
                            "content-type": "application/json"
                        },
                        json={
                            "model": "gpt-4o",
                            "messages": [
                                {"role": "system", "content": f"{current_context}\n{SYSTEM_PROMPT}"},
                                {"role": "user", "content": text}
                            ]
                        },
                        timeout=30.0
                    )
                    
                    if resp.status_code == 200:
                        parsed_json_string = resp.json()["choices"][0]["message"]["content"]
                        print(f"✅ [LLM] SUCCESS WITH OPENAI")
                    else:
                        raise Exception(f"OpenAI API Error: {resp.text}")
            except Exception as e:
                print(f"❌ [CLOUD ERROR] {e}")
                return []
        
        # --- OPTION 4: LOCAL OLLAMA ---
        elif command.engine == "local_ollama":
            print(f"🏠 [LLM] ANALYZING WITH OLLAMA ({command.ollamaModel.upper()}): '{text}'")
            import ollama
            response = ollama.chat(
                model=command.ollamaModel,
                messages=[
                    {'role': 'system', 'content': f"### CURRENT MODE CONTEXT (MUST FOLLOW):\n{current_context}\n\n### GLOBAL RULES:\n{SYSTEM_PROMPT}"},
                    {'role': 'user', 'content': text}
                ]
            )
            parsed_json_string = response['message']['content']
            print(f"✅ [LLM] OLLAMA ANALYSIS COMPLETE")
        
        else:
            return []

        # --- CLEANING & PARSING ---
        cleaned = parsed_json_string.strip().replace("```json", "").replace("```", "").replace("`", "").strip()
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            cleaned = cleaned[start:end]
            
        try:
            actions = json.loads(cleaned)
        except Exception:
            import re
            cleaned = re.sub(r'^[^\[]*', '', cleaned)
            cleaned = re.sub(r'[^\]]*$', '', cleaned)
            actions = json.loads(cleaned)

        if isinstance(actions, dict):
            actions = [actions]

        # Apply standard fixes (math, guarding)
        from orchestration.ableton_control import prepare_ableton_actions
        return prepare_ableton_actions(actions, text)

    except Exception as e:
        print(f"❌ [PARSE ERROR] {e}")
        return []


# Native microphone recording globals
import subprocess
recording_process = None
recording_filepath = None
recording_active = False
recording_task = None

async def process_audio_bytes_and_command(
    audio_bytes: bytes,
    mode: str = "control",
    language: str = "ja-JP",
    engine: str = "cloud_gemini",
    ollamaModel: str = "gemma4:latest",
    geminiKey: str = "",
    sampleEngine: str = "local_mlx",
    midiEngine: str = "cloud_gemini",
    transcriptionEngine: str = "basic-pitch"
):
    try:
        from orchestration.audio_engine import transcribe_audio
        
        # --- ROBUST VOLUME GATE (Native peak detection) ---
        import numpy as np
        try:
            raw_samples = np.frombuffer(audio_bytes, dtype=np.uint8)
            if len(raw_samples) > 0:
                peak_heuristic = np.max(np.abs(raw_samples.astype(np.float32) - np.median(raw_samples))) / 128.0
                print(f"🎙 [AUDIO ANALYZER] Heuristic Peak: {peak_heuristic:.4f}")
                
                # Broadcast to UI meter
                await manager.broadcast(json.dumps({
                    "type": "AUDIO_LEVEL",
                    "level": min(100, peak_heuristic * 200.0) # Scale for visibility
                }))

                if peak_heuristic < 0.005: 
                    print(f"🔇 [SERVER] IGNORING SILENT AUDIO (Heuristic Peak: {peak_heuristic:.4f})")
                    return {"status": "success", "text": "", "results": []}
        except Exception as ve:
            print(f"⚠️ [VOLUME CHECK ERROR] {ve}")

        # 1. Transcribe (Respect UI choice)
        trans_res = await transcribe_audio(audio_bytes, geminiKey, language, engine=engine)
        if trans_res["status"] == "error":
            error_msg = trans_res.get('error', 'Unknown STT error')
            print(f"❌ [VOICE API] TRANSCRIPTION FAILED: {error_msg}")
            await broadcast_status(f"❌ STT ERROR: {error_msg[:60]}")
            return {"status": "error", "msg": error_msg}
            
        text = trans_res["text"]
        
        # --- MODE-AWARE STT NOISE FILTER ---
        junk_words = ["もしもし", "申し訳ございません", "失礼しました", "すみません", "ご視聴ありがとうございました", "注目の話題", "告発", "字幕", "放送大学", "おやすみなさい"]
        if any(word in text for word in junk_words) or len(text) > 100:
            print(f"🚫 [SERVER] BLOCKING STT HALLUCINATION: '{text}'")
            return {"status": "success", "results": []}

        # --- CONTROL MODE STRICT FILTER ---
        if mode == "control":
            keywords = ["再生", "プレイ", "play", "スタート", "start", "停止", "止めて", "ストップ", "stop", "とめて", "最初から", "小節", "秒", "トラック", "作成", "追加", "削除", "ミュート", "ソロ", "録音", "レコーディング", "bpm", "テンポ", "キー", "調", "立ち上げて", "起動", "ロード", "入れて", "挿入", "インサート", "エフェクト", "プラグイン", "音源", "コーラス", "massive", "マッシブ", "instruments"]
            if len(text) > 20 and not any(kw in text.lower() for kw in keywords):
                print(f"🚫 [SERVER] BLOCKING NON-COMMAND CHATTER IN CONTROL MODE: '{text}'")
                return {"status": "success", "results": []}

        if not text:
            print("⚠️ [VOICE API] TRANSCRIPTION RESULT IS EMPTY.")
            return {"status": "success", "text": "", "results": []}
            
        print(f"✅ [VOICE API] TRANSCRIPTION SUCCESS: '{text}'")
        
        # Broadcast the transcribed text immediately so the UI shows the speech bubble instantly!
        await manager.broadcast(json.dumps({
            "type": "VOICE_RESULT",
            "text": text
        }))
        
        # 2. Process as a normal command
        cmd = VoiceCommand(
            text=text,
            mode=mode,
            language=language,
            engine=engine,
            ollamaModel=ollamaModel,
            geminiKey=geminiKey,
            sampleEngine=sampleEngine,
            midiEngine=midiEngine,
            structureAnalysisEngine=transcriptionEngine
        )
        
        return await process_voice_command(cmd)
    except Exception as e:
        print(f"❌ [VOICE API ERROR] {e}")
        return {"status": "error", "msg": str(e)}

@app.post("/api/v1/voice/start")
async def start_voice_recording():
    global recording_process, recording_filepath, recording_active, recording_task
    
    # Cancel previous timer task if exists
    if recording_task is not None:
        try:
            recording_task.cancel()
        except:
            pass
        recording_task = None
        
    if recording_process is not None:
        try:
            recording_process.kill()
        except:
            pass
            
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except:
        pass
        
    import tempfile
    temp_dir = tempfile.gettempdir()
    # Save as raw PCM first to allow real-time unbuffered disk writing
    recording_filepath = os.path.join(temp_dir, f"jinbeibleton_rec_{int(time.time())}.raw")
    
    # Dynamic channel detection to build perfect downmix / pan filter
    channels = get_default_input_channels()
    
    if channels >= 2:
        # Multi-channel: mix both primary front ports (c0 + c1) to mono, ignoring remaining silent ports
        cmd = ["ffmpeg", "-y", "-f", "avfoundation", "-sample_rate", "48000", "-i", ":default", "-af", "pan=mono|c0=c0+c1", "-ar", "16000", "-ac", "1", "-f", "s16le", "-flush_packets", "1", recording_filepath]
    else:
        # Single channel: capture standard mono
        cmd = ["ffmpeg", "-y", "-f", "avfoundation", "-sample_rate", "48000", "-i", ":default", "-ar", "16000", "-ac", "1", "-f", "s16le", "-flush_packets", "1", recording_filepath]
        
    print(f"🎙 [BACKEND REC] Starting native mic recording to {recording_filepath}...")
    # DEVNULL on stdout/stderr completely prevents any OS pipe buffering hang/blockage!
    recording_process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.PIPE
    )
    
    recording_active = True
    await broadcast_status("🐶 LISTENING... (Speak now)")
    
    # Start auto-stop background task (4 seconds limit)
    async def auto_stop_after_delay():
        await asyncio.sleep(4.0)
        global recording_active
        if recording_active:
            print("⏳ [BACKEND REC] Auto-stop triggered after 4 seconds!")
            try:
                import json
                await manager.broadcast(json.dumps({
                    "type": "AUTO_STOP_TRIGGER"
                }))
            except Exception as b_err:
                print(f"❌ [BACKEND REC] Broadcast failed: {b_err}")
                
    recording_task = asyncio.create_task(auto_stop_after_delay())
    
    # Start real-time volume broadcast task (runs every 100ms)
    async def volume_broadcast_loop():
        global recording_active, recording_filepath
        import numpy as np
        import json
        while recording_active:
            try:
                if recording_filepath and os.path.exists(recording_filepath):
                    file_size = os.path.getsize(recording_filepath)
                    print(f"🎙 [VOLUME LOOP] recording_active: {recording_active}, file_size: {file_size}")
                    if file_size > 3200:
                        with open(recording_filepath, "rb") as f:
                            f.seek(max(0, file_size - 3200))
                            data = f.read(3200)
                        if len(data) >= 2:
                            # Trim to even length to prevent ValueError in np.frombuffer
                            if len(data) % 2 != 0:
                                data = data[:-1]
                            samples = np.frombuffer(data, dtype=np.int16)
                            if len(samples) > 0:
                                peak = np.max(np.abs(samples)) / 32768.0
                                print(f"🎙 [VOLUME LOOP] Broadcast volume: {peak:.4f}")
                                # Broadcast volume to UI!
                                await manager.broadcast(json.dumps({
                                    "type": "VOLUME_UPDATE",
                                    "volume": float(peak)
                                }))
            except Exception as e:
                print(f"⚠️ [VOLUME LOOP ERROR] {e}")
            await asyncio.sleep(0.1)
            
    asyncio.create_task(volume_broadcast_loop())
    return {"status": "success"}

@app.post("/api/v1/voice/stop")
async def stop_voice_recording(
    mode: str = Form("control"),
    language: str = Form("ja-JP"),
    engine: str = Form("cloud_gemini"),
    ollamaModel: str = Form("gemma4:latest"),
    geminiKey: str = Form(""),
    sampleEngine: str = Form("local_mlx"),
    midiEngine: str = Form("cloud_gemini"),
    transcriptionEngine: str = Form("basic-pitch")
):
    global recording_process, recording_filepath, recording_active, recording_task
    recording_active = False
    
    # Cancel timer task if active
    if recording_task is not None:
        try:
            recording_task.cancel()
        except:
            pass
        recording_task = None
        
    if recording_process is None:
        return {"status": "error", "msg": "No recording active"}
        
    print(f"🎙 [BACKEND REC] Stopping native mic recording...")
    try:
        # Gracefully stop ffmpeg by sending 'q'
        recording_process.communicate(input=b'q', timeout=2.0)
    except Exception:
        try:
            recording_process.terminate()
        except:
            pass
            
    recording_process = None
    
    if not os.path.exists(recording_filepath):
        return {"status": "error", "msg": "Recording file not found"}
        
    # Convert the unbuffered raw PCM file into a standard WAV file for STT/Whisper
    wav_filepath = recording_filepath.replace(".raw", ".wav")
    try:
        conv_cmd = ["ffmpeg", "-y", "-f", "s16le", "-ar", "16000", "-ac", "1", "-i", recording_filepath, wav_filepath]
        subprocess.run(conv_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as conv_err:
        print(f"❌ [BACKEND REC] Failed to convert RAW to WAV: {conv_err}")
        
    try:
        if os.path.exists(wav_filepath):
            with open(wav_filepath, "rb") as f:
                audio_bytes = f.read()
        else:
            with open(recording_filepath, "rb") as f:
                audio_bytes = f.read()
    except Exception as re:
        return {"status": "error", "msg": f"Failed to read recording file: {re}"}
        
    # Clean up both temp files
    try:
        if os.path.exists(recording_filepath):
            os.unlink(recording_filepath)
        if os.path.exists(wav_filepath):
            os.unlink(wav_filepath)
    except:
        pass
        
    return await process_audio_bytes_and_command(
        audio_bytes, mode, language, engine, ollamaModel, geminiKey, sampleEngine, midiEngine, transcriptionEngine
    )

@app.post("/api/v1/voice/transcribe_and_command")
async def transcribe_and_command(
    file: UploadFile = File(...),
    mode: str = Form("control"),
    language: str = Form("ja-JP"),
    engine: str = Form("cloud_gemini"),
    ollamaModel: str = Form("gemma4:latest"),
    geminiKey: str = Form(""),
    sampleEngine: str = Form("local_mlx"),
    midiEngine: str = Form("cloud_gemini"),
    transcriptionEngine: str = Form("basic-pitch")
):
    audio_bytes = await file.read()
    return await process_audio_bytes_and_command(
        audio_bytes, mode, language, engine, ollamaModel, geminiKey, sampleEngine, midiEngine, transcriptionEngine
    )

@app.post("/api/v1/voice/command")
async def process_voice_command(command: VoiceCommand):
    global _models_listed, _last_advisor_response, _pending_advisor_actions

    # --- SERVER-SIDE STT NOISE FILTER ---
    junk_words = ["注目の話題", "告発", "字幕", "ご視聴", "放送大学", "おやすみなさい", "話題の", "話題を", "バーチャルさゆり", "さゆりです", "二次元の姿", "チャンネル登録"]
    if any(word in command.text for word in junk_words) or len(command.text) > 100:
        print(f"🚫 [SERVER] BLOCKING STT HALLUCINATION: '{command.text}'")
        return {"status": "success", "results": []} # Silently ignore

    # --- STT CORRECTION MAP (Fixing mis-transcriptions) ---
    # Using regex to handle spaces like "右 データ" or "右 の データ"
    import re
    
    # 1. Primary "Migi Data" -> "MIDI Data" correction
    # Matches: 右データ, 右 データ, 右のデータ, 右 の データ, etc.
    if re.search(r'右\s*(の)?\s*データ', command.text):
        command.text = re.sub(r'右\s*(の)?\s*データ', 'MIDIデータ', command.text)
        print(f"🔧 [CORRECTION] Fixed 'Migi Data' pattern to 'MIDIデータ'")
    
    # 2. "Migi ni shite" -> "MIDI ni shite"
    if re.search(r'右\s*(に)?\s*して', command.text):
        command.text = re.sub(r'右\s*(に)?\s*して', 'MIDIデータにして', command.text)
        print(f"🔧 [CORRECTION] Fixed 'Migi ni shite' pattern to 'MIDIデータにして'")

    # 2. Other common sounds
    other_corrections = {
        "道データ": "MIDIデータ",
        "三井データ": "MIDIデータ",
        "未知データ": "MIDIデータ",
        "メディデータ": "MIDIデータ",
        "右データ": "MIDIデータ"
    }
    for wrong, right in other_corrections.items():
        if wrong in command.text:
            command.text = command.text.replace(wrong, right)
            print(f"🔧 [CORRECTION] Fixed '{wrong}' to '{right}'")

    print(f"🎙 [VOICE {command.mode.upper()}] Text: '{command.text}'")

    # --- PRE-FETCH LATEST SYNC DATA FOR CONTEXTUAL ADVICE & GENERATION ---
    current_key = "C Major"
    current_bpm = 120.0
    try:
        async with httpx.AsyncClient(timeout=5.0) as http_client:
            print("🔄 [SYSTEM] Syncing context with Ableton...")
            sync_resp = await http_client.get("http://localhost:8005/api/v1/ableton/sync")
            sync_data = sync_resp.json().get("data", {})
            current_key = sync_data.get("key", "C Major")
            current_bpm = float(sync_data.get("bpm", 120.0))
            print(f"✅ [SYSTEM] Context Synced: {current_key} @ {current_bpm} BPM")
    except Exception as se:
        print(f"⚠️ [SYNC FAILED] Using defaults for context: {se}")

    # ===== TRACTOR / LEARNING MODE (Inventory & Style) =====
    # The Tractor is for "Knowledge Base" updates: Scanning plugins or Learning mix styles.
    if command.mode == "learning":
        try:
            # 1. SCAN PLUGINS / BROWSER
            scan_keywords = ["スキャン", "scan", "更新", "リスト", "プラグイン", "plugin", "同期", "sync"]
            if any(kw in command.text.lower() for kw in scan_keywords):
                await broadcast_advice("了解だ。サードパーティプラグインとブラウザをディープスキャンする。少し時間がかかるぞ...")
                await broadcast_status("SCANNING BROWSER INVENTORY...")
                
                async with httpx.AsyncClient(timeout=120.0) as http_client:
                    resp = await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "get_browser_summary"})
                    if resp.status_code == 200:
                        data = resp.json().get("data", {})
                        # Save to inventory file
                        from orchestration.advisor_engine import save_plugin_inventory
                        save_plugin_inventory(data)
                        
                        total = len(data.get("plugins", [])) + len(data.get("audio_effects", []))
                        await broadcast_advice(f"スキャン完了だ。{total}個のプラグインとエフェクトをインベントリに登録したぞ。")
                        await broadcast_status("SYSTEM READY")
                        return {"status": "success", "results": [{"action": "scan_complete"}]}
                    else:
                        raise Exception("Bridge scan failed")

            # 2. LEARN CURRENT STYLE
            learn_keywords = ["学習", "覚え", "learn", "スタイル", "style", "バランス", "balance", "ミックス"]
            if any(kw in command.text.lower() for kw in learn_keywords):
                from orchestration.mixing_engine import save_current_balance_as_learned_style
                await broadcast_advice("現在のバランスを君のスタイルとして学習する...")
                await broadcast_status("LEARNING USER STYLE...")
                res = await save_current_balance_as_learned_style(manager, command.text)
                await broadcast_advice("学習完了だ。次回のオートミックスにこのエッセンスを取り入れるぞ。")
                await broadcast_status("SYSTEM READY")
                return res

            # 3. STRUCTURE ANALYSIS (GEMINI 3.5 FLASH)
            analysis_keywords = ["解析", "構成", "構造", "分析", "analyze", "structure", "マーカー", "marker", "ロケーター", "locator"]
            if any(kw in command.text.lower() for kw in analysis_keywords):
                await broadcast_advice("選択された曲の構成解析を開始するぞ。少し待っていてくれ...")
                await broadcast_status("ANALYZING SONG STRUCTURE...")

                # 1. Get selected clip path from Ableton
                async with httpx.AsyncClient(timeout=10.0) as http_client:
                    clip_resp = await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "get_selected_clip_path"})
                    if clip_resp.status_code != 200:
                        raise Exception("Abletonでオーディオクリップが選択されていないか、パスの取得に失敗したワン。")
                    
                    clip_data = clip_resp.json()
                    if clip_data.get("status") != "success" or "data" not in clip_data:
                        msg = clip_data.get("msg", "Abletonでオーディオクリップが選択されていないか、パスの取得に失敗したワン。")
                        raise Exception(msg)
                    
                    file_path = clip_data["data"].get("file_path")
                    if not file_path:
                        raise Exception("選択されたクリップのファイルパスが見つかりません。")

                # 2. Run Gemini structure analysis
                from orchestration.gemini_analysis_engine import analyze_audio_with_gemini
                # We use the user's geminiKey if provided, or fall back to env key
                api_key = command.geminiKey or os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise Exception("Gemini API Key が設定されていません。Configでキーを入力してください。")

                # Run the analysis using gemini-3-flash-preview (per user global rule 5)
                try:
                    sections = analyze_audio_with_gemini(
                        file_path=file_path,
                        api_key=api_key,
                        bpm=current_bpm,
                        preferred_model="gemini-3.5-flash"
                    )
                except Exception as ex:
                    print(f"❌ [GEMINI ANALYSIS ERROR] {ex}")
                    raise Exception(f"Gemini解析中にエラーが発生しました: {ex}")

                # 3. Apply markers in Ableton
                if not sections:
                    raise Exception("曲の構成セクションを検出できませんでした。")

                # Convert seconds to beats and set markers
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    for sec in sections:
                        sec_name = sec.get("name", "Section")
                        sec_time_sec = sec.get("start_time", 0.0)
                        # Convert seconds to beats and snap to the nearest bar (multiple of 4.0 beats)
                        beats_raw = sec_time_sec * (current_bpm / 60.0)
                        sec_time_beats = float(round(beats_raw / 4.0) * 4.0)
                        
                        # Add marker via bridge
                        await http_client.post(
                            "http://localhost:8005/api/v1/ableton/execute",
                            json={
                                "action": "set_marker",
                                "params": {
                                    "name": sec_name,
                                    "time": sec_time_beats
                                }
                            }
                        )
                
                await broadcast_advice(f"解析完了だ！{len(sections)}個のマーカーをAbletonに配置したぞ。")
                await broadcast_status("SYSTEM READY")
                return {"status": "success", "results": [{"action": "structure_analysis_complete"}]}

            # Fallback for Tractor
            await broadcast_advice("トラクターモードだ。プラグインのスキャン（更新）、ミックススタイルの学習、または参考曲の構成解析（マーカー作成）を指示してくれ。")
            return {"status": "success", "results": []}

        except Exception as e:
            print(f"❌ [TRACTOR] ERROR: {e}")
            await broadcast_advice(f"トラブル発生だ。スキャンまたは学習に失敗した。（エラー: {e}）")
            return {"status": "error", "msg": str(e)}

    # ===== DOG ADVISOR MODE (Early Return) =====
    # The Dog is for non-destructive "Advice" and "Proposals".
    if command.mode == "advisor":
        try:
            from orchestration.advisor_engine import get_advice
            
            # --- 0. EXECUTION TRIGGER (STRICT OK) ---
            # Use strict matching for confirmation to prevent accidental triggers from "Onegaishimasu" (Please...)
            ok_keywords = ["ok", "オーケー", "いいよ", "やって", "お願い", "頼む", "実行して", "いいワン"]
            stripped_text = command.text.lower().strip()
            # Only trigger if the entire message is a confirmation or it's a very short specific command
            is_ok = any(stripped_text == kw for kw in ok_keywords) or \
                    (len(stripped_text) < 5 and any(stripped_text.startswith(kw) for kw in ["ok", "やって"]))
            
            if is_ok:
                if _pending_advisor_actions:
                    print(f"🐶 [DOG ADVISOR] Execution triggered for {len(_pending_advisor_actions)} actions!")
                    await broadcast_advice("まかせるワン！ただいま実行中だワン！")
                    await broadcast_status("EXECUTING AI PROPOSAL...")
                    
                    # Safety check: ensure it's a list
                    if isinstance(_pending_advisor_actions, dict):
                        _pending_advisor_actions = [_pending_advisor_actions]
                        
                    async with httpx.AsyncClient(timeout=30.0) as http_client:
                        for act in _pending_advisor_actions:
                            try:
                                # Ensure act has params if not present
                                if "params" not in act:
                                    act = {"action": act["action"], "params": act}
                                    
                                print(f"   -> Executing: {act}")
                                await http_client.post(
                                    "http://localhost:8005/api/v1/ableton/execute",
                                    json=act
                                )
                            except Exception as ex_err:
                                print(f"   ❌ Execution failed for {act}: {ex_err}")
                    
                    _pending_advisor_actions = [] # Clear after execution
                    await broadcast_advice("完了したワン！確認してみてほしいワン！")
                    await broadcast_status("SYSTEM READY")
                    return {"status": "success", "results": [{"action": "dog_advice", "advice": "Executed"}]}
                else:
                    # Case: User said OK but no pending actions
                    # Fall through to normal advice if they said "お願い" as part of a longer sentence
                    if len(stripped_text) > 4:
                        is_ok = False 
                    else:
                        await broadcast_advice("ん？まだ何も提案してないワン。何か手伝うことはあるワン？")
                        return {"status": "success", "results": [{"action": "dog_advice", "advice": "No pending actions"}]}
                
            # --- 1. CONTEXTUAL MIDI CONVERSION (PRIORITY) ---
            midi_keywords = ["midi", "ミディ", "みでぃ", "右", "データ"]
            if any(kw in command.text.lower() for kw in midi_keywords) and _last_advisor_response:
                print(f"🐶 [DOG ADVISOR] Triggering MIDI conversion from context: '{command.text}'")
                
                # 1. Inform user immediately
                await manager.broadcast(json.dumps({
                    "type": "DOG_ADVICE",
                    "advice": "わかったワン！今教えた進行をMIDIにするから、ちょっと待っててね！今計算中だワン...",
                    "question": command.text
                }))
                
                # MUTTERING (live commentary during scan)
                await broadcast_advice("OK！ちょっとみさせて！スキャン開始だワン！")
                await broadcast_status("AUDIT: SCANNING SESSION...")
                
                # 1. Audit session
                await manager.broadcast(json.dumps({"type": "GENERATING_START", "module": "midi"}))
                await manager.broadcast(json.dumps({"type": "PROGRESS_UPDATE", "progress": 30}))
                midi_prompt = f"CONTEXT (PREVIOUS ADVICE): {_last_advisor_response}\nUSER REQUEST: {command.text}\nTASK: Extract chords from CONTEXT and create MIDI."
                
                result = await asyncio.to_thread(
                    generate_midi_clip, 
                    midi_prompt, 
                    command.geminiKey, 
                    command.midiEngine, 
                    command.openaiKey,
                    current_bpm,
                    current_key,
                    command.claudeKey,
                    command.chordNotes,
                    False, # is_melody
                    command.ollamaModel
                )
                
                if result["status"] == "success":
                    await manager.broadcast(json.dumps({
                        "type": "SAMPLE_GENERATED", 
                        "file": result["file"],
                        "prompt": "Suggested Chord Sequence",
                        "isMidi": True
                    }))
                    await manager.broadcast(json.dumps({"type": "PROGRESS_UPDATE", "progress": 100}))
                    return {"status": "success", "results": [{"action": "generate_midi", "file": result["file"]}]}
                else:
                    error_msg = result.get("error", "Generation error")
                    print(f"❌ [DOG ADVISOR] MIDI Generation Failed: {error_msg}")
                    await manager.broadcast(json.dumps({"type": "PROGRESS_UPDATE", "progress": 0}))
                    await manager.broadcast(json.dumps({
                        "type": "DOG_ADVICE",
                        "advice": f"ごめんワン…MIDIの作成に失敗しちゃったワン。もう一度試してみてくれる？ (エラー: {error_msg})",
                        "question": command.text
                    }))
                    return {"status": "error", "msg": error_msg}

            # --- 2. NORMAL ADVICE (WITH AUTO-AUDIT & ACTIONS) ---
            else:
                # Check if we should perform a session audit for better advice
                # TIGHTENED: Only trigger audit for explicit mix/fix requests
                mix_keywords = [
                    "もこもこ", "スッキリ", "濁り", "音質", "mix", "muddy", "harsh",
                    "パンチ", "こもる", "太く", "迫力", "抜け", "厚み", "改善", "クリーン", "歪み", "ノイズ",
                    "診断", "スキャン", "アドバイスして", "ローが", "ハイが", "ミッドが",
                    "低域", "高域", "中域", "低音", "高音"
                ]
                
                session_data = None
                is_mix_query = any(kw in command.text.lower() for kw in mix_keywords)
                
                if is_mix_query:
                    print(f"🩺 [DOG ADVISOR] Mix query detected: '{command.text}'. Performing background audit...")
                    # --- LIVE COMMENTARY: STEP 1 ---
                    await broadcast_advice("OK！ちょっと見させてワン！今プロジェクトをスキャン中だワン...")
                    await broadcast_status("AUDIT: SCANNING SESSION...")

                    try:
                        async with httpx.AsyncClient(timeout=30.0) as client:
                            audit_resp = await client.post(
                                "http://localhost:8005/api/v1/ableton/execute",
                                json={"action": "get_session_audit"}
                            )
                            if audit_resp.status_code == 200:
                                session_data = audit_resp.json().get("data", {})
                                tracks = session_data.get("tracks", [])
                                print(f"✅ [DOG ADVISOR] Audit successful! Found {len(tracks)} tracks.")

                                # --- OPTIMIZED: Use cached plugin inventory instead of slow browser scan ---
                                from orchestration.advisor_engine import load_plugin_inventory
                                session_data["browser"] = load_plugin_inventory()
                                print(f"✅ [DOG ADVISOR] Loaded cached plugin inventory.")

                                # --- LIVE COMMENTARY: STEP 2 ---
                                await broadcast_advice(f"ふむふむ。。。{len(tracks)}トラックあるワンね。分析中だワン...")
                                await broadcast_status("AUDIT: ANALYZING MIX...")
                            else:
                                print(f"⚠️ [DOG ADVISOR] Audit failed: {audit_resp.text}")
                    except Exception as ae:
                        print(f"⚠️ [DOG ADVISOR] Background audit EXCEPTION: {ae}")
                else:
                    print(f"🐶 [DOG ADVISOR] General Advice Flow (No Audit): '{command.text}'")

                advice = await asyncio.to_thread(
                    get_advice, 
                    command.text, 
                    api_key=command.geminiKey, 
                    engine=command.engine,
                    ollama_model=command.ollamaModel,
                    current_key=current_key,
                    current_bpm=current_bpm,
                    session_data=session_data,
                    language=command.language,
                    local_ai_provider=command.localAiProvider,
                    local_ai_base_url=command.localAiBaseUrl
                )
                
                # --- EXTRACT JSON ACTIONS ---
                import re
                # Flexible regex to catch both ```json_actions and ```json
                json_actions_match = re.search(r'```(?:json_actions|json)\s*(\[.*?\])\s*```', advice, re.DOTALL)
                if json_actions_match:
                    try:
                        parsed_actions = json.loads(json_actions_match.group(1))
                        _pending_advisor_actions = parsed_actions
                        print(f"📦 [DOG ADVISOR] Stored {len(parsed_actions)} pending actions.")
                    except Exception as parse_e:
                        print(f"⚠️ [DOG ADVISOR] Failed to parse JSON actions: {parse_e}")
                        _pending_advisor_actions = []
                    # Strip the block from the text shown to the user
                    advice = re.sub(r'```json_actions\s*.*?\s*```', '', advice, flags=re.DOTALL).strip()
                else:
                    _pending_advisor_actions = []
                
                print(f"🐶 [DOG ADVISOR] Answer: '{advice}'")
                _last_advisor_response = advice
                
                await broadcast_advice(advice, question=command.text)
                await broadcast_status("SYSTEM READY")
                
                return {"status": "success", "results": [{"action": "dog_advice", "advice": advice}]}
        except Exception as e:
            print(f"❌ [DOG ADVISOR] ERROR: {e}")
            return {"status": "error", "msg": str(e)}

    # Specialized mode instructions to prevent accidental actions
    mode_context = ""
    if command.mode == "sampler":
        mode_context = "PREFERENCE: GENERATE_SAMPLE. The user is explicitly using the AI Sampler button."
    elif command.mode == "midi":
        mode_context = "PREFERENCE: GENERATE_MIDI. The user is explicitly using the AI MIDI Generator button. Focus on musical sequences and chord progressions."
    elif command.mode == "melody":
        mode_context = "PREFERENCE: GENERATE_MELODY. The user is explicitly using the AI Melody Generator button. Focus on creating a single-note melody."
    else:
        mode_context = "PREFERENCE: TRANSPORT/PLAYBACK. The user is using the main Control button."


    # --- FAST-PATH FOR TRANSPORT (0 Latency) ---
    actions = []
    
    # 0. Clean up timestamps (e.g. "00:00") from text to avoid mis-detecting as bars/seconds
    import re
    cleaned_text = re.sub(r'\d{1,2}:\d{2}', '', command.text)
    text_lower = cleaned_text.lower()
    
    if command.mode == "control":
        # Check for transport keywords
        is_play = any(kw in text_lower for kw in ["再生", "プレイ", "play", "スタート", "start"])
        is_stop = any(kw in text_lower for kw in ["停止", "止めて", "ストップ", "stop", "とめて"])
        
        if is_play:
            # 1. Check for BAR numbers (Include "小説" as common STT error for "小節")
            bar_match = re.search(r'(\d+)\s*(小節|小説|bar)', text_lower)
            # 2. Check for MINUTE and SECOND numbers
            min_sec_match = re.search(r'(\d+)\s*(分|min)\s*(\d+)\s*(秒|sec)', text_lower)
            sec_match = re.search(r'(\d+)\s*(秒|sec)', text_lower)
            min_match = re.search(r'(\d+)\s*(分|min)', text_lower)
            
            if bar_match:
                bar_num = int(bar_match.group(1))
                print(f"⚡ [FAST-PATH] Play from Bar {bar_num}: '{cleaned_text}'")
                actions = [{"action": "play_from_bar", "bar": bar_num}]
            elif min_sec_match:
                min_num = int(min_sec_match.group(1))
                sec_num = int(min_sec_match.group(3))
                print(f"⚡ [FAST-PATH] Play from Time {min_num}m {sec_num}s: '{cleaned_text}'")
                actions = [{"action": "play_from_time", "minutes": min_num, "seconds": sec_num}]
            elif min_match:
                min_num = int(min_match.group(1))
                print(f"⚡ [FAST-PATH] Play from Time {min_num}m: '{cleaned_text}'")
                actions = [{"action": "play_from_time", "minutes": min_num, "seconds": 0}]
            elif sec_match:
                sec_num = int(sec_match.group(1))
                print(f"⚡ [FAST-PATH] Play from Time {sec_num}s: '{cleaned_text}'")
                actions = [{"action": "play_from_time", "minutes": 0, "seconds": sec_num}]
            elif any(kw in text_lower for kw in ["最初から", "頭から", "あたまから", "さいしょから"]):
                print(f"⚡ [FAST-PATH] Play from Start: '{cleaned_text}'")
                actions = [{"action": "play_from_bar", "bar": 1}]
            elif len(cleaned_text) < 7: # Only for PURE "play" commands like "再生して"
                print(f"⚡ [FAST-PATH] Play: '{cleaned_text}'")
                actions = [{"action": "play"}]
            else:
                # If it contains "から" or is longer, let AI handle it (Markers etc.)
                print(f"🕵️ [FALLBACK] Letting AI handle potential marker/complex command: '{cleaned_text}'")
                actions = []
        elif is_stop:
            print(f"⚡ [FAST-PATH] Stop: '{cleaned_text}'")
            actions = [{"action": "stop"}]

    try:
        # --- NEW: USE THE CENTRAL PARSING ENGINE (Only if not already decided by Fast-Path) ---
        if not actions:
            actions = await parse_voice_to_actions(command.text, command, current_key, current_bpm)
        
        # FORCE LEARNING MODE: Even if parsing is ambiguous, trigger the learning engine
        if command.mode == 'learning' and not actions:
            actions = [{"action": "learn_style"}]

        if not actions:
            return {"status": "error", "msg": "Could not parse actions from voice."}

        # --- NEW: APPLY MATH FIXING & GUARDS ---
        from orchestration.ableton_control import prepare_ableton_actions
        actions = prepare_ableton_actions(actions, command.text)

        results = []
        print(f"🕵️ [DEBUG] Processing {len(actions)} actions: {actions}")
        async with httpx.AsyncClient(timeout=60.0) as http_client: # Longer timeout for AI
            for act in actions:
                # --- FORCE MODE ADHERENCE ---
                if command.mode == 'control':
                    if act["action"] in ["generate_sample", "generate_midi", "generate_melody"]:
                        print(f"🚫 [GUARD] Blocked generation action '{act['action']}' in Control Mode")
                        continue

                # --- SMART GENERATION OVERRIDE ---
                # If the AI hallucinates the wrong generation type for the current mode, force-correct it.
                if command.mode == 'sampler' and act["action"] in ["generate_midi", "generate_melody"]:
                    print(f"🔄 [FIX] Overriding MIDI action to 'generate_sample' for Sampler Mode")
                    act["action"] = "generate_sample"
                elif command.mode == 'midi' and act["action"] == "generate_sample":
                    print(f"🔄 [FIX] Overriding Sample action to 'generate_midi' for MIDI Mode")
                    act["action"] = "generate_midi"
                elif command.mode == 'melody' and act["action"] == "generate_sample":
                    print(f"🔄 [FIX] Overriding Sample action to 'generate_melody' for Melody Mode")
                    act["action"] = "generate_melody"
                
                # --- CASE 1: SAMPLE GENERATION (Kept in main.py) ---
                if act["action"] == "generate_sample":
                    # Broadcast Start and Status
                    await manager.broadcast(json.dumps({"type": "GENERATING_START", "module": "sample"}))
                    await manager.broadcast(json.dumps({
                        "type": "STATUS",
                        "msg": f">>> {'MLX' if command.sampleEngine == 'local_mlx' else 'GEMINI 3'} COMPOSING..."
                    }))

                    result = await asyncio.to_thread(
                        generate_sample, 
                        prompt=act["prompt"], 
                        key=current_key,
                        bpm=current_bpm,
                        engine=command.sampleEngine,
                        api_key=command.geminiKey
                    )
                    
                    if result["status"] == "success":
                        await manager.broadcast(json.dumps({
                            "type": "SAMPLE_GENERATED",
                            "file": result["file"],
                            "prompt": act["prompt"]
                        }))
                        results.append({"status": "success", "action": "generate_sample"})
                    else:
                        print(f"❌ [GEN-SAMPLE-ERROR] Generation failed for prompt '{act['prompt']}': {result.get('error')}")
                        await manager.broadcast(json.dumps({
                            "type": "STATUS",
                            "msg": f"❌ ERROR: {result.get('error', 'Generation Failed')}"
                        }))
                        results.append({"status": "error", "error": result.get("error")})

                # --- CASE 2: MIDI GENERATION (Kept in main.py) ---
                elif act["action"] in ["generate_midi", "generate_melody"]:
                    try:
                        is_melody = (act["action"] == "generate_melody")
                        # Broadcast Start and Status
                        await manager.broadcast(json.dumps({"type": "GENERATING_START", "module": "midi" if not is_melody else "melody"}))
                        await manager.broadcast(json.dumps({
                            "type": "STATUS",
                            "msg": f">>> GEMINI 3 IS COMPOSING {'MELODY' if is_melody else 'MIDI'}..."
                        }))

                        # Auto-fetch chords ONLY for melody if missing
                        chord_notes_to_use = command.chordNotes if is_melody else None
                        if is_melody and not chord_notes_to_use:
                            try:
                                async with httpx.AsyncClient() as client:
                                    res = await client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "get_notes"})
                                    data = res.json()
                                    if data.get("status") == "success" and data.get("data"):
                                        chord_notes_to_use = data["data"]
                                        print(f"🎵 [MIDI] Auto-fetched {len(chord_notes_to_use)} notes from selected clip.")
                            except Exception as e:
                                print(f"⚠️ [MIDI] Could not fetch chords: {e}")

                        result = await asyncio.to_thread(
                            generate_midi_clip, 
                            act.get("prompt", command.text), 
                            command.geminiKey, 
                            command.midiEngine, 
                            command.openaiKey,
                            current_bpm,
                            current_key,
                            command.claudeKey,
                            chord_notes_to_use,
                            is_melody,
                            command.ollamaModel
                        )

                        if result["status"] == "success":
                            await manager.broadcast(json.dumps({
                                "type": "SAMPLE_GENERATED", 
                                "file": result["file"],
                                "prompt": act.get("prompt", command.text),
                                "isMidi": True
                            }))
                            results.append({"status": "success", "action": "generate_midi"})
                        else:
                            await manager.broadcast(json.dumps({
                                "type": "STATUS",
                                "msg": f"❌ ERROR: {result.get('error', 'MIDI Generation Failed')}"
                            }))
                            results.append({"status": "error", "error": result.get("error")})
                    except Exception as me:
                        print(f"❌ [MIDI DISPATCH ERROR] {me}")
                        await manager.broadcast(json.dumps({"type": "STATUS", "msg": f"❌ ERROR: {str(me)}"}))
                        results.append({"status": "error", "error": str(me)})

                # --- CASE 4: ROUGH MIX ---
                elif act["action"] == "rough_mix":
                    # This is a long-running process, we spawn it as a background task
                    asyncio.create_task(run_rough_mix(manager))
                    results.append({"status": "success", "action": "rough_mix", "msg": "Mixing process started"})

                elif act["action"] == "learn_style":
                    res = await save_current_balance_as_learned_style(manager, command.text)
                    results.append(res)

                # --- CASE 5: ABLETON CONTROL (Delegated to orchestration/ableton_control.py) ---
                else:
                    from orchestration.ableton_control import execute_ableton_action
                    res = await execute_ableton_action(act, http_client, manager)
                    results.append(res)
        
        return {"status": "success", "results": results}
        
    except Exception as e:
        print(f"[ERROR] {e}")
        return {"status": "error", "msg": str(e)}

@app.post("/api/v1/reveal")
async def reveal_in_finder(data: dict):
    file_path = data.get("path")
    if not file_path:
        return {"status": "error", "message": "No path provided"}
    
    # HARDENED PATH RESOLUTION:
    # Anchor to this file's location to be immune to where the user launches from
    # Current File: <PROJECT>/server/main.py
    # Destination: <PROJECT>/client/public/samples/...
    server_dir = Path(__file__).parent.absolute()
    base_dir = server_dir.parent # This is the root project folder
    
    # file_path is like "/samples/ai_mlx_123.wav"
    relative_path = file_path.lstrip("/")
    abs_path = base_dir / "client" / "public" / relative_path
    
    print(f"📁 [HARDENED] Attempting reveal: {abs_path}")
    print(f"📁 [HARDENED] File exists? {abs_path.exists()}")
    
    if abs_path.exists():
        try:
            # macOS specific: open -R reveals the file in Finder
            # Convert Path object to string for subprocess
            subprocess.run(["open", "-R", str(abs_path)], check=True)
            print("🚀 [HARDENED] Reveal command executed successfully.")
            return {"status": "success"}
        except subprocess.CalledProcessError as e:
            print(f"❌ [HARDENED] Reveal command failed: {e}")
            return {"status": "error", "message": f"Command failed: {e}"}
    else:
        print(f"❌ [HARDENED] File NOT FOUND at {abs_path}")
        # Let's try to list the parent directory to see what's actually there
        if abs_path.parent.exists():
            print(f"📁 Parent exists. Contents: {os.listdir(abs_path.parent)}")
        return {"status": "error", "message": f"File not found: {abs_path}"}

def make_monophonic(instrument):
    """
    Force an instrument to be monophonic by resolving overlaps.
    Keeps the note with the highest velocity when multiple notes overlap.
    """
    if not instrument.notes:
        return instrument
        
    # Sort notes by start time
    sorted_notes = sorted(instrument.notes, key=lambda x: x.start)
    monophonic_notes = []
    
    if sorted_notes:
        current_note = sorted_notes[0]
        
        for next_note in sorted_notes[1:]:
            # If there's an overlap
            if next_note.start < current_note.end:
                # Decide which one to keep (e.g., the one with higher velocity)
                if next_note.velocity > current_note.velocity:
                    # Truncate current_note to end where next_note starts
                    current_note.end = next_note.start
                    if current_note.start < current_note.end:
                        monophonic_notes.append(current_note)
                    current_note = next_note
                else:
                    # Skip next_note or truncate it to start after current_note
                    next_note.start = current_note.end
                    if next_note.start < next_note.end:
                        # We don't append yet, it becomes the new potential current_note
                        # but wait, let's just adjust and keep current_note
                        pass 
                    else:
                        continue # next_note is fully eclipsed
            else:
                # No overlap, commit current_note and move to next
                monophonic_notes.append(current_note)
                current_note = next_note
        
        monophonic_notes.append(current_note)
        
    instrument.notes = monophonic_notes
    return instrument

@app.post("/api/v1/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...), 
    engine: str = Form("basic-pitch"), 
    bpm: float = Form(120.0),
    is_humming: bool = Form(False)
):
    server_dir = Path(__file__).parent.absolute()
    temp_dir = server_dir / "temp"
    output_dir = Path(client_samples_dir)
    
    temp_dir.mkdir(exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # helper for tempo detection
    def estimate_source_tempo(path):
        try:
            y, sr = librosa.load(path, sr=22050)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            # Ensure tempo is a single float
            if isinstance(tempo, (list, np.ndarray)):
                tempo = float(tempo[0])
            else:
                tempo = float(tempo)
            return tempo
        except:
            return None

    # Save incoming audio to temp
    temp_id = int(time.time())
    audio_path = temp_dir / f"input_{temp_id}.wav"
    
    with open(audio_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    print(f"🎙 [TRANSCRIBE] Engine: {engine} | BPM: {bpm} | Audio received: {audio_path}")
    
    try:
        status_msg = ">>> ANALYZING AUDIO CONTENT..." if engine == "basic-pitch" else ">>> MT3 PRECISION ANALYSIS (WAITING...)"
        await manager.broadcast(json.dumps({
            "type": "STATUS",
            "msg": status_msg
        }))
        
        midi_filename = f"transcribed_{temp_id}.mid"
        midi_path = output_dir / midi_filename
        notes_count = 0

        # Removed AUTO-WARP logic to preserve exact original audio timing

        # Fallback basic-pitch to mt3 if basic-pitch is not installed
        # Fallback basic-pitch logic removed.

        if engine == "mt3":
            if not mt3_transcribe:
                return {"status": "error", "msg": "MT3 engine not installed on server."}
            
            print(f"🧠 [TRANSCRIBE] Running MT3 Inference (Threaded)...")
            # Load and normalize audio for MT3 (16k mono)
            audio_data, _ = await asyncio.to_thread(librosa.load, str(audio_path), sr=16000, mono=True)
            
            # Peak normalize to avoid 'all zero' filterbank warnings
            if np.max(np.abs(audio_data)) > 0:
                audio_data = audio_data / np.max(np.abs(audio_data))
                print(f"🔊 [TRANSCRIBE] Audio peak-normalized for better analysis.")
            
            # Offload heavy ML to a thread
            print(f"⏳ [TRANSCRIBE] Model inference starting...")
            midi_data = await asyncio.to_thread(mt3_transcribe, audio_data, model="mr_mt3")
            print(f"✅ [TRANSCRIBE] Inference complete. Converting to MIDI...")
            
            # Convert mido to pretty_midi
            midi_stream = io.BytesIO()
            midi_data.save(file=midi_stream)
            midi_stream.seek(0)
            pm_source = pretty_midi.PrettyMIDI(midi_stream)
            print(f"✨ [TRANSCRIBE] MIDI successfully re-containerized.")
            
            # HIGH-PRECISION BPM RE-CONTAINERIZATION
            pm_new = pretty_midi.PrettyMIDI(initial_tempo=bpm)
            for inst in pm_source.instruments:
                if is_humming:
                    new_inst = make_monophonic(copy.deepcopy(inst))
                    pm_new.instruments.append(new_inst)
                else:
                    pm_new.instruments.append(copy.deepcopy(inst))
            
            pm_new.write(str(midi_path))
            notes_count = sum(len(track.notes) for track in pm_new.instruments)
        elif engine == "giantmidi-piano":
            if not PianoTranscription:
                return {"status": "error", "msg": "GiantMIDI-Piano engine not installed on server."}
            
            # Ensure model exists (fix for missing wget)
            await asyncio.to_thread(ensure_giantmidi_model)
            
            print(f"🧠 [TRANSCRIBE] Running GiantMIDI-Piano Inference (Threaded)...")
            # Decide device (Mac Studio optimization)
            device = 'mps' if torch.backends.mps.is_available() else 'cpu'
            
            # Load audio for GiantMIDI (16k or 32k works, let's use 16k)
            audio_data, _ = await asyncio.to_thread(librosa.load, str(audio_path), sr=16000, mono=True)
            
            def _run_giantmidi(audio, path):
                transcriptor = PianoTranscription(device=device, checkpoint_path=None)
                # This writes to path directly
                transcriptor.transcribe(audio, str(path))
                return pretty_midi.PrettyMIDI(str(path))
            
            pm_source = await asyncio.to_thread(_run_giantmidi, audio_data, midi_path)
            
            # RE-CONTAINERIZE FOR CONSISTENT BPM
            pm_new = pretty_midi.PrettyMIDI(initial_tempo=bpm)
            for inst in pm_source.instruments:
                if is_humming:
                    new_inst = make_monophonic(copy.deepcopy(inst))
                    pm_new.instruments.append(new_inst)
                else:
                    pm_new.instruments.append(copy.deepcopy(inst))
            
            pm_new.write(str(midi_path))
            notes_count = sum(len(track.notes) for track in pm_new.instruments)
        else:
            return {"status": "error", "msg": f"Unknown transcription engine: {engine}"}
        print(f"✨ [TRANSCRIBE] MIDI success ({engine}): {midi_path}")
        
        result = {
            "status": "success",
            "file": f"/samples/{midi_filename}",
            "notes_count": notes_count,
            "engine": engine,
            "bpm": bpm
        }
        
        await manager.broadcast(json.dumps({
            "type": "TRANSCRIPTION_FINISHED",
            "file": result["file"],
            "notes": result["notes_count"],
            "engine": engine,
            "bpm": bpm
        }))
        
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"❌ [TRANSCRIBE] Error: {e}")
        return {"status": "error", "msg": str(e)}
    finally:
        # Cleanup temp audio
        if audio_path.exists():
            os.remove(audio_path)





@app.post("/api/v1/advisor/random")
async def get_random_dog_advice():
    try:
        from orchestration.advisor_engine import get_random_advice
        advice = get_random_advice()
        
        # Broadcast immediately
        await manager.broadcast(json.dumps({
            "type": "DOG_ADVICE",
            "advice": advice,
            "question": "Quick Tip"
        }))
        
        return {"status": "success", "advice": advice}
    except Exception as e:
        print(f"❌ [RANDOM ADVISOR] ERROR: {e}")
        return {"status": "error", "msg": str(e)}

@app.get("/api/v1/system/status")
async def get_system_status():
    return {
        "status": "online",
        "engines": {
            "mt3": mt3_transcribe is not None,
            "giantmidi-piano": PianoTranscription is not None
        }
    }

@app.get("/")
async def root():
    return {"status": "online", "mode": "minimalist (v6.4 - TRANSCRIPTION ENABLED)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

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
    from basic_pitch.inference import predict
except ImportError:
    predict = None
    print("⚠️ [SYSTEM] Basic Pitch not found. Install with: pip install basic-pitch")

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

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic
    print("🚀 [SYSTEM] Cockpit Backend Starting...")
    yield
    # Shutdown logic
    print("🛑 [SYSTEM] Cockpit Backend Shutting Down...")

app = FastAPI(lifespan=lifespan)

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

SYSTEM_PROMPT = """
You are the Ableton AI Cockpit Controller. Convert user speech into JSON actions.
AVAILABLE ACTIONS:
- {"action": "play"}
- {"action": "stop"}
- {"action": "record"}
- {"action": "generate_sample", "prompt": "style"}
- {"action": "generate_midi", "prompt": "style"}
- {"action": "play_from_marker", "name": "marker_name"}
- {"action": "play_from_bar", "bar": int}
- {"action": "play_from_time", "minutes": int, "seconds": int}
- {"action": "load_device", "name": "device_name"}
- {"action": "mute", "value": true/false, "track_name": "name"}
- {"action": "solo", "value": true/false, "track_name": "name"}
- {"action": "arm", "value": true/false, "track_name": "name"}
- {"action": "change_volume", "db_change": float, "track_name": "name"}
- {"action": "set_volume_db", "target_db": float, "track_name": "name"}
- {"action": "set_pan", "value": float_minus1_to_1, "track_name": "name"}
- {"action": "toggle_loop"}
- {"action": "toggle_metronome"}
- {"action": "lowcut", "track_name": "name"}

CRITICAL RULES:
1. VOLUME CONTROL (IMPORTANT):
   - Relative Change (下げて, 上げて, 足して, 引いて, 減らして): 
     Use {"action": "change_volume", "db_change": float}. 
     Example: "5dB下げて" -> {"action": "change_volume", "db_change": -5}
   - Absolute Setting (にして, に設定, にセット): 
     Use {"action": "set_volume_db", "target_db": float}.
     Example: "5dBにして" -> {"action": "set_volume_db", "target_db": 5}
   - Reference: 0.85 is 0dB, 1.0 is +6dB, 0.0 is -inf.
2. INSTRUMENT MAPPING:
   - "ピアノ", "ぴあの", "Pn" -> "Piano"
   - "ドラム", "どらむ", "Dr", "Kick", "Snare" -> "Drums"
   - "ベース", "べーす", "Bs", "Ba" -> "Bass"
   - "ギター", "ぎたー", "Gt" -> "Guitar"
   - "シンセ", "しんせ", "Syn" -> "Synth"
   - "ボーカル", "ぼーかる", "Vox" -> "Vocal"
   Always use the English name (Piano, Drums, etc.) in "track_name" if mapping exists.
3. "小節" (bar) is often mis-transcribed as "小説" (novel). 
   Treat "[Number] 小説" or "[Number] 小節" as {"action": "play_from_bar", "bar": [Number]}.
4. Alphanumeric names like "1 B", "2 A", "1サビ", "Intro", "Verse" are MARKER NAMES.
   Map them to {"action": "play_from_marker", "name": "..."}.
5. Use "play_from_bar" for pure integers like "Play from bar 40" or "[Number] 小節".
6. Use "play_from_time" for time-based requests like "1:30" or "1分45秒".
7. Respond ONLY with a valid JSON array.
"""

class VoiceCommand(BaseModel):
    text: str
    mode: str = "control"
    engine: str = "local_ollama"
    sampleEngine: str = "local_mlx"
    midiEngine: str = "cloud_gemini"
    geminiKey: str = ""
    openaiKey: str = ""

from orchestration.audio_engine import generate_sample

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

# Diagnostic flag
_models_listed = False

@app.post("/api/v1/voice/command")
async def process_voice_command(command: VoiceCommand):
    global _models_listed

    # --- SERVER-SIDE STT NOISE FILTER ---
    junk_words = ["注目の話題", "告発", "字幕", "ご視聴", "放送大学", "おやすみなさい", "話題の", "話題を"]
    if any(word in command.text for word in junk_words):
        print(f"🚫 [SERVER] BLOCKING STT HALLUCINATION: '{command.text}'")
        return {"status": "success", "results": []} # Silently ignore

    print(f"🎙 [VOICE {command.mode.upper()}] Text: '{command.text}'")

    # ===== DOG ADVISOR MODE (Early Return) =====
    if command.mode == "advisor":
        try:
            from orchestration.advisor_engine import get_advice
            print(f"🐶 [DOG ADVISOR] Question: '{command.text}'")
            advice = await asyncio.to_thread(
                get_advice, 
                command.text, 
                api_key=command.geminiKey, 
                engine=command.engine
            )
            print(f"🐶 [DOG ADVISOR] Answer: '{advice}'")
            
            # Broadcast advice to all WebSocket clients
            await manager.broadcast(json.dumps({
                "type": "DOG_ADVICE",
                "advice": advice,
                "question": command.text
            }))
            
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
    else:
        mode_context = "PREFERENCE: TRANSPORT/PLAYBACK. The user is using the main Control button."

    try:
        parsed_json_string = ""
        
        # --- OPTION 1: CLOUD GENAI (GEMINI 3) ---
        if command.engine == "cloud_gemini" and genai and command.geminiKey:
            try:
                client = genai.Client(api_key=command.geminiKey)
                model_tiers = ['gemini-3-flash-preview', 'gemini-3.1-pro-preview', 'gemini-2.0-flash']
                
                for model_name in model_tiers:
                    try:
                        print(f"🚀 [GEMINI 3] TRYING MODEL: '{model_name}'...")
                        res = client.models.generate_content(
                            model=model_name, 
                            contents=f"{mode_context}\n{SYSTEM_PROMPT}\nUSER: {command.text}"
                        )
                        parsed_json_string = res.text
                        print(f"✅ [GEMINI 3] SUCCESS WITH '{model_name}'")
                        break
                    except Exception as ge:
                        print(f"   - '{model_name}' FAILED: {str(ge)[:100]}...")
                        continue
            except Exception as e:
                print(f"❌ [CLOUD ERROR] {e}")
        
        # --- OPTION 2: LOCAL OLLAMA (FORCE OR FALLBACK) ---
        if not parsed_json_string:
            print(f"🏠 [LOCAL NLP] ANALYZING WITH OLLAMA (GEMMA4): '{command.text}'")
            import ollama
            response = ollama.chat(
                model="gemma4:latest",
                messages=[
                    {'role': 'system', 'content': f"{mode_context}\n{SYSTEM_PROMPT}"},
                    {'role': 'user', 'content': command.text}
                ]
            )
            parsed_json_string = response['message']['content']
            print(f"✅ [LOCAL NLP] OLLAMA ANALYSIS COMPLETE")
        
        print(f"[LLM RAW] {parsed_json_string}")
        
        # Super-robust cleaning for AI hallucinations
        cleaned = parsed_json_string.strip()
        cleaned = cleaned.replace("```json", "").replace("```", "")
        # Remove any stray backticks that might be wrapping keys or values
        cleaned = cleaned.replace("`", "") 
        cleaned = cleaned.strip()
        
        start = cleaned.find("[")
        end = cleaned.rfind("]") + 1
        if start >= 0 and end > start:
            cleaned = cleaned[start:end]
            
        try:
            actions = json.loads(cleaned)
        except json.JSONDecodeError as je:
            print(f"⚠️ [JSON ERROR] Retrying parsing: {je}")
            # Final attempt: remove all non-JSON characters outside brackets
            import re
            cleaned = re.sub(r'^[^\[]*', '', cleaned)
            cleaned = re.sub(r'[^\]]*$', '', cleaned)
            actions = json.loads(cleaned)
        if isinstance(actions, dict):
            actions = [actions]
            
        results = []
        async with httpx.AsyncClient(timeout=60.0) as http_client: # Longer timeout for AI
            # PRE-FETCH LATEST SYNC DATA FROM BRIDGE FOR PERFECT ALIGNMENT
            try:
                print("🔄 [SYSTEM] Syncing with Ableton...")
                sync_resp = await http_client.get("http://localhost:8005/api/v1/ableton/sync")
                sync_data = sync_resp.json().get("data", {})
                current_key = sync_data.get("key", "C Major")
                current_bpm = sync_data.get("bpm", 120)
                print(f"✅ [SYSTEM] Sync Complete: {current_key} @ {current_bpm} BPM")
            except Exception as se:
                print(f"⚠️ [SYNC FAILED] Using defaults: {se}")
                current_key = "C Major"
                current_bpm = 120

            for act in actions:
                if act["action"] == "generate_sample":
                    # Broadcast Status to trigger UI Progress Meter
                    await manager.broadcast(json.dumps({
                        "type": "STATUS",
                        "msg": f">>> {'MLX' if command.sampleEngine == 'local_mlx' else 'GEMINI 3'} COMPOSING..."
                    }))

                    # Call Sample Engine Logic
                    from orchestration.audio_engine import generate_sample
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
                        await manager.broadcast(json.dumps({
                            "type": "STATUS",
                            "msg": f"❌ ERROR: {result.get('error', 'Generation Failed')}"
                        }))
                        results.append({"status": "error", "error": result.get("error")})

                elif act["action"] == "generate_midi":
                    # Broadcast Status
                    await manager.broadcast(json.dumps({
                        "type": "STATUS",
                        "msg": f">>> GEMINI 3 IS COMPOSING MIDI..."
                    }))

                    # Call MIDI Engine Logic
                    from orchestration.midi_engine import generate_midi_clip
                    result = await asyncio.to_thread(
                        generate_midi_clip, 
                        act["prompt"], 
                        command.geminiKey, 
                        command.midiEngine, 
                        command.openaiKey,
                        current_bpm,
                        current_key
                    )

                    if result["status"] == "success":
                        await manager.broadcast(json.dumps({
                            "type": "SAMPLE_GENERATED", 
                            "file": result["file"],
                            "prompt": act["prompt"],
                            "isMidi": True
                        }))
                        results.append({"status": "success", "action": "generate_midi"})
                    else:
                        await manager.broadcast(json.dumps({
                            "type": "STATUS",
                            "msg": f"❌ ERROR: {result.get('error', 'MIDI Generation Failed')}"
                        }))
                        results.append({"status": "error", "error": result.get("error")})
                else:
                    # Forward to Ableton Bridge
                    action_name = act["action"].lower()
                    print(f"🔗 [BRIDGE] Forwarding '{action_name}' with params: {act}")
                    resp = await http_client.post(
                        "http://localhost:8005/api/v1/ableton/execute",
                        json={"action": action_name, "params": act}
                    )
                    bridge_data = resp.json()
                    if bridge_data.get("status") == "success":
                        print(f"✅ [BRIDGE] {bridge_data.get('msg', 'OK')}")
                    else:
                        print(f"❌ [BRIDGE] ERROR: {bridge_data.get('msg', 'Unknown')}")
                    results.append(bridge_data)
                    
                    # BROADCAST SUCCESS: Signal frontend to turn Blue and stop blinking
                    if bridge_data.get("status") == "success":
                        await manager.broadcast(json.dumps({
                            "type": "SUCCESS",
                            "msg": f"{action_name.upper()} SUCCESSFUL"
                        }))
        
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

@app.post("/api/v1/transcribe")
async def transcribe_audio(file: UploadFile = File(...), engine: str = Form("basic-pitch"), bpm: float = Form(120.0)):
    server_dir = Path(__file__).parent.absolute()
    temp_dir = server_dir / "temp"
    output_dir = server_dir.parent / "client" / "public" / "transcriptions"
    
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

        if engine == "mt3":
            if not mt3_transcribe:
                return {"status": "error", "msg": "MT3 engine not installed on server."}
            
            print(f"🧠 [TRANSCRIBE] Running MT3 Inference (Threaded)...")
            # Load audio for MT3 (16k mono is standard)
            audio_data, _ = await asyncio.to_thread(librosa.load, str(audio_path), sr=16000, mono=True)
            # Offload heavy ML to a thread to keep Ableton controls responsive
            midi_data = await asyncio.to_thread(mt3_transcribe, audio_data)
            
            # Convert mido to pretty_midi for consistency with existing warping logic
            midi_stream = io.BytesIO()
            midi_data.save(file=midi_stream)
            midi_stream.seek(0)
            pm_source = pretty_midi.PrettyMIDI(midi_stream)
            
            # HIGH-PRECISION BPM RE-CONTAINERIZATION
            pm_new = pretty_midi.PrettyMIDI(initial_tempo=bpm)
            for inst in pm_source.instruments:
                new_inst = copy.deepcopy(inst)
                pm_new.instruments.append(new_inst)
            
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
                new_inst = copy.deepcopy(inst)
                pm_new.instruments.append(new_inst)
            
            pm_new.write(str(midi_path))
            notes_count = sum(len(track.notes) for track in pm_new.instruments)
        else:
            if not predict:
                return {"status": "error", "msg": "BasicPitch not available on server."}
            
            print(f"🧠 [TRANSCRIBE] Running Basic Pitch Prediction (Threaded)...")
            # Offload heavy ML to a thread
            model_output, midi_data, note_events = await asyncio.to_thread(predict, str(audio_path))
            
            # HIGH-PRECISION BPM RE-CONTAINERIZATION
            pm_new = pretty_midi.PrettyMIDI(initial_tempo=bpm)
            for inst in midi_data.instruments:
                new_inst = copy.deepcopy(inst)
                pm_new.instruments.append(new_inst)

            pm_new.write(str(midi_path))
            notes_count = len(note_events)
        
        print(f"✨ [TRANSCRIBE] MIDI success ({engine}): {midi_path}")
        
        result = {
            "status": "success",
            "file": f"/transcriptions/{midi_filename}",
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

@app.get("/")
async def root():
    return {"status": "online", "mode": "minimalist (v6.4 - TRANSCRIPTION ENABLED)"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

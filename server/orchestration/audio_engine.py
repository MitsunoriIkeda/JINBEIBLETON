import os
import time
import json
import base64
import platform
from pathlib import Path
import numpy as np
import soundfile as sf
import httpx

# Dynamic import of torch if needed
torch = None
try:
    import torch as _torch
    torch = _torch
except ImportError:
    pass

# Redirect HF Cache
def _get_hf_cache_dir():
    from pathlib import Path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ssd_dir = os.path.abspath(os.path.join(script_dir, "..")) # /server
    local_cache = os.path.join(ssd_dir, ".hf_cache")
    if os.path.exists(local_cache) and os.access(ssd_dir, os.W_OK):
        return local_cache
    home_cache = os.path.join(str(Path.home()), ".jinbeibleton", ".hf_cache")
    os.makedirs(home_cache, exist_ok=True)
    return home_cache

os.environ["HF_HOME"] = _get_hf_cache_dir()

# Dynamic Imports based on OS
IS_MAC = platform.system() == "Darwin"

# Global model instances
_mlx_model = None
_torch_model = None

def get_local_model():
    global _mlx_model, _torch_model
    
    if IS_MAC:
        # --- MAC (MLX) ---
        if _mlx_model is None:
            try:
                import gc
                gc.collect()
                # Only use offline mode if the model files are already cached.
                # This allows first-time users to automatically download the models,
                # while preventing slow network checks for subsequent runs.
                model_cache_path = os.path.join(os.environ.get("HF_HOME", ""), "hub", "models--facebook--musicgen-stereo-medium")
                if os.path.exists(model_cache_path) and os.listdir(model_cache_path):
                    os.environ["HF_HUB_OFFLINE"] = "1"
                    print("🧠 [AUDIO-MLX] Using offline cache mode for local generation.")
                else:
                    os.environ.pop("HF_HUB_OFFLINE", None)
                    print("🧠 [AUDIO-MLX] Local cache empty/not found. Downloading models from Hugging Face...")
                try:
                    from mlx_audiocraft.models import MusicGen
                except ImportError:
                    from audiocraft_mlx.models import MusicGen
                print(f"🧠 [AUDIO-MLX] Loading MusicGen (High Quality Stereo-Medium) for Mac...")
                _mlx_model = MusicGen.get_pretrained("facebook/musicgen-stereo-medium")
            except ImportError:
                print("❌ [AUDIO-MLX] 'audiocraft-mlx' not installed. Mac local gen disabled.")
                return None
        return _mlx_model
    else:
        # --- WINDOWS/LINUX (Torch/Audiocraft) ---
        if _torch_model is None:
            try:
                import gc
                gc.collect()
                if torch.cuda.is_available(): torch.cuda.empty_cache()
                from audiocraft.models import MusicGen
                print(f"🧠 [AUDIO-TORCH] Loading MusicGen (High Quality Stereo-Medium) for Windows/Linux...")
                device = "cuda" if torch.cuda.is_available() else "cpu"
                _torch_model = MusicGen.get_pretrained("facebook/musicgen-stereo-medium")
                _torch_model.to(device)
            except ImportError:
                print("❌ [AUDIO-TORCH] 'audiocraft' not installed. Windows local gen disabled.")
                return None
        return _torch_model

async def transcribe_audio(audio_bytes: bytes, api_key: str = "", language: str = "ja-JP", engine: str = "cloud"):
    """
    Multi-engine Speech-to-Text router.
    """
    # Ensure ffmpeg is in PATH (from static-ffmpeg)
    try:
        import static_ffmpeg
        static_ffmpeg.add_paths()
    except Exception:
        pass

    # --- ENGINE 1: GEMINI CLOUD (Only if requested and key exists) ---
    if "cloud" in engine.lower() and api_key:
        try:
            from google import genai
            from google.genai import types
            
            client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
            
            print(f"🎙 [STT] Using Gemini Cloud ({len(audio_bytes)} bytes)...")
            
            response = client.models.generate_content(
                model='gemini-3-flash-preview',
                contents=[
                    types.Part.from_bytes(
                        data=audio_bytes,
                        mime_type='audio/webm'
                    ),
                    types.Part.from_text(text=f"Transcribe this audio strictly. Language is {language}. Return ONLY the transcribed text, nothing else. If no speech is detected, return an empty string.")
                ]
            )
            
            text = response.text.strip()
            print(f"✅ [STT-GEMINI] Result: '{text}'")
            return {"status": "success", "text": text}
            
        except Exception as e:
            print(f"⚠️ [STT-GEMINI] Failed: {e}. Falling back to local...")
    
    # --- ENGINE 2: MLX-WHISPER (Mac local, no key needed) ---
    try:
        import mlx_whisper
        print(f"🎙 [STT] Using mlx-whisper LOCAL ({len(audio_bytes)} bytes)...")
        
        # Save to temp file (mlx-whisper needs a file path)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        lang_code = language.split("-")[0]  # "ja-JP" → "ja"
        result = mlx_whisper.transcribe(
            tmp_path,
            language=lang_code,
            path_or_hf_repo="mlx-community/whisper-large-v3-turbo",
        )
        
        os.unlink(tmp_path)  # Clean up temp file
        text = result.get("text", "").strip()

        # --- HALLUCINATION FILTER (Whisper-specific noise) ---
        hallucinations = [
            "ご視聴ありがとうございました", "チャンネル登録", "お疲れ様でした", 
            "視聴ありがとうございました", "ご視聴ありがとう", "ありがとうございました",
            "Thank you for watching", "Please subscribe", "Bye bye"
        ]
        if any(h in text for h in hallucinations) and len(text) < 20:
            print(f"🚫 [SERVER] BLOCKING STT HALLUCINATION: '{text}'")
            text = ""

        print(f"✅ [STT-MLX-WHISPER] Result: '{text}'")
        return {"status": "success", "text": text}
        
    except ImportError:
        print("⚠️ [STT] mlx-whisper not installed. Trying faster-whisper...")
    except Exception as e:
        print(f"⚠️ [STT-MLX-WHISPER] Error: {e}. Trying faster-whisper...")
    
    # --- ENGINE 3: FASTER-WHISPER (Cross-platform, no key needed) ---
    try:
        from faster_whisper import WhisperModel
        print(f"🎙 [STT] Using faster-whisper LOCAL ({len(audio_bytes)} bytes)...")
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        
        model = WhisperModel("large-v3-turbo", compute_type="int8")
        lang_code = language.split("-")[0]
        segments, _ = model.transcribe(tmp_path, language=lang_code)
        text = " ".join([seg.text for seg in segments]).strip()
        
        os.unlink(tmp_path)
        print(f"✅ [STT-FASTER-WHISPER] Result: '{text}'")
        return {"status": "success", "text": text}
        
    except ImportError:
        print("❌ [STT] No local STT engine available.")
    except Exception as e:
        print(f"❌ [STT-FASTER-WHISPER] Error: {e}")
    
    # --- NO ENGINE AVAILABLE ---
    return {
        "status": "error", 
        "error": "No STT engine available. Please set a Gemini API Key in Config, or install mlx-whisper (Mac) / faster-whisper."
    }


def generate_sample(prompt: str, duration: int = 5, key: str = "C Major", bpm: int = 120, engine: str = "local_mlx", api_key: str = ""):
    """
    Generates an audio sample. Routes to MLX on Mac and standard PyTorch on Windows for 'local' engine.
    """
    is_jazz = "jazz" in prompt.lower() or "ジャズ" in prompt.lower()
    style_suffix = ""
    if is_jazz:
        style_suffix = ", sophisticated lush jazz chords, elegant bossa nova groove, smooth nuanced piano, lounge atmosphere, professional studio mix, high fidelity"
    
    # ULTRA-STRICT MUSICAL CONTEXT
    musical_context = f"KEY: {key}, BPM: {bpm}. MUST BE IN {key}."
    final_prompt = f"{musical_context} A professional high-fidelity stereo {prompt}{style_suffix}. The output MUST be strictly in the key of {key} and exactly {bpm} BPM. High quality, studio production, perfect loop."
    # Resolve the client samples folder path dynamically to ensure write permissions in macOS /Applications
    def get_samples_dir():
        script_dir = os.path.dirname(os.path.abspath(__file__))
        src_path = os.path.abspath(os.path.join(script_dir, "../../client/public/samples"))
        if os.path.exists(os.path.dirname(src_path)) and os.access(os.path.dirname(src_path), os.W_OK):
            os.makedirs(src_path, exist_ok=True)
            return src_path
        home_samples = os.path.join(str(Path.home()), ".jinbeibleton", "samples")
        os.makedirs(home_samples, exist_ok=True)
        return os.path.abspath(home_samples)

    samples_dir = get_samples_dir()
    
    # --- CLOUD GEMINI 3 (LYRIA ENGINE) ---
    if engine == "cloud_lyria":
        try:
            try:
                from google import genai
            except ImportError:
                return {"status": "error", "error": "Google GenAI SDK not installed"}
                
            if not api_key:
                return {"status": "error", "error": "Gemini API Key missing"}
                
            print(f"🌐 [LYRIA 3.1] GENERATING (REST API): '{final_prompt}'")
            
            # TIERED AUTO-HEALING (Using actual Lyria models discovered in test scripts)
            model_tiers = ['lyria-3-clip-preview', 'lyria-3-pro-preview', 'gemini-3-flash-preview']
            
            response_data = None
            for model_name in model_tiers:
                try:
                    print(f"🚀 [LYRIA] Trying model via REST: {model_name}...")
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                    payload = {
                        "contents": [{
                            "role": "user",
                            "parts": [{
                                "text": f"Generate a 30-second high-fidelity studio stereo audio loop. The output MUST be strictly in the key of {key} and exactly {bpm} BPM. Style: {final_prompt}. Output only the audio."
                            }]
                        }],
                        "generationConfig": {
                            "response_modalities": ["AUDIO"]
                        }
                    }
                    
                    # Try both camelCase and snake_case for maximum compatibility
                    # (Google's API is inconsistent between versions)
                    payload["generationConfig"]["responseModalities"] = ["AUDIO"]

                    # Use a very long timeout (300s) for the raw HTTP request
                    with httpx.Client(timeout=300.0) as client:
                        print(f"📡 [DEBUG] Sending REST request to {model_name}...")
                        resp = client.post(url, json=payload)
                        print(f"📡 [DEBUG] Response Status: {resp.status_code}")
                        if resp.status_code == 200:
                            response_data = resp.json()
                            print(f"📡 [DEBUG] Success! Response JSON keys: {list(response_data.keys())}")
                            break
                        else:
                            print(f"📡 [DEBUG] Error Body: {resp.text}")
                            print(f"   - {model_name} HTTP {resp.status_code}: {resp.text[:100]}...")
                except Exception as e:
                    print(f"📡 [DEBUG] Exception during REST call: {e}")
                    print(f"   - {model_name} FAILED: {str(e)[:100]}...")
                    continue

            if not response_data or 'candidates' not in response_data:
                raise Exception("Cloud Lyria REST call returned no candidates (blocked or rate-limited).")

            import io
            import torchaudio

            # Extract audio data from REST response format
            candidate = response_data['candidates'][0]
            parts = candidate.get('content', {}).get('parts', [])
            print(f"📡 [DEBUG] Found {len(parts)} parts in response.")
            
            if not parts:
                print(f"⚠️ [LYRIA REST] Candidate blocked or empty! Full candidate data:")
                print(json.dumps(candidate, indent=2))
                raise Exception("No parts in response (safety/recitation block).")
            
            audio_bytes = None
            text_response = ""
            
            for i, part in enumerate(parts):
                print(f"📡 [DEBUG] Part {i} keys: {list(part.keys())}")
                
                if 'text' in part:
                    text_response += part['text']
                    print(f"📡 [DEBUG] Part {i} text: {part['text'][:100]}...")

                inline_data = part.get('inlineData')
                if inline_data:
                    print(f"📡 [DEBUG] Part {i} has inlineData. MimeType: {inline_data.get('mimeType')}")
                    audio_bytes = base64.b64decode(inline_data.get('data'))
                    break
                
                # Check for direct 'data' key (fallback)
                if 'data' in part:
                    print(f"📡 [DEBUG] Part {i} has direct data key.")
                    audio_bytes = base64.b64decode(part['data'])
                    break

            if not audio_bytes:
                raise Exception("No audio data found in REST response parts.")

            # Create standard audio directory
            os.makedirs(samples_dir, exist_ok=True)
            
            # Save raw bytes to temp file for ffmpeg conversion
            import tempfile
            mime_type = "audio/mpeg"
            is_mp3 = "mpeg" in mime_type or "mp3" in mime_type
            raw_ext = ".mp3" if is_mp3 else ".wav"
            
            with tempfile.NamedTemporaryFile(suffix=raw_ext, delete=False) as tmp_in:
                tmp_in.write(audio_bytes)
                temp_in_path = tmp_in.name

            try:
                filename = f"ai_lyria_{int(time.time())}.wav"
                filepath = os.path.join(samples_dir, filename)
                
                # Convert to 16-bit PCM, 44.1kHz, stereo WAV for maximum browser compatibility and high-fidelity Ableton import
                import subprocess
                cmd = ["ffmpeg", "-y", "-i", temp_in_path, "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2", filepath]
                subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
                os.unlink(temp_in_path)
                print(f"✨ [LYRIA] Converted raw data to standard 16-bit 44.1kHz WAV using ffmpeg: {filename}")
                
                # --- HIGH-FIDELITY STEREO KEY ALIGNER ---
                try:
                    print(f"🎛 [STEREO ALIGNER] Transposing loop to match Ableton Key: {key}...")
                    import librosa
                    
                    # 1. Load original audio in pristine stereo (mono=False)
                    y_stereo, sr = librosa.load(filepath, sr=None, mono=False)
                    
                    # 2. Downmix a temporary copy to mono solely for key detection
                    if y_stereo.ndim == 2:
                        y_mono = librosa.to_mono(y_stereo)
                    else:
                        y_mono = y_stereo
                        
                    # 3. Detect dominant raw key using Chroma CQT
                    chroma = librosa.feature.chroma_cqt(y=y_mono, sr=sr)
                    chroma_mean = chroma.mean(axis=1)
                    detected_pitch_class = int(np.argmax(chroma_mean))
                    
                    # 4. Map target Ableton root note to pitch class
                    pitch_map = {
                        "C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3,
                        "E": 4, "F": 5, "F#": 6, "Gb": 6, "G": 7, "G#": 8,
                        "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11
                    }
                    target_root = key.split()[0]
                    target_pitch_class = pitch_map.get(target_root, 0)
                    
                    # Calculate the musical transposition interval (semitones)
                    shift = target_pitch_class - detected_pitch_class
                    if shift > 6: shift -= 12
                    elif shift < -6: shift += 12
                    
                    # 5. Apply transposition if pitch shift is required
                    if shift != 0:
                        print(f"🎛 [STEREO ALIGNER] Transposing: {shift:+d} semitones (Detected root: {detected_pitch_class} -> Target: {target_pitch_class})")
                        if y_stereo.ndim == 2:
                            # Process left and right channels independently to preserve beautiful stereo width
                            y_left = librosa.effects.pitch_shift(y_stereo[0], sr=sr, n_steps=shift)
                            y_right = librosa.effects.pitch_shift(y_stereo[1], sr=sr, n_steps=shift)
                            y_stereo = np.stack([y_left, y_right])
                        else:
                            y_stereo = librosa.effects.pitch_shift(y_stereo, sr=sr, n_steps=shift)
                            
                        # 6. Save the transposed high-fidelity stereo WAV back (soundfile expects shape: samples x channels)
                        if y_stereo.ndim == 2:
                            sf.write(filepath, y_stereo.T, sr)
                        else:
                            sf.write(filepath, y_stereo, sr)
                        print(f"✨ [STEREO ALIGNER] Loop successfully transposed & synced to {key}!")
                    else:
                        print(f"✨ [STEREO ALIGNER] Key already matches target {key}. Transposition skipped!")
                        
                except Exception as align_err:
                    import traceback
                    print(f"⚠️ [STEREO ALIGNER WARNING] Transposition skipped or failed:")
                    traceback.print_exc()

                return {"status": "success", "file": f"/samples/{filename}"}
            except Exception as ffmpeg_err:
                print(f"⚠️ [LYRIA] ffmpeg conversion failed: {ffmpeg_err}. Saving raw with correct extension.")
                
                # Ultimate fallback: save with the correct extension (.mp3 or .wav)
                is_mp3 = "mpeg" in mime_type or "mp3" in mime_type
                ext = ".mp3" if is_mp3 else ".wav"
                filename = f"ai_lyria_{int(time.time())}{ext}"
                filepath = os.path.join(samples_dir, filename)
                with open(filepath, "wb") as f:
                    f.write(audio_bytes)
                return {"status": "success", "file": f"/samples/{filename}"}

        except Exception as lyria_err:
            import traceback
            print(f"❌ [LYRIA ERROR] Cloud Lyria generation failed: {lyria_err}")
            traceback.print_exc()
            return {"status": "error", "error": f"Cloud Lyria generation failed: {str(lyria_err)}"}

    # --- LOCAL ENGINE (AUTO-ROUTING) ---
    try:
        model = get_local_model()
        if model is None:
            os_name = "Windows" if not IS_MAC else "Mac"
            lib_name = "audiocraft" if not IS_MAC else "audiocraft-mlx"
            return {"status": "error", "error": f"{os_name}用のローカル生成ライブラリ({lib_name})が未インストールですワン！"}

        print(f"🎹 [LOCAL-GEN] OS: {platform.system()} | Engine: {'MLX' if IS_MAC else 'Torch'}")
        
        # Consistent parameters
        gen_duration = 8 
        
        if IS_MAC:
            # MLX Path
            model.set_generation_params(duration=gen_duration, top_k=250, temperature=1.0)
            wavs = model.generate([final_prompt], progress=True)
            audio_data = wavs[0].transpose(1, 0) # [Samples, Channels]
            sample_rate = 32000
        else:
            # Torch Path (Windows)
            model.set_generation_params(duration=gen_duration)
            wavs = model.generate([final_prompt], progress=True)
            # Audiocraft returns [Batch, Channels, Samples] on GPU/CPU
            audio_data = wavs[0].cpu().numpy().transpose(1, 0)
            sample_rate = model.sample_rate

        filename = f"ai_local_{int(time.time())}.wav"
        filepath = os.path.join(samples_dir, filename)
        sf.write(filepath, audio_data, sample_rate) 
        
        print(f"✨ [LOCAL-GEN] Success: {filename}")
        return {"status": "success", "file": f"/samples/{filename}"}

    except Exception as e:
        print(f"❌ [LOCAL-GEN] ERROR: {str(e)}")
        return {"status": "error", "error": str(e)}
    
    finally:
        # Clear VRAM/Memory if possible
        if IS_MAC:
            try:
                import mlx.core as mx
                mx.clear_cache()
            except: pass
        elif torch and torch.cuda.is_available():
            torch.cuda.empty_cache()

import os
import time
import torch
import numpy as np
import soundfile as sf
import base64

# Redirect HF Cache
os.environ["HF_HOME"] = os.path.abspath(os.path.join(os.getcwd(), ".hf_cache"))

from audiocraft_mlx.models import MusicGen
try:
    import mlx.core as mx
except ImportError:
    mx = None

try:
    from google import genai
except ImportError:
    genai = None

# Global model instance for local MLX
_mlx_model = None

def get_mlx_model():
    global _mlx_model
    if _mlx_model is None:
        print(f"🧠 MLX ENGINE: Loading MusicGen (Stable Stereo-Medium)...")
        _mlx_model = MusicGen.get_pretrained("facebook/musicgen-stereo-medium")
    return _mlx_model

def generate_sample(prompt: str, duration: int = 5, key: str = "C Major", bpm: int = 120, engine: str = "local_mlx", api_key: str = ""):
    """
    Generates an audio sample using either Local Transformers (MusicGen) or Cloud (Google Lyria/Gemini).
    """
    is_jazz = "jazz" in prompt.lower() or "ジャズ" in prompt.lower()
    style_suffix = ""
    if is_jazz:
        style_suffix = ", sophisticated lush jazz chords, elegant bossa nova groove, smooth nuanced piano, lounge atmosphere, professional studio mix, high fidelity"
    
    final_prompt = f"In the key of {key} and {bpm} BPM, generate a professional stereo {prompt}{style_suffix}, loop, studio quality, 4k audio."
    
    samples_dir = os.path.abspath(os.path.join(os.getcwd(), "..", "client", "public", "samples"))
    os.makedirs(samples_dir, exist_ok=True)
    
    # --- CLOUD GEMINI 3 (LYRIA ENGINE) ---
    if engine == "cloud_lyria":
        if not genai:
            return {"status": "error", "error": "Google GenAI SDK not installed"}
        if not api_key:
            return {"status": "error", "error": "Gemini API Key missing"}
            
        try:
            print(f"🌐 [LYRIA 3.1] GENERATING: '{final_prompt}'")
            client = genai.Client(api_key=api_key)
            
            # TIERED AUTO-HEALING (GEMINI 3 -> 1.5 Pro -> 1.5 Flash)
            model_tiers = [
                'gemini-3-flash-preview',
                'gemini-3.1-pro-preview',
                'gemini-2.0-flash'
            ]
            
            response = None
            for model_name in model_tiers:
                try:
                    print(f"🌐 [LYRIA 3.1] TRYING MODEL: '{model_name}'...")
                    response = client.models.generate_content(
                        model=model_name,
                        contents=f"Generate an 8-second high-fidelity stereo audio loop based on this description: {final_prompt}. Return only the audio data."
                    )
                    print(f"✅ [LYRIA 3.1] Success with '{model_name}'")
                    break
                except Exception as ge:
                    if "404" in str(ge): continue
                    raise ge # Re-raise if it's a real error (quota/key)

            if not response:
                return {"status": "error", "error": "LYRIA 3.1: 利用可能なモデルが見つかりません (404)"}

            audio_found = False
            for part in response.candidates[0].content.parts:
                if part.inline_data:
                    filename = f"ai_lyria_{int(time.time())}.wav"
                    filepath = os.path.join(samples_dir, filename)
                    with open(filepath, "wb") as f:
                        f.write(part.inline_data.data)
                    audio_found = True
                    break
            
            if audio_found:
                print(f"✨ [LYRIA 3.1] Success: {filename}")
                return {"status": "success", "file": f"/samples/{filename}"}
            else:
                return {"status": "error", "error": "LYRIA 3.1: 音声データが返されませんでした"}
        except Exception as e:
            err_str = str(e)
            jap_err = "APIキーが無効か、利用権限がありません"
            if "quota" in err_str.lower(): jap_err = "リクエスト制限（Quota）を超過しました"
            
            print(f"❌ [LYRIA 3.1] ERROR: {err_str}")
            return {"status": "error", "error": f"LYRIA 3.1 生成失敗: {jap_err}"}

    # --- LOCAL MLX ENGINE ---
    try:
        model = get_mlx_model()
        print(f"🎹 MLX GENERATING (STABLE): '{final_prompt}'")

        model.set_generation_params(duration=8, top_k=250, temperature=1.0)
        wavs = model.generate([final_prompt], progress=True)
        
        filename = f"ai_mlx_{int(time.time())}.wav"
        filepath = os.path.join(samples_dir, filename)
        
        audio_data = wavs[0].transpose(1, 0)
        sf.write(filepath, audio_data, 32000) 
        
        print(f"✨ MLX Success: {filename} (STEREO)")
        return {"status": "success", "file": f"/samples/{filename}"}

    except Exception as e:
        print(f"❌ MLX ENGINE ERROR: {str(e)}")
        return {"status": "error", "error": str(e)}
    
    finally:
        if mx and hasattr(mx, "clear_cache"):
            print("🧹 MLX: Clearing GPU memory cache...")
            mx.clear_cache()

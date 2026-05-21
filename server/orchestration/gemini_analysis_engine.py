import os
import json
import time
import subprocess
import tempfile
from google import genai
from google.genai import types
from tenacity import retry, stop_after_attempt, wait_exponential

def compress_audio(input_path: str):
    """
    Compresses audio using Mac's afconvert to a lightweight AAC/MP4 file.
    """
    temp_dir = tempfile.gettempdir()
    output_path = os.path.join(temp_dir, "gemini_analysis_temp.m4a")
    
    print(f"📦 [COMPRESSION] Compressing {os.path.basename(input_path)} to AAC...")
    try:
        if os.path.exists(output_path):
            os.remove(output_path)
            
        subprocess.run([
            "afconvert", "-f", "m4af", "-d", "aac", "-b", "128000",
            input_path, output_path
        ], check=True)
        return output_path
    except Exception as e:
        print(f"⚠️ [COMPRESSION] afconvert failed: {e}")
        return input_path

def analyze_audio_with_gemini(file_path: str, api_key: str, bpm: float = 120.0, preferred_model: str = "gemini-3.5-flash"):
    """
    Uploads audio to Gemini with absolute connection stability.
    """
    if not api_key:
        raise Exception("Gemini API Key is missing.")

    # 0. Compress
    original_path = file_path
    upload_path = compress_audio(file_path) if file_path.lower().endswith(".wav") else file_path

    print(f"🌟 [GEMINI ANALYSIS] Initializing GenAI Client (STABLE MODE)...")
    # Setting timeout to None means wait forever - most stable for flaky connections
    client = genai.Client(
        api_key=api_key,
        http_options={'timeout': None} 
    )

    # 1. Upload
    file_size_mb = os.path.getsize(upload_path) / (1024 * 1024)
    print(f"📤 [GEMINI ANALYSIS] Sending file ({file_size_mb:.2f} MB)...")
    
    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=2, min=4, max=20))
    def upload_with_retry():
        return client.files.upload(file=upload_path)

    try:
        start_upload = time.time()
        file_metadata = upload_with_retry()
        print(f"✅ [GEMINI ANALYSIS] Uploaded in {time.time() - start_upload:.1f}s")
    except Exception as e:
        print(f"❌ [GEMINI ANALYSIS] PERMANENT UPLOAD FAILURE: {e}")
        if upload_path != original_path: os.remove(upload_path)
        raise e
    
    # 2. Process
    print(f"⏳ [GEMINI ANALYSIS] Server processing...")
    wait_start = time.time()
    while file_metadata.state.name == "PROCESSING":
        time.sleep(5)
        if time.time() - wait_start > 600:
            raise Exception("Server processing timeout.")
        file_metadata = client.files.get(name=file_metadata.name)
    
    if file_metadata.state.name == "FAILED":
        raise Exception("Gemini processing failed.")

    # 3. Prompt
    prompt = f"""
    Analyze the musical structure of the provided audio file.
    Tempo: {bpm} BPM.
    Time Signature: 4/4.
    One bar = {240/bpm:.4f} seconds.
    
    Instructions:
    1. Identify the key structural sections (e.g., Intro, Verse, Pre-Chorus, Chorus, Build-up, Drop, Bridge, Outro).
    2. Assume the song starts on the grid at 0.0 seconds.
    3. Calculate the start time of each section in seconds. Each section transition MUST align with the start of a bar.
    4. Therefore, each section's 'start_time' must be a multiple of the bar length ({240/bpm:.4f} seconds).
    
    Return EXACTLY a JSON array of objects, with no extra markdown text or wrapping (just the JSON array):
    [
      {{"name": "Intro", "start_time": 0.0}},
      {{"name": "Verse", "start_time": 16.0}},
      ...
    ]
    """

    # 4. Generate
    all_models = ["gemini-3.5-flash", "gemini-3.5-pro", "gemini-3-flash-preview", "gemini-3-pro-preview", "gemini-1.5-pro", "gemini-2.0-flash-exp", "gemini-1.5-flash"]
    if preferred_model in all_models: all_models.remove(preferred_model)
    models_to_try = [preferred_model] + all_models
    
    for model_id in models_to_try:
        try:
            print(f"📡 [GEMINI ANALYSIS] Requesting {model_id}...")
            response = client.models.generate_content(
                model=model_id,
                contents=[file_metadata, prompt],
                config=types.GenerateContentConfig(response_mime_type="application/json")
            )
            
            client.files.delete(name=file_metadata.name)
            if upload_path != original_path: os.remove(upload_path)

            if response.text:
                sections = json.loads(response.text)
                print(f"✅ [GEMINI ANALYSIS] Success with {model_id} ({len(sections)} sections)")
                return sections
        except Exception as e:
            print(f"⚠️ [GEMINI ANALYSIS] {model_id} failed, trying next...")
            continue

    if upload_path != original_path: os.remove(upload_path)
    raise Exception("All Gemini models failed.")

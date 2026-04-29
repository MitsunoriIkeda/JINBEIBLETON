import os
import json
import time
from mido import MidiFile, MidiTrack, Message

# MIDI Constants
TICKS_PER_BEAT = 480

def generate_midi_clip(prompt: str, api_key: str = "", midi_engine: str = "cloud_gemini", openai_key: str = "", bpm: int = 120, key: str = "C Major"):
    """
    Generates a professional MIDI file based on the prompt using Gemini, OpenAI, or Ollama.
    """
    if not api_key and not openai_key and midi_engine != "local_ollama":
        return {"status": "error", "error": "API Key missing"}

    # Ensure numeric types
    bpm = int(float(bpm)) if bpm else 120

    print(f"🎹 [MIDI ENGINE] Composing MIDI for: '{prompt}' (Engine: {midi_engine})")
    
    # SYSTEM PROMPT for MIDI generation
    MIDI_SYSTEM_PROMPT = f"""
    You are a world-class music producer and jazz pianist. 
    Your task is to generate a professional-grade chord progression or musical sequence as a JSON object.
    
    STYLE PREFERENCE: {prompt}
    BPM: {bpm}
    KEY: {key}
    
    RULES:
    1. If the style is JAZZ, use advanced voicings with tensions (9th, 11th, 13th, alt chords).
    2. If the style is CITYPOP, use lush Major 7ths and sophisticated syncopation.
    3. Output the sequence as a list of "notes" in JSON.
    4. Each note must have: "pitch" (MIDI note number 0-127), "start_tick" (tick from start), "duration_ticks", and "velocity" (0-127).
    5. Ensure the progression is musically sound and follows standard theory for the requested genre.
    6. LENGTH: Default to 8 bars if not specified. If the user mentions a specific number of bars (e.g., "4 bars", "16 bars"), you MUST follow that instruction exactly.
    (480 ticks per beat, 4 beats per bar = 1920 ticks per bar).
    
    OUTPUT FORMAT (STRICT JSON ONLY):
    {{
      "sequence_name": "string",
      "bars": number,
      "notes": [
        {{"pitch": 60, "start_tick": 0, "duration_ticks": 480, "velocity": 85}},
        ...
      ]
    }}
    """

    try:
        raw_response_text = ""
        success_model = None

        # --- OPTION 1: CLOUD GEMINI ---
        if midi_engine == "cloud_gemini" and api_key:
            from google import genai
            client = genai.Client(api_key=api_key)
            model_tiers = ['gemini-3-flash-preview', 'gemini-3.1-pro-preview', 'gemini-2.0-flash']
            
            for model_name in model_tiers:
                try:
                    print(f"🚀 [MIDI ENGINE] TRYING GEMINI '{model_name}'...")
                    res = client.models.generate_content(model=model_name, contents=MIDI_SYSTEM_PROMPT)
                    raw_response_text = res.text.strip()
                    success_model = f"GEMINI ({model_name})"
                    print(f"✅ [MIDI ENGINE] Success with {success_model}")
                    break
                except Exception as e:
                    print(f"   - '{model_name}' FAILED: {str(e)[:100]}...")
                    continue

        # --- OPTION 2: CLOUD OPENAI ---
        elif midi_engine == "cloud_openai" and openai_key:
            try:
                print(f"🚀 [MIDI ENGINE] TRYING OPENAI 'gpt-4o'...")
                import openai
                client = openai.OpenAI(api_key=openai_key)
                res = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "system", "content": MIDI_SYSTEM_PROMPT}],
                    response_format={ "type": "json_object" }
                )
                raw_response_text = res.choices[0].message.content.strip()
                success_model = "OPENAI (GPT-4O)"
                print(f"✅ [MIDI ENGINE] Success with {success_model}")
            except Exception as e:
                print(f"❌ [MIDI ENGINE] OPENAI FAILED: {e}")

        # --- OPTION 3: LOCAL OLLAMA (FORCE OR FALLBACK) ---
        if not success_model:
            print(f"⚠️ [MIDI ENGINE] {'FORCING LOCAL' if midi_engine == 'local_ollama' else 'CLOUD FAILED'}. USING OLLAMA...")
            import ollama
            res = ollama.chat(
                model="gemma4:latest",
                messages=[{'role': 'user', 'content': MIDI_SYSTEM_PROMPT}]
            )
            raw_response_text = res['message']['content'].strip()
            success_model = "LOCAL OLLAMA"
            print(f"✅ [MIDI ENGINE] Success with {success_model}")

        # Extract JSON from response (handling potential markdown blocks)
        json_text = raw_response_text
        if "```json" in json_text:
            json_text = json_text.split("```json")[1].split("```")[0].strip()
        elif "```" in json_text:
            json_text = json_text.split("```")[1].split("```")[0].strip()
        
        # Strip any leading/trailing non-JSON noise
        start_idx = json_text.find('{')
        end_idx = json_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_text = json_text[start_idx:end_idx+1]
            
        response_data = json.loads(json_text)
        notes = response_data.get("notes", [])

        # Create MIDI File
        import mido
        mid = mido.MidiFile(ticks_per_beat=TICKS_PER_BEAT)
        track = mido.MidiTrack()
        mid.tracks.append(track)
        
        # Add Tempo
        tempo = mido.bpm2tempo(bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo))

        # Build events
        events = []
        max_tick = 0
        for n in notes:
            pitch = max(0, min(127, int(n.get("pitch", 60))))
            velocity = max(0, min(127, int(n.get("velocity", 80))))
            start_tick = max(0, int(n.get("start_tick", 0)))
            duration = max(1, int(n.get("duration_ticks", 480)))
            
            end_tick = start_tick + duration
            if end_tick > max_tick:
                max_tick = end_tick

            events.append({"tick": start_tick, "type": "on", "pitch": pitch, "vel": velocity})
            events.append({"tick": end_tick, "type": "off", "pitch": pitch, "vel": 0})
        
        # ENFORCE MINIMUM LENGTH: Ensure the clip at least reaches the requested bar length
        # Attempt to parse bar count from prompt (e.g. "16 bars")
        requested_bars = 8
        import re
        match = re.search(r'(\d+)\s*(小節|bars|bar|measures|measure)', prompt)
        if match:
            requested_bars = int(match.group(1))
        
        target_ticks = requested_bars * 1920 # 4/4 assume
        if max_tick < target_ticks:
            # Add a silent "Note Off" at the end to force the track length
            events.append({"tick": target_ticks, "type": "off", "pitch": 0, "vel": 0})

        # Sort and Delta-fy
        events.sort(key=lambda x: x["tick"])
        last_tick = 0
        for e in events:
            delta = e["tick"] - last_tick
            if e["type"] == "on":
                track.append(mido.Message('note_on', note=e["pitch"], velocity=e["vel"], time=delta))
            else:
                track.append(mido.Message('note_off', note=e["pitch"], velocity=e["vel"], time=delta))
            last_tick = e["tick"]

        # Save
        filename = f"ai_midi_{int(time.time())}.mid"
        save_path = os.path.join(os.path.dirname(__file__), "..", "..", "client", "public", "samples", filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        mid.save(save_path)
        
        print(f"✨ [MIDI ENGINE] Saved: {filename} (Length: {requested_bars} bars)")
        return {"status": "success", "file": f"/samples/{filename}"}

    except Exception as e:
        print(f"❌ [MIDI ENGINE] ERROR: {e}")
        return {"status": "error", "error": str(e)}

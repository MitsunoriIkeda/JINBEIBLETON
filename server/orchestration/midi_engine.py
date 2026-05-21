import os
import json
import time
from mido import MidiFile, MidiTrack, Message

# MIDI Constants
TICKS_PER_BEAT = 480

def generate_midi_clip(prompt: str, api_key: str = "", midi_engine: str = "cloud_gemini", openai_key: str = "", bpm: int = 120, key: str = "C Major", claude_key: str = "", chord_notes: list = None, is_melody: bool = False, ollama_model: str = "gemma4:latest"):
    """
    Generates a professional MIDI file based on the prompt using Gemini, OpenAI, Claude, or Ollama.
    """
    print(f"🎹 [MIDI ENGINE] Composing {'MELODY' if is_melody else 'MIDI'} (Engine: {midi_engine} | Model: {ollama_model if midi_engine == 'local_ollama' else 'Cloud'})")
    
    if not api_key and not openai_key and midi_engine != "local_ollama":
        return {"status": "error", "error": "API Key missing"}

    # Ensure numeric types
    bpm = int(float(bpm)) if bpm else 120
    
    # Base SYSTEM PROMPT
    chord_str = ""
    if chord_notes and len(chord_notes) > 0:
        # Format chord notes for the prompt
        chord_str = "Selected Chord Progression (from Ableton):\n"
        for cn in chord_notes:
            chord_str += f"- Pitch: {cn.get('pitch')} | Time (beats): {cn.get('start_time')} | Duration: {cn.get('duration')}\n"

    # --- NEW: SCALE ASSISTANT ---
    # Provide the AI with the exact notes allowed in the scale to prevent key errors
    def get_scale_pitches(key_str):
        scales = {
            "C Major": [0, 2, 4, 5, 7, 9, 11],
            "C Minor": [0, 2, 3, 5, 7, 8, 10],
            "C# Major": [1, 3, 5, 6, 8, 10, 0],
            "C# Minor": [1, 3, 4, 6, 8, 9, 11],
            "D Major": [2, 4, 6, 7, 9, 11, 1],
            "D Minor": [2, 4, 5, 7, 9, 10, 0],
            "D# Major": [3, 5, 7, 8, 10, 0, 2],
            "D# Minor": [3, 5, 6, 8, 10, 11, 1],
            "E Major": [4, 6, 8, 9, 11, 1, 3],
            "E Minor": [4, 6, 7, 9, 11, 0, 2],
            "F Major": [5, 7, 9, 10, 0, 2, 4],
            "F Minor": [5, 7, 8, 10, 0, 1, 3],
            "F# Major": [6, 8, 10, 11, 1, 3, 5],
            "F# Minor": [6, 8, 9, 11, 1, 2, 4],
            "G Major": [7, 9, 11, 0, 2, 4, 6],
            "G Minor": [7, 9, 10, 0, 2, 3, 5],
            "G# Major": [8, 10, 0, 1, 3, 5, 7],
            "G# Minor": [8, 10, 11, 1, 3, 4, 6],
            "A Major": [9, 11, 1, 2, 4, 6, 8],
            "A Minor": [9, 11, 0, 2, 4, 5, 7],
            "A# Major": [10, 0, 2, 3, 5, 7, 9],
            "A# Minor": [10, 0, 1, 3, 5, 6, 8],
            "B Major": [11, 1, 3, 4, 6, 8, 10],
            "B Minor": [11, 1, 2, 4, 6, 7, 9]
        }
        return scales.get(key_str, [0, 2, 4, 5, 7, 9, 11]) # Default to C Major

    scale_notes = get_scale_pitches(key)
    
    if midi_engine == "local_ollama":
        if is_melody:
            MIDI_SYSTEM_PROMPT = f"""
            You are a world-class jazz and pop composer.
            
            STRICT REQUIREMENTS:
            1. KEY: {key}. Available pitch classes: {scale_notes} (MIDI mod 12).
            2. RULES: ONLY use the pitch classes listed above. Do NOT use any other notes.
            3. BPM: {bpm}.
            4. TASK: {prompt}
            {chord_str}
            
            STRICT ARRANGEMENT RULES:
            1. MELODY: Create a sophisticated, rhythmic MONOPHONIC melody that aligns with the chord progression provided above (match the timing and harmonic transitions of the chords).
            2. JAZZ FEEL: Use syncopation (notes starting at 240, 720, 1200 ticks). Avoid starting every note on the beat.
            3. LENGTH: EXACTLY 8 BARS.
            4. Ticks per beat: 480.
            
            OUTPUT FORMAT (STRICT JSON ONLY - VERY IMPORTANT):
            {{
              "sequence_name": "Melody",
              "bars": 8,
              "notes": [
                [70, 0, 480, 90],
                [72, 480, 240, 95]
              ]
            }}
            NOTE: Each item inside "notes" is a 4-element array: [pitch, start_tick, duration_ticks, velocity]. Output ONLY valid JSON.
            """
        else:
            MIDI_SYSTEM_PROMPT = f"""
            You are a professional Jazz Harmony Expert.
            
            STRICT REQUIREMENTS:
            1. KEY: {key}. Available pitch classes: {scale_notes} (MIDI mod 12).
            2. RULES: All notes in your chords MUST be from the {key} scale.
            3. BPM: {bpm}.
            4. TASK: {prompt}
            
            STRICT ARRANGEMENT RULES:
            1. VOICING: Use professional Jazz voicings (Shell voicings, 7th, 9th, 11th, 13th). 
            2. STRUCTURE: Each bar must have a distinct chord. DO NOT repeat the same chord for 8 bars.
            3. RHYTHM: Use "Comping" style. Occasionally start chords 240 ticks BEFORE the beat for a jazz swing feel.
            4. BARS: Generate EXACTLY 8 BARS.
            5. ROOT: Always place a root note in the bass (pitch 36-46) and the harmony above (pitch 55-75).
            
            OUTPUT FORMAT (STRICT JSON ONLY - VERY IMPORTANT):
            {{
              "sequence_name": "Jazz Comping",
              "bars": 8,
              "notes": [
                [41, 0, 1800, 80],
                [65, 0, 1800, 75]
              ]
            }}
            NOTE: Each item inside "notes" is a 4-element array: [pitch, start_tick, duration_ticks, velocity]. Output ONLY valid JSON.
            """
    else:
        if is_melody:
            MIDI_SYSTEM_PROMPT = f"""
            You are a world-class jazz and pop composer.
            
            STRICT REQUIREMENTS:
            1. KEY: {key}. Available pitch classes: {scale_notes} (MIDI mod 12).
            2. RULES: ONLY use the pitch classes listed above. Do NOT use any other notes.
            3. BPM: {bpm}.
            4. TASK: {prompt}
            {chord_str}
            
            STRICT ARRANGEMENT RULES:
            1. MELODY: Create a sophisticated, rhythmic MONOPHONIC melody that aligns with the chord progression provided above (match the timing and harmonic transitions of the chords).
            2. JAZZ FEEL: Use syncopation (notes starting at 240, 720, 1200 ticks). Avoid starting every note on the beat.
            3. LENGTH: EXACTLY 8 BARS.
            4. Ticks per beat: 480.
            
            OUTPUT FORMAT (STRICT JSON ONLY):
            {{
              "sequence_name": "Melody",
              "bars": 8,
              "notes": [
                {{"pitch": 70, "start_tick": 0, "duration_ticks": 480, "velocity": 90}},
                ...
              ]
            }}
            """
        else:
            MIDI_SYSTEM_PROMPT = f"""
            You are a professional Jazz Harmony Expert.
            
            STRICT REQUIREMENTS:
            1. KEY: {key}. Available pitch classes: {scale_notes} (MIDI mod 12).
            2. RULES: All notes in your chords MUST be from the {key} scale.
            3. BPM: {bpm}.
            4. TASK: {prompt}
            
            STRICT ARRANGEMENT RULES:
            1. VOICING: Use professional Jazz voicings (Shell voicings, 7th, 9th, 11th, 13th). 
            2. STRUCTURE: Each bar must have a distinct chord. DO NOT repeat the same chord for 8 bars.
            3. RHYTHM: Use "Comping" style. Occasionally start chords 240 ticks BEFORE the beat for a jazz swing feel.
            4. BARS: Generate EXACTLY 8 BARS.
            5. ROOT: Always place a root note in the bass (pitch 36-46) and the harmony above (pitch 55-75).
            
            OUTPUT FORMAT (STRICT JSON ONLY):
            {{
              "sequence_name": "Jazz Comping",
              "bars": 8,
              "notes": [
                {{"pitch": 41, "start_tick": 0, "duration_ticks": 1800, "velocity": 80}},
                {{"pitch": 65, "start_tick": 0, "duration_ticks": 1800, "velocity": 75}},
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
            # Use v1beta for newer models
            client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
            
            # Priority: Free Tier 'gemini-3-flash-preview' first, then newer stable models
            model_tiers = [
                'gemini-3-flash-preview', 
                'gemini-3.1-flash-lite',
                'gemini-3.1-pro',
                'gemini-1.5-flash-latest',
                'gemini-1.5-pro-latest',
                'gemini-1.5-pro',
                'gemini-1.5-flash'
            ]
            
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
            
            # (NO FALLBACK) - Strictly use Gemini as requested
            if not success_model:
                return {"status": "error", "error": "All Gemini models failed. No fallback allowed."}

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
                return {"status": "error", "error": f"OPENAI FAILED: {str(e)}"}

        # --- OPTION 3: LOCAL OLLAMA ---
        elif midi_engine == "local_ollama":
            print(f"🏠 [MIDI ENGINE] USING OLLAMA ({ollama_model})...")
            import ollama
            res = ollama.chat(
                model=ollama_model,
                messages=[{'role': 'user', 'content': MIDI_SYSTEM_PROMPT}],
                format='json'
            )
            raw_response_text = res['message']['content'].strip()
            success_model = f"LOCAL OLLAMA ({ollama_model})"
            print(f"✅ [MIDI ENGINE] Success with {success_model}")

        if not success_model:
            return {"status": "error", "error": f"MIDI Engine '{midi_engine}' failed or not configured."}

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
            if isinstance(n, list) and len(n) >= 4:
                try:
                    pitch = max(0, min(127, int(n[0])))
                    start_tick = max(0, int(n[1]))
                    duration = max(1, int(n[2]))
                    velocity = max(0, min(127, int(n[3])))
                except (ValueError, TypeError):
                    continue
            elif isinstance(n, dict):
                pitch = max(0, min(127, int(n.get("pitch", 60))))
                velocity = max(0, min(127, int(n.get("velocity", 80))))
                start_tick = max(0, int(n.get("start_tick", 0)))
                duration = max(1, int(n.get("duration_ticks", 480)))
            else:
                continue
            
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

        # Resolve the client samples folder path dynamically to ensure write permissions in macOS /Applications
        def get_samples_dir():
            from pathlib import Path
            script_dir = os.path.dirname(os.path.abspath(__file__))
            src_path = os.path.abspath(os.path.join(script_dir, "../../client/public/samples"))
            if os.path.exists(os.path.dirname(src_path)) and os.access(os.path.dirname(src_path), os.W_OK):
                os.makedirs(src_path, exist_ok=True)
                return src_path
            home_samples = os.path.join(str(Path.home()), ".jinbeibleton", "samples")
            os.makedirs(home_samples, exist_ok=True)
            return os.path.abspath(home_samples)

        samples_dir = get_samples_dir()
        filename = f"ai_midi_{int(time.time())}.mid"
        save_path = os.path.join(samples_dir, filename)
        mid.save(save_path)
        
        print(f"✨ [MIDI ENGINE] Saved: {filename} (Length: {requested_bars} bars)")
        return {"status": "success", "file": f"/samples/{filename}"}

    except Exception as e:
        print(f"❌ [MIDI ENGINE] ERROR: {e}")
        return {"status": "error", "error": str(e)}

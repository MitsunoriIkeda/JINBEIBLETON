import librosa
import numpy as np

def analyze_local_audio(file_path: str):
    """
    Analyzes a local audio file and returns structural segments (Intro, Verse, Chorus, etc.)
    based on RMS energy heuristics.
    """
    print(f"🎵 [LOCAL ANALYSIS] Loading audio file: {file_path}")
    
    try:
        # Load audio (downsample to 22050 for faster analysis)
        y, sr = librosa.load(file_path, sr=22050)
        
        # Calculate RMS energy
        hop_length = 512
        rms = librosa.feature.rms(y=y, hop_length=hop_length)[0]
        
        # Smooth the RMS curve to find broad sections rather than tiny spikes
        # A 5-second smoothing window (roughly 200 frames at 22050/512)
        smoothing_frames = int((22050 / hop_length) * 5)
        if smoothing_frames % 2 == 0: smoothing_frames += 1 # must be odd for savgol
        from scipy.signal import savgol_filter
        
        # apply smoothing if signal is long enough
        if len(rms) > smoothing_frames:
            rms_smooth = savgol_filter(rms, smoothing_frames, 3)
        else:
            rms_smooth = rms
            
        # Detect novelty (boundaries)
        # Using librosa's onset detection or beat tracking can be too granular.
        # We will use simple thresholding on the derivative of smoothed RMS to find major shifts.
        derivative = np.diff(rms_smooth)
        
        # Find peaks in the derivative (sudden increases in energy = chorus/verse starts)
        from scipy.signal import find_peaks
        # peak threshold: mean + 1 std
        thresh = np.mean(np.abs(derivative)) + np.std(np.abs(derivative))
        peaks, _ = find_peaks(np.abs(derivative), height=thresh, distance=smoothing_frames)
        
        # Convert frame indices to timestamps
        boundary_times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
        
        # Add start (0.0) and end time
        duration = librosa.get_duration(y=y, sr=sr)
        boundaries = [0.0] + list(boundary_times) + [duration]
        boundaries = sorted(list(set(boundaries)))
        
        sections = []
        
        # Determine overall energy stats to classify sections
        section_energies = []
        for i in range(len(boundaries)-1):
            start_f = librosa.time_to_frames(boundaries[i], sr=sr, hop_length=hop_length)
            end_f = librosa.time_to_frames(boundaries[i+1], sr=sr, hop_length=hop_length)
            avg_e = np.mean(rms_smooth[start_f:end_f]) if end_f > start_f else 0
            section_energies.append(avg_e)
            
        if not section_energies:
            return [{"name": "Track", "start_time": 0.0, "end_time": duration}]
            
        max_e = max(section_energies)
        mean_e = np.mean(section_energies)
        
        # Name heuristically
        intro_used = False
        outro_used = False
        
        for i in range(len(boundaries)-1):
            start_t = boundaries[i]
            end_t = boundaries[i+1]
            e = section_energies[i]
            
            # Simple heuristic naming
            if i == 0 and e < mean_e:
                name = "Intro"
                intro_used = True
            elif i == len(boundaries)-2 and e < mean_e:
                name = "Outro"
                outro_used = True
            elif e > max_e * 0.85:
                name = "Chorus"
            elif e < mean_e * 0.8:
                name = "Breakdown"
            else:
                name = "Verse"
                
            sections.append({
                "name": name,
                "start_time": round(start_t, 2),
                "end_time": round(end_t, 2)
            })
            
        # Clean up consecutive same names (e.g., Verse followed by Verse)
        merged_sections = []
        for s in sections:
            if merged_sections and merged_sections[-1]["name"] == s["name"]:
                merged_sections[-1]["end_time"] = s["end_time"]
            else:
                merged_sections.append(s)
                
        # Counter for numbered names (e.g., Verse 1, Verse 2)
        counts = {"Verse": 1, "Chorus": 1, "Breakdown": 1}
        for s in merged_sections:
            if s["name"] in counts:
                base_name = s["name"]
                s["name"] = f"{base_name} {counts[base_name]}"
                counts[base_name] += 1
                
        print(f"✅ [LOCAL ANALYSIS] Found {len(merged_sections)} sections.")
        for s in merged_sections:
            print(f"   - {s['start_time']}s to {s['end_time']}s: {s['name']}")
            
        return merged_sections
        
    except Exception as e:
        print(f"❌ [LOCAL ANALYSIS ERROR] {str(e)}")
        raise e

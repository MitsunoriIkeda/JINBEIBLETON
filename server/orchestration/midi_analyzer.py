import mido
import json
import os

def analyze_midi_file(filepath: str):
    if not os.path.exists(filepath):
        return {"success": False, "error": f"File not found: {filepath}"}
    
    try:
        mid = mido.MidiFile(filepath)
        notes = []
        ticks_per_beat = mid.ticks_per_beat
        
        for track in mid.tracks:
            current_ticks = 0
            for msg in track:
                current_ticks += msg.time
                if msg.type == 'note_on' and msg.velocity > 0:
                    beats = current_ticks / ticks_per_beat
                    notes.append({
                        "pitch": msg.note,
                        "time": round(beats, 3),
                        "velocity": msg.velocity
                    })
        
        notes.sort(key=lambda x: x['time'])
        
        # Summary Logic
        summary = "ANALYSIS COMPLETE:\n"
        if not notes:
            summary += "EMPTY CLIP."
        else:
            bars = {}
            for n in notes:
                bar_num = int(n['time'] / 4) + 1
                if bar_num not in bars: bars[bar_num] = []
                bars[bar_num].append(n['pitch'])
            
            for b_idx in sorted(bars.keys())[:4]: # Limit to first 4 bars
                names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                p_names = sorted(list(set([names[p % 12] + str(int(p/12)-1) for p in bars[b_idx]])))
                summary += f"Bar {b_idx}: {', '.join(p_names)}\n"
        
        return {
            "success": True,
            "summary": summary,
            "note_count": len(notes)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

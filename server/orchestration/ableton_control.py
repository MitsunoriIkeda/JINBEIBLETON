import httpx
import json
import re
import asyncio

def prepare_ableton_actions(actions, text):
    """
    Applies Math Fixing and Command Guarding to the action list.
    Called before the execution loop.
    """
    
    # 1. HYBRID CALCULATION ENGINE: Fix LLM math errors using Regex
    def fix_musical_math(acts, text):
        # 1. Improved bar detection (handles "小説", "小説家", "章節", etc.)
        bar_pattern = r'(\d+)\s*(?:小節|小説|小説家|小接|章節|節)'
        bar_matches = re.findall(bar_pattern, text)
        
        # 2. Range detection (e.g., "97から105")
        range_pattern = r'(\d+)\s*(?:小節|小説|章節)?\s*(?:から|〜|～|—)\s*(\d+)\s*(?:小節|小説|章節)?'
        range_match = re.search(range_pattern, text)
        
        start_bar = None
        length_bars = None
        
        if range_match:
            start_bar = int(range_match.group(1))
            length_bars = int(range_match.group(2)) - start_bar
        elif bar_matches:
            start_bar = int(bar_matches[0])
            if len(bar_matches) > 1:
                length_bars = int(bar_matches[1]) - start_bar
        
        if start_bar is not None:
            for a in acts:
                if a.get("action") == "set_loop":
                    a["start"] = (start_bar - 1) * 4
                    if length_bars is not None:
                        a["length"] = length_bars * 4
                if a.get("action") == "record":
                    a["bar"] = start_bar - 2
            print(f"🧮 [MATH FIXER] Applied precise math: Start Bar {start_bar}, Length {length_bars}")
        return acts

    actions = fix_musical_math(actions, text)

    # 2. MARKER NORMALIZER (Frozen Feature)
    def normalize_markers(acts):
        for a in acts:
            if a.get("action") == "play_from_marker" and "name" in a:
                m_name = str(a["name"])
                # Remove spaces: "1 A" -> "1A"
                m_name = re.sub(r'(\d+)\s+([A-Za-z])', r'\1\2', m_name)
                # Convert "Dash" to "'" : "1Aダッシュ" -> "1A'"
                m_name = m_name.replace("ダッシュ", "'").replace("Dash", "'").replace("dash", "'")
                # Final Polish: Upper case for sections
                if re.match(r'^\d+[A-Za-z]\'?$', m_name):
                    m_name = m_name.upper()
                a["name"] = m_name
        return acts

    actions = normalize_markers(actions)

    # 3. COMMAND GUARD: Avoid self-cancelling actions
    has_record = any(a.get("action") == "record" for a in actions)
    if has_record:
        actions = [a for a in actions if a.get("action") not in ["play", "play_from_bar", "play_from_marker", "play_from_time"]]
        print(f"🛡 [GUARD] Stripped redundant play commands: {actions}")
    
    return actions

async def execute_ableton_action(act, http_client, manager):
    """
    Executes a single Ableton action (Bridge forwarding or Color organizing).
    """
    action_name = act["action"].lower()
    
    # --- SPECIAL CASE: Organize Colors ---
    if action_name == "organize_colors":
        print("🎨 [ORCHESTRATION] Organizing track colors...")
        try:
            resp = await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "get_tracks_info", "params": {}})
            tracks_info = resp.json().get("data", [])
            
            color_map = {
                "drums": 1, "kick": 1, "snare": 1, "hihat": 1, "perc": 1, "どらむ": 1, "dr": 1,
                "bass": 13, "sub": 13, "べーす": 13, "ba": 13, "bs": 13,
                "synth": 11, "lead": 11, "pad": 11, "chord": 11, "piano": 11, "ぴあの": 11, "しんせ": 11, "pf": 11, "pn": 11, "keys": 11,
                "guitar": 25, "gt": 25, "ぎたー": 25, "riff": 25, "onigiri": 25,
                "vocal": 27, "vox": 27, "voc": 27, "ぼーかる": 27, "vo": 27,
                "fx": 60, "siren": 60, "metal": 60, "bit": 60, "noise": 60, "reverb": 48, "delay": 48
            }
            
            for t in tracks_info:
                name_lower = t["name"].lower()
                target_color = 0
                for keyword, color_idx in color_map.items():
                    if keyword in name_lower:
                        target_color = color_idx
                        break
                
                if target_color != t.get("color"):
                    print(f"   🎨 [COLOR] Updating '{t['name']}' to index {target_color}")
                    await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={
                        "action": "set_track_color", 
                        "params": {"track_name": t["name"], "color": target_color}
                    })
            
            await manager.broadcast(json.dumps({"type": "SUCCESS", "msg": "COLORS ORGANIZED"}))
            return {"status": "success", "msg": "Colors organized"}
        except Exception as ce:
            print(f"❌ [COLOR ERROR] {ce}")
            return {"status": "error", "msg": str(ce)}
        
    # --- CASE: HUMANIZE (MIDI CLEANUP SKILL) ---
    elif action_name == "humanize":
        print(f"🪄 [SKILL] Humanizing selected clip...")
        try:
            # 1. Fetch current notes
            resp = await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "get_notes"})
            data = resp.json()
            if data.get("status") != "success":
                return data
            
            notes = data.get("data", [])
            if not notes:
                return {"status": "error", "msg": "No notes found in clip"}
            
            import random
            vel_amt = act.get("velocity_amount", 12)
            time_amt = act.get("timing_amount", 0.02)
            
            new_notes = []
            for n in notes:
                # Rule: Preserve accents at 127
                if n['velocity'] < 127:
                    n['velocity'] = max(1, min(126, n['velocity'] + random.randint(-vel_amt, vel_amt)))
                
                # Rule: Preserve downbeat anchor (time near 0)
                if n['start_time'] > 0.01:
                    n['start_time'] = max(0, n['start_time'] + (random.random() * 2 - 1) * time_amt)
                
                new_notes.append(n)
            
            # 2. Push back to Ableton
            await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={
                "action": "replace_notes",
                "params": {"notes": new_notes}
            })
            
            await manager.broadcast(json.dumps({"type": "SUCCESS", "msg": f"HUMANIZED {len(new_notes)} NOTES"}))
            return {"status": "success", "msg": f"Humanized {len(new_notes)} notes"}
        except Exception as he:
            print(f"❌ [HUMANIZE ERROR] {he}")
            return {"status": "error", "msg": str(he)}
            
    # --- GENERAL BRIDGE FORWARDING ---
    else:
        print(f"🔗 [BRIDGE] Forwarding '{action_name}' with params: {act}")
        try:
            resp = await http_client.post(
                "http://localhost:8005/api/v1/ableton/execute",
                json={"action": action_name, "params": act}
            )
            bridge_data = resp.json()
            
            if bridge_data.get("status") == "success":
                await manager.broadcast(json.dumps({
                    "type": "SUCCESS",
                    "msg": f"{action_name.upper()} SUCCESSFUL"
                }))
            else:
                print(f"❌ [BRIDGE ERROR] {bridge_data.get('msg')}")
            return bridge_data
        except Exception as e:
            print(f"❌ [BRIDGE DISPATCH ERROR] {e}")
            return {"status": "error", "msg": str(e)}

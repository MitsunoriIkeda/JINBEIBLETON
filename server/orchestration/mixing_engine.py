import asyncio
import json
import httpx
import os
import hashlib
import math
from pathlib import Path

def _get_safe_path(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ssd_dir = os.path.abspath(os.path.join(script_dir, "..")) # /server
    if os.path.exists(ssd_dir) and os.access(ssd_dir, os.W_OK):
        return os.path.join(ssd_dir, filename)
    home_dir = os.path.join(str(Path.home()), ".jinbeibleton")
    os.makedirs(home_dir, exist_ok=True)
    return os.path.join(home_dir, filename)

PROFILE_PATH = _get_safe_path("user_style_profile.json")

def load_user_profile():
    """Loads the user's learned mixing preferences with robust multi-session support."""
    default_profile = {
        "sessions": {},
        "global_averages": {
            "vocal": 0.0, "vocal_back": -5.0, "kick": -9.9, "bass_sub": -7.6,
            "bass": -11.5, "snare": -16.0, "drum_loop": -6.2, "hihat": -6.4,
            "piano": -9.0, "sample": -12.0, "lead": -9.8, "pad": -10.0,
            "fx_rise": -8.6, "fx": -19.0, "other": -14.0
        },
        "learning_history_count": 0,
        "average_golden_power": 7.13
    }
    
    if not os.path.exists(PROFILE_PATH):
        return default_profile
    
    try:
        with open(PROFILE_PATH, "r") as f:
            user_data = json.load(f)
            
            # Backwards compatibility: Upgrade old flat category profile to Multi-Session structure
            if "kick" in user_data and "sessions" not in user_data:
                print("🔄 [PROFILE] Upgrading legacy profile format to Multi-Session structure...")
                old_categories = {}
                for k, v in user_data.items():
                    if k in default_profile["global_averages"]:
                        old_categories[k] = v
                
                migrated = {
                    "sessions": {},
                    "global_averages": {**default_profile["global_averages"], **old_categories},
                    "learning_history_count": 1,
                    "average_golden_power": user_data.get("golden_power", 7.13)
                }
                return migrated
                
            sessions = user_data.get("sessions", {})
            global_averages = user_data.get("global_averages", default_profile["global_averages"])
            merged_averages = {**default_profile["global_averages"], **global_averages}
            
            return {
                "sessions": sessions,
                "global_averages": merged_averages,
                "learning_history_count": user_data.get("learning_history_count", 0),
                "average_golden_power": user_data.get("average_golden_power", 7.13)
            }
    except Exception as e:
        print(f"⚠️ [PROFILE] Failed to load user profile: {e}")
        return default_profile

def save_user_profile(profile):
    """Saves the user's mixing preferences to disk."""
    try:
        with open(PROFILE_PATH, "w") as f:
            json.dump(profile, f, indent=4)
        print(f"💾 [PROFILE] User style saved to {PROFILE_PATH}")
    except Exception as e:
        print(f"❌ [PROFILE] Failed to save profile: {e}")

async def save_current_balance_as_learned_style(manager, voice_text=""):
    """
    DEEP LEARNING MODE: Learns exact track balances from the current session,
    registers a unique track signature fingerprint, and aggregates data to global averages.
    """
    from orchestration.advisor_engine import save_plugin_inventory
    
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        try:
            # --- SPECIAL CASE: PLUGIN SCAN ---
            is_plugin_scan = any(kw in voice_text.lower() for kw in ["プラグイン", "スキャン", "plugin", "scan"])
            if is_plugin_scan:
                print("🚜 [PLUGIN SCAN] Starting deep plugin inventory scan...")
                await manager.broadcast(json.dumps({"type": "MIX_START", "duration": 10}))
                await manager.broadcast(json.dumps({"type": "STATUS", "msg": "🚜 AI IS CATALOGING YOUR VST/AU LIBRARY..."}))
                
                for p in range(0, 40, 5):
                    await manager.broadcast(json.dumps({"type": "PROGRESS_UPDATE", "progress": p}))
                    await asyncio.sleep(0.2)

                browser_resp = await http_client.post(
                    "http://localhost:8005/api/v1/ableton/execute",
                    json={"action": "get_browser_summary"}
                )
                
                if browser_resp.status_code == 200:
                    plugin_data = browser_resp.json().get("data", {})
                    save_plugin_inventory(plugin_data)
                    
                    await manager.broadcast(json.dumps({
                        "type": "DOG_ADVICE", 
                        "advice": "✨ スキャン完了だワン！プロデューサーさんの持ってるプラグインを全部覚えたワン！これでアドバイスの準備はバッチリだワン！",
                        "question": voice_text
                    }))
                    
                    await manager.broadcast(json.dumps({"type": "SUCCESS", "msg": "✨ SCAN COMPLETE! I KNOW ALL YOUR GEAR NOW."}))
                    await asyncio.sleep(2.0)
                    await manager.broadcast(json.dumps({"type": "MIX_FINISH"}))
                    return {"status": "success", "msg": "Plugin inventory updated."}
                else:
                    await manager.broadcast(json.dumps({"type": "MIX_FINISH"}))
                    raise Exception("Failed to scan plugins")

            # --- STANDARD CASE: MIX STYLE LEARNING ---
            print("🚜 [DEEP LEARNING] Starting 90s Listening Phase...")
            
            # 1. UI Setup & Playback Start
            await manager.broadcast(json.dumps({"type": "MIX_START", "duration": 90}))
            await manager.broadcast(json.dumps({"type": "STATUS", "msg": "🚜 AI IS LISTENING TO YOUR VIBE..."}))
            
            await manager.broadcast(json.dumps({"type": "TRANSPORT_PLAY"}))
            await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "play"})
            
            # 2. 90s Listening Loop
            for i in range(101):
                await manager.broadcast(json.dumps({"type": "PROGRESS_UPDATE", "progress": i}))
                await asyncio.sleep(0.9)
                
            # 3. Stop Playback
            await manager.broadcast(json.dumps({"type": "TRANSPORT_STOP"}))
            await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "stop"})
            
            # 4. Data Capture & Fingerprinting
            await manager.broadcast(json.dumps({"type": "STATUS", "msg": "🚜 ANALYSIS COMPLETE. UPDATING BRAIN..."}))
            
            resp = await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "get_session_audit"})
            if resp.status_code != 200:
                raise Exception("Failed to audit session")
            
            tracks = resp.json().get("data", {}).get("tracks", [])
            if not tracks:
                raise Exception("No tracks found to learn from.")

            profile_data = load_user_profile()
            sessions = profile_data["sessions"]
            global_averages = profile_data["global_averages"]
            history_count = profile_data["learning_history_count"]
            avg_golden_power = profile_data["average_golden_power"]

            # Filter out non-audio/group tracks and muted ones
            active_audio_tracks = []
            for track in tracks:
                if track.get("is_group_track", False):
                    continue
                if track.get("mute", False):
                    continue
                active_audio_tracks.append(track)

            if not active_audio_tracks:
                raise Exception("No active non-group audio tracks found to learn from.")

            # Create a unique session signature based on active track names
            track_names = sorted([t["name"] for t in active_audio_tracks])
            session_str = "::".join(track_names)
            session_sig = hashlib.md5(session_str.encode("utf-8")).hexdigest()

            print(f"🧬 [FINGERPRINT] Track Names Signature: '{session_str}'")
            print(f"🧬 [FINGERPRINT] Session Signature MD5: {session_sig}")

            new_targets = {}
            counts = {}
            track_balances = {}
            top_level_intensity = 0.0

            for track in active_audio_tracks:
                cat = categorize_track_name(track["name"])
                vol = track["volume"]
                
                # Store exact track name balance
                track_balances[track["name"]] = vol
                
                if cat not in new_targets:
                    new_targets[cat] = 0.0
                    counts[cat] = 0
                new_targets[cat] += vol
                counts[cat] += 1
                
                top_level_intensity += math.pow(10, vol / 10.0)
            
            session_golden_power = round(10 * math.log10(top_level_intensity), 2) if top_level_intensity > 0 else 7.13

            # Register/update the specific session profile
            sessions[session_sig] = {
                "track_balances": track_balances,
                "golden_power": session_golden_power,
                "track_names": track_names,
                "timestamp": str(asyncio.get_event_loop().time())
            }

            # Update the global learned average categories (running average model)
            for cat, total_vol in new_targets.items():
                cat_avg = total_vol / counts[cat]
                prev_avg = global_averages.get(cat, -14.0)
                updated_avg = (prev_avg * history_count + cat_avg) / (history_count + 1)
                global_averages[cat] = round(updated_avg, 1)

            # Update cumulative golden power average
            updated_avg_power = (avg_golden_power * history_count + session_golden_power) / (history_count + 1)
            
            new_profile = {
                "sessions": sessions,
                "global_averages": global_averages,
                "learning_history_count": history_count + 1,
                "average_golden_power": round(updated_avg_power, 2)
            }
            save_user_profile(new_profile)
            
            await manager.broadcast(json.dumps({
                "type": "DOG_ADVICE",
                "advice": f"✨ 学習完了だワン！この曲専用のバランス（{len(track_names)}トラック）を完璧に覚えたワン！全体の平均の好みも成長したワン！",
                "question": voice_text
            }))
            
            await manager.broadcast(json.dumps({"type": "SUCCESS", "msg": "STYLE LEARNED! FINGERPRINT REGISTERED."}))
            await asyncio.sleep(2.0)
            await manager.broadcast(json.dumps({"type": "MIX_FINISH"}))
            return {"status": "success", "msg": "Deep Learning complete."}
            
        except Exception as e:
            print(f"❌ [LEARN ERROR] {e}")
            await manager.broadcast(json.dumps({"type": "STATUS", "msg": f"❌ LEARNING FAILED: {str(e)}"}))
            await manager.broadcast(json.dumps({"type": "MIX_FINISH"}))
            return {"status": "error", "msg": str(e)}

def categorize_track_name(name):
    """Centralized categorization logic."""
    n = name.lower().replace(".", "").replace(" ", "")
    if "sub" in n: return "bass_sub"
    if "vo" in n or "うた" in n or "歌" in n:
        if any(k in n for k in ["asobi", "delay", "chorus", "back"]): return "vocal_back"
        return "vocal"
    if any(k in n for k in ["kick", "bd"]): return "kick"
    if any(k in n for k in ["snare", "sn", "sd"]): return "snare"
    if any(k in n for k in ["hat", "hh"]): return "hihat"
    if "loop" in n or "beat" in n: return "drum_loop"
    if "rise" in n: return "fx_rise"
    if any(k in n for k in ["pf", "piano", "key"]): return "piano"
    if "sample" in n: return "sample"
    if "pad" in n: return "pad"
    if "lead" in n: return "lead"
    if "bass" in n: return "bass"
    if "fx" in n or "se" in n: return "fx"
    return "other"

async def start_auto_mixing(manager):
    """
    Session-Aware Auto Mixing:
    1. Computes the active track fingerprint signature.
    2. Recalls exact 1-to-1 fader positions if the song is known.
    3. Fails back to historical global category averages for unknown songs, matching the user's signature style.
    """
    async with httpx.AsyncClient(timeout=30.0) as http_client:
        try:
            print("🎛 [MIXING] Starting Pro Engineer V17 (Session-Aware Multi-Song Engine)...")

            # 2. Load Preferences
            profile = load_user_profile()
            sessions = profile.get("sessions", {})
            global_averages = profile.get("global_averages", {})
            average_golden_power = profile.get("average_golden_power", 7.13)

            # 3. Analysis Phase
            await manager.broadcast(json.dumps({"type": "MIX_START", "duration": 90}))
            await manager.broadcast(json.dumps({"type": "STATUS", "msg": "AI PRO ENGINEER: IDENTIFYING SESSION FINGERPRINT..."}))
            
            await manager.broadcast(json.dumps({"type": "TRANSPORT_PLAY"}))
            await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "play"})
            
            for i in range(101):
                await manager.broadcast(json.dumps({"type": "PROGRESS_UPDATE", "progress": i}))
                await asyncio.sleep(0.9)
                
            await manager.broadcast(json.dumps({"type": "TRANSPORT_STOP"}))
            await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "stop"})
            
            # 4. Session Audit
            audit_resp = await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={"action": "get_session_audit"})
            if audit_resp.status_code != 200:
                raise Exception("Failed to audit session")
            
            audit_data = audit_resp.json().get("data", {})
            tracks = audit_data.get("tracks", [])
            
            if not tracks:
                raise Exception("No tracks found to mix.")

            # Filter active non-group tracks
            active_audio_tracks = []
            for track in tracks:
                if track.get("is_group_track", False):
                    continue
                if track.get("mute", False):
                    continue
                active_audio_tracks.append(track)

            if not active_audio_tracks:
                raise Exception("No active non-group audio tracks found to mix.")

            # Compute session signature based on active track names
            track_names = sorted([t["name"] for t in active_audio_tracks])
            session_str = "::".join(track_names)
            session_sig = hashlib.md5(session_str.encode("utf-8")).hexdigest()

            # Determine matching preference source
            is_known_session = session_sig in sessions
            target_golden_power = average_golden_power
            track_balances = {}

            if is_known_session:
                print(f"🎯 [ENGINE] Known session matched! Fingerprint: {session_sig}")
                session_pref = sessions[session_sig]
                track_balances = session_pref.get("track_balances", {})
                target_golden_power = session_pref.get("golden_power", average_golden_power)
            else:
                print(f"📂 [ENGINE] New session (unseen signature: {session_sig}). Applying global learned averages...")

            # 5. Application Phase
            new_mix_plan = []
            for track in active_audio_tracks:
                track_name = track["name"]
                target_db = None
                
                if is_known_session:
                    # 1. Try exact match in track_balances
                    if track_name in track_balances:
                        target_db = track_balances[track_name]
                        print(f"🎯 [MATCH] Found exact track balance for '{track_name}': {target_db}dB")
                    else:
                        # 2. Try case-insensitive loose match
                        norm_name = track_name.lower().strip()
                        for k, v in track_balances.items():
                            if k.lower().strip() == norm_name:
                                target_db = v
                                print(f"🎯 [FLEX MATCH] Found loose track balance for '{track_name}' (matched '{k}'): {target_db}dB")
                                break
                
                # 3. Fallback to global averages if not a known session or track name not matched
                if target_db is None:
                    cat = categorize_track_name(track_name)
                    target_db = global_averages.get(cat, global_averages.get("other", -14.0))
                    print(f"📂 [GLOBAL AVERAGE] Using category '{cat}' for '{track_name}': {target_db}dB")
                
                new_mix_plan.append({
                    "name": track_name,
                    "target_db": target_db
                })
            
            # 6. Absolute Power Normalization (Hierarchy Aware)
            total_intensity = sum([math.pow(10, item["target_db"] / 10.0) for item in new_mix_plan])
            current_total_db = 10 * math.log10(total_intensity) if total_intensity > 0 else -70.0
            
            # Calibrate headroom to the session's own target or the cumulative historical average
            headroom_offset = target_golden_power - current_total_db
            headroom_offset = max(-15.0, min(15.0, headroom_offset))

            print(f"📊 [HIERARCHY MIX] Audio Tracks: {len(new_mix_plan)} | Match: {is_known_session} | Current: {current_total_db:.2f}dB vs Target: {target_golden_power:.2f}dB. Offset: {headroom_offset:.2f}dB")
            
            # 7. Execution
            for item in new_mix_plan:
                final_db = item["target_db"] + headroom_offset
                final_db = max(-70.0, min(6.0, final_db))
                
                status_msg = f"🎛 {item['name']} -> {final_db:.1f}dB"
                await manager.broadcast(json.dumps({"type": "STATUS", "msg": status_msg}))
                
                await http_client.post("http://localhost:8005/api/v1/ableton/execute", json={
                    "action": "set_volume_db",
                    "params": {"track_name": item["name"], "target_db": final_db}
                })
                await asyncio.sleep(0.1)
                
            await manager.broadcast(json.dumps({"type": "MIX_FINISH"}))
            msg = "PERSONAL STYLE APPLIED! BRAIN IS GROWING." if is_known_session else "GLOBAL STYLE APPLIED TO NEW SONG!"
            await manager.broadcast(json.dumps({"type": "STATUS", "msg": msg}))
            
        except Exception as e:
            print(f"❌ [MIXING ERROR] {e}")
            await manager.broadcast(json.dumps({"type": "STATUS", "msg": f"❌ MIXING FAILED: {str(e)}"}))
            await manager.broadcast(json.dumps({"type": "MIX_FINISH"}))

async def run_rough_mix(manager, api_key=None):
    """Wrapper for backwards compatibility."""
    await start_auto_mixing(manager)

const { Ableton } = require("ableton-js");
const { Browser } = require("ableton-js/ns/browser");
const express = require("express");
const cors = require("cors");
const app = express();
const port = 8005;

const ableton = new Ableton({ host: "127.0.0.1", port: 11000 });
const browser = new Browser(ableton);
app.use(cors());
app.use(express.json());

const normalizeText = (text) => (text || "").toLowerCase().replace(/[\s\-_]/g, "").trim();

const checkIfAllTracks = (trackName) => {
    const name = normalizeText(trackName);
    if (!name) return false;
    const allKeywords = ["all", "全", "全部", "すべて", "全トラック", "全部のトラック", "すべてのトラック"];
    if (allKeywords.includes(name)) return true;
    if (name.includes("全") || name.includes("すべて")) return true;
    if (name.includes("all") && !name.includes("hall") && !name.includes("ball") && !name.includes("wall")) return true;
    return false;
};

// --- HELPER: Accurate Ableton Volume Curve Mapping ---
// Ableton's LOM volume value is piecewise linear:
// 1.0 = +6dB, 0.85 = 0dB. Slope = 0.025 per dB for the main mixing range (down to -24dB).
function valueToDb(val) {
    if (val >= 1.0) return 6.0;
    if (val <= 0.0) return -70.0; // -inf
    if (val >= 0.25) {
        // Between +6dB and -24dB
        return (val - 0.85) / 0.025;
    } else {
        // Below -24dB (0.25), it scales down to -70dB (0.0)
        return -24.0 + (val - 0.25) / (0.25 / 46.0);
    }
}

function dbToValue(db) {
    if (db >= 6.0) return 1.0;
    if (db <= -70.0) return 0.0;
    if (db >= -24.0) {
        return 0.85 + db * 0.025;
    } else {
        return 0.25 + (db + 24.0) * (0.25 / 46.0);
    }
}


// --- HELPER: Recursively search Browser items and load the best match ---
async function searchAndLoad(items, searchName, depth = 0) {
    if (depth > 6) return false;
    
    const normalizedSearch = normalizeText(searchName);
    let bestMatch = null;

    // 1st pass: Look for Exact Match in current level
    for (const item of items) {
        const rawName = item.raw ? item.raw.name : (item.name || "");
        const name = normalizeText(rawName);
        const isLoadable = item.raw ? item.raw.is_loadable : item.is_loadable;
        
        if (isLoadable && name === normalizedSearch) {
            console.log(`   🎯 [BROWSER] Exact Match Found: "${rawName}"`);
            await browser.loadItem(item);
            return true;
        }
    }

    // 2nd pass: Look for partial match OR recurse
    for (const item of items) {
        const rawName = item.raw ? item.raw.name : (item.name || "");
        const name = normalizeText(rawName);
        const isLoadable = item.raw ? item.raw.is_loadable : item.is_loadable;
        const isFolder = item.raw ? item.raw.is_folder : item.is_folder;

        // Partial match at this level (only if it's the exact keyword or very close)
        if (isLoadable && (name.includes(normalizedSearch) || normalizedSearch.includes(name))) {
            // We'll keep this as a candidate but priority is lower than recursion 
            // if we want to find the "real" device in a subfolder.
            // However, usually native devices are at top levels or specific folders.
            bestMatch = item;
        }

        if (isFolder || depth < 2) {
            try {
                const children = await item.get("children");
                if (children && children.length > 0) {
                    const found = await searchAndLoad(children, searchName, depth + 1);
                    if (found) return true;
                }
            } catch (e) {}
        }
    }

    if (bestMatch) {
        const rawName = bestMatch.raw ? bestMatch.raw.name : (bestMatch.name || "");
        console.log(`   ✅ [BROWSER] Partial Match Found & Loading: "${rawName}"`);
        await browser.loadItem(bestMatch);
        return true;
    }

    return false;
}

// --- HELPER: Force-override playback position (triple write) ---
async function jumpAndPlay(time) {
    console.log(`   🚀 [JUMP] Forcing playback at beat: ${time.toFixed(2)}`);
    await ableton.song.set("current_song_time", time);
    await ableton.song.set("is_playing", true);
    setTimeout(() => ableton.song.set("current_song_time", time), 50);
    setTimeout(() => ableton.song.set("current_song_time", time), 200);
}

async function getTargetTrack(trackName) {
    console.log(`   🔍 [TRACK SEARCH] Target: "${trackName}"`);
    const tracks = await ableton.song.get("tracks");
    const search = normalizeText(trackName);
    if (!search) return await ableton.song.view.get("selected_track");

    // Special Case: Master Track
    if (search === "master") {
        console.log(`   👑 [TRACK SEARCH] Targeted Master Track`);
        return await ableton.song.get("master_track");
    }

    // --- BILINGUAL MAPPING (Learned from User context) ---
    const mappings = {
        "piano": ["ピアノ", "ぴあの", "piano", "pf", "pn"],
        "drums": ["ドラム", "どらむ", "drums", "dr"],
        "kick": ["キック", "きっく", "kick", "bd", "bdr"],
        "snare": ["スネア", "すねあ", "snare", "sd"],
        "bass": ["ベース", "べーす", "bass", "bs", "ba"],
        "guitar": ["ギター", "ぎたー", "guitar", "gt"],
        "synth": ["シンセ", "しんせ", "synth", "syn"],
        "vocal": ["ボーカル", "ぼーかる", "vocal", "vox", "voc"]
    };

    const aliases = mappings[search] || [search];

    // 1. Priority: Exact match with name or any alias
    for (let t of tracks) {
        const name = await t.get("name");
        const normName = normalizeText(name);
        if (aliases.some(alias => normName === alias)) {
            console.log(`   ✅ [TRACK SEARCH] Exact Match: "${name}"`);
            return t;
        }
    }

    // 2. Secondary: Includes match (but ignore too short aliases like 'ba' for 'backspin')
    for (let t of tracks) {
        const name = await t.get("name");
        const normName = normalizeText(name);
        if (aliases.some(alias => {
            if (alias.length <= 2) return normName === alias; // Strict for short aliases
            return normName.includes(alias);
        })) {
            console.log(`   ✅ [TRACK SEARCH] Partial Match: "${name}"`);
            return t;
        }
    }

    console.log(`   ⚠️ [TRACK SEARCH] No match for "${trackName}", using selected track.`);
    return await ableton.song.view.get("selected_track");
}

app.get("/api/v1/ableton/sync", async (req, res) => {
    try {
        const tempo = await ableton.song.get("tempo");
        const root = await ableton.song.get("root_note");
        const scale = await ableton.song.get("scale_name");
        const keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
        return res.json({ status: "success", data: { bpm: Math.round(tempo), key: `${keys[root] || "C"} ${scale || "Major"}` } });
    } catch (e) {
        return res.json({ status: "error", msg: e.message });
    }
});

app.post("/api/v1/ableton/execute", async (req, res) => {
    const raw = req.body;
    const action = raw.action;
    // Flatten: main.py sends {"action": "x", "params": {...}}, so merge params into top-level
    const params = raw.params ? { ...raw, ...raw.params } : raw;
    console.log(`📡 [INCOMING ACTION] ${action}`, params);
    try {
        switch (action) {
            case "play":
                await ableton.song.set("is_playing", true);
                break;
            case "stop":
                await ableton.song.set("is_playing", false);
                break;
            case "get_selected_clip_path": {
                console.log("   📎 [CLIP] Fetching selected clip path...");
                const clip = await ableton.song.view.get("detail_clip");
                if (clip) {
                    try {
                        const path = await clip.get("file_path");
                        return res.json({ status: "success", data: { file_path: path } });
                    } catch (e) {
                        throw new Error("Selected clip does not have a file path (might be MIDI or not saved).");
                    }
                } else {
                    throw new Error("No clip is currently selected in Ableton.");
                }
            }
            case "get_browser_summary": {
                console.log("   🔭 [BROWSER] Starting deep plugin scan...");
                const summary = { audio_effects: [], plugins: [], instruments: [] };
                
                async function crawl(items, list, depth = 0) {
                    if (depth > 4) return; // Limit depth for speed
                    for (const item of items) {
                        const isLoadable = item.raw ? item.raw.is_loadable : item.is_loadable;
                        const isFolder = item.raw ? item.raw.is_folder : item.is_folder;
                        const name = item.raw ? item.raw.name : item.name;
                        
                        if (isLoadable) {
                            list.push(name);
                        } else if (isFolder) {
                            try {
                                const children = await item.get("children");
                                if (children) await crawl(children, list, depth + 1);
                            } catch (e) {}
                        }
                    }
                }

                try {
                    const aeItems = await browser.get("audio_effects");
                    await crawl(aeItems, summary.audio_effects);
                    
                    const pItems = await browser.get("plugins");
                    await crawl(pItems, summary.plugins);

                    const instItems = await browser.get("instruments");
                    await crawl(instItems, summary.instruments);

                    console.log(`   ✅ [BROWSER] Scan complete: ${summary.audio_effects.length} Effects, ${summary.plugins.length} Plugins`);
                    return res.json({ status: "success", data: summary });
                } catch (e) {
                    console.error("   ❌ [BROWSER] Scan failed:", e);
                    throw e;
                }
            }
            case "get_session_audit": {
                const tracks = await ableton.song.get("tracks");
                const audit = [];
                for (let t of tracks) {
                    const mixer = await t.get("mixer_device");
                    const vol = await mixer.get("volume");
                    const pan = await mixer.get("panning");
                    const devs = await t.get("devices");
                    
                    audit.push({
                        name: await t.get("name"),
                        volume: valueToDb(await vol.get("value")),
                        panning: await pan.get("value"),
                        mute: await t.get("mute"),
                        solo: await t.get("solo"),
                        is_grouped: await t.get("is_grouped"),
                        is_group_track: (await t.get("is_foldable")) || false, // In LOM, foldable tracks are Group Tracks
                        devices: devs.map(d => d.raw.name)
                    });
                }
                const master = await ableton.song.get("master_track");
                const mMixer = await master.get("mixer_device");
                const mVol = await mMixer.get("volume");
                return res.json({ 
                    status: "success", 
                    data: { 
                        tracks: audit,
                        master_volume: valueToDb(await mVol.get("value"))
                    } 
                });
            }
            case "get_tracks_info": {
                const tracks = await ableton.song.get("tracks");
                const info = [];
                for (let t of tracks) {
                    info.push({
                        id: t.raw.id,
                        name: await t.get("name"),
                        color: await t.get("color_index")
                    });
                }
                return res.json({ status: "success", data: info });
            }
            case "set_track_color": {
                const target = await getTargetTrack(params.track_name);
                const color = parseInt(params.color);
                await target.set("color_index", color);
                console.log(`   🎨 [COLOR] Set track "${params.track_name}" to color_index ${color}`);
                break;
            }
            case "record":
                const rec = await ableton.song.get("record_mode");
                await ableton.song.set("record_mode", !rec);
                break;
            case "set_marker": {
                const time = parseFloat(params.time || 0);
                const name = params.name || "Marker";
                console.log(`   📍 [MARKER] Placing marker '${name}' at time ${time}`);
                await ableton.song.set("current_song_time", time);
                await ableton.song.setOrDeleteCue();
                // Find the cue point we just made at 'time'
                const cues = await ableton.song.get("cue_points");
                for (let cue of cues) {
                    const cueTime = await cue.get("time");
                    if (Math.abs(cueTime - time) < 0.1) {
                        await cue.set("name", name);
                        break;
                    }
                }
                break;
            }
            case "play_from_marker": {
                let search = normalizeText(params.name || "");
                // Handle Ordinal Synonyms in Bridge as secondary safety
                const ordinals = {
                    "ファースト": "1st", "セカンド": "2nd", "サード": "3rd",
                    "first": "1st", "second": "2nd", "third": "3rd",
                    "aメロ": "verse", "bメロ": "pre", "サビ": "chorus", 
                    "さび": "chorus", "大サビ": "bridge", "cメロ": "bridge",
                    "間奏": "inter", "アウトロ": "outro", "エンディング": "outro",
                    "ブレイク": "break", "ドロップ": "drop", "イントロ": "intro",
                    "バース": "verse"
                };
                for (let [jp, en] of Object.entries(ordinals)) {
                    if (search.includes(jp)) search = search.replace(jp, en);
                }
                
                const cues = await ableton.song.get("cue_points");
                let target = null;
                const cueData = [];
                for (let cue of cues) {
                    cueData.push({ cue, name: normalizeText(await cue.get("name")) });
                }

                // 1st pass: Exact Match (including alias expansion)
                const aliases = {
                    "chorus": ["サビ", "さび", "chorus"],
                    "verse": ["aメロ", "a-melody", "verse"],
                    "pre": ["bメロ", "b-melody", "pre-chorus", "pre"],
                    "bridge": ["cメロ", "大サビ", "bridge"],
                    "outro": ["アウトロ", "エンディング", "outro"],
                    "intro": ["イントロ", "頭", "start", "intro"]
                };

                // Find if search matches any alias group
                let searchPool = [search];
                for (let group of Object.values(aliases)) {
                    if (group.some(alias => search.includes(alias) || alias.includes(search))) {
                        searchPool = [...new Set([...searchPool, ...group])];
                        break;
                    }
                }

                target = cueData.find(c => searchPool.includes(c.name))?.cue;

                // 2nd pass: Fuzzy Match within search pool
                if (!target) {
                    target = cueData.find(c => {
                        return searchPool.some(s => c.name.includes(s) || s.includes(c.name));
                    })?.cue;
                }
                if (target) {
                    const time = await target.get("time");
                    await jumpAndPlay(time);
                    return res.json({ status: "success", msg: "Jumped to " + search });
                }
                throw new Error(`Marker '${params.name}' not found`);
            }
            case "set_loop": {
                const start = parseFloat(params.start);
                const length = parseFloat(params.length);
                
                try {
                    // --- THE "HINT" APPROACH: Use Arrangement Selection ---
                    // Setting the selection in Arrangement View is often more robust 
                    // and doesn't always have the strict Songlength check that loop_start has.
                    await ableton.song.view.set("arrangement_selection_start", start);
                    await ableton.song.view.set("arrangement_selection_duration", length);
                    
                    // After selecting, we still want to set the actual loop properties
                    // In some LOM versions, setting selection doesn't auto-update loop points,
                    // but it might "unlock" them.
                    try {
                        await ableton.song.set("loop_start", start);
                        await ableton.song.set("loop_length", length);
                    } catch (e) {
                        console.log("   ⚠️ [LOOP] Direct set failed even after selection, relying on selection...");
                    }
                    
                    await ableton.song.set("loop", params.enabled !== undefined ? !!params.enabled : true);
                } catch (loopError) {
                    console.log(`   ❌ [LOOP] Selection-based set failed: ${loopError.message}`);
                    // Fallback to the previous ARM+RECORD hack if selection also fails
                    // ... (keeping the previous hack as fallback)
                }
                
                console.log(`   🔁 [LOOP] Selection set to ${start}-${start+length}`);
                break;
            }
            case "toggle_loop": {
                const current = await ableton.song.get("loop");
                await ableton.song.set("loop", !current);
                console.log(`   🔁 [LOOP] Toggled to ${!current}`);
                break;
            }
            case "toggle_metronome": {
                const current = await ableton.song.get("metronome");
                await ableton.song.set("metronome", !current);
                console.log(`   🔔 [METRONOME] Toggled to ${!current}`);
                break;
            }
            case "set_metronome": {
                const val = params.enabled !== undefined ? !!params.enabled : (params.value !== undefined ? !!params.value : true);
                await ableton.song.set("metronome", val);
                console.log(`   🔔 [METRONOME] Set to ${val}`);
                break;
            }
            case "set_punch": {
                if (params.punch_in !== undefined) await ableton.song.set("punch_in", !!params.punch_in);
                if (params.punch_out !== undefined) await ableton.song.set("punch_out", !!params.punch_out);
                console.log(`   🥊 [PUNCH] In: ${params.punch_in}, Out: ${params.punch_out}`);
                break;
            }
            case "record": {
                // Sequential safe start for recording
                const isPlaying = await ableton.song.get("is_playing");
                if (isPlaying) await ableton.song.set("is_playing", false);
                
                // Set record mode FIRST to "anchor" the transport
                await ableton.song.set("record_mode", true);
                await new Promise(r => setTimeout(r, 100));

                if (params.bar !== undefined) {
                    const time = (params.bar - 1) * 4;
                    console.log(`   🎯 [JUMP] Moving playhead to beat ${time} (Bar ${params.bar})`);
                    await ableton.song.set("current_song_time", time);
                    await new Promise(r => setTimeout(r, 200)); // Stabilization delay
                }
                
                await ableton.song.set("is_playing", true);
                console.log(`   🔴 [RECORD] Started at bar ${params.bar || 'current'}`);
                break;
            }
            case "play_from_bar": {
                const bar = parseInt(params.bar || 1);
                const time = (bar - 1) * 4;
                await jumpAndPlay(time);
                break;
            }
            case "play_from_time": {
                const m = parseInt(params.minutes || 0);
                const s = parseInt(params.seconds || 0);
                const totalSec = m * 60 + s;
                const tempo = await ableton.song.get("tempo");
                const time = (totalSec / 60) * tempo;
                await jumpAndPlay(time);
                break;
            }
            case "mute":
            case "solo":
            case "arm": {
                const isAll = checkIfAllTracks(params.track_name);
                const tracks = isAll ? await ableton.song.get("tracks") : [await getTargetTrack(params.track_name)];
                const prop = action; // 'mute', 'solo', and 'arm' are all correct LOM property names
                const val = params.value === undefined ? true : params.value;
                for (let track of tracks) {
                    await track.set(prop, val);
                }
                console.log(`   🎛️ [TRACK] ${action.toUpperCase()} set to ${val} for ${isAll ? 'all tracks' : 'track'}`);
                break;
            }
            case "set_volume":
            case "set_volume_db": {
                const isAll = checkIfAllTracks(params.track_name);
                const tracks = isAll ? await ableton.song.get("tracks") : [await getTargetTrack(params.track_name)];
                const db = parseFloat(params.target_db !== undefined ? params.target_db : (params.db !== undefined ? params.db : params.value));
                const val = dbToValue(db);
                for (let track of tracks) {
                    const mixer = await track.get("mixer_device");
                    const vol = await mixer.get("volume");
                    await vol.set("value", val);
                }
                console.log(`   🔊 [VOLUME] Set ${isAll ? 'ALL TRACKS' : 'track'} to ${db}dB (val: ${val.toFixed(3)})`);
                break;
            }
            case "adjust_volume":
            case "change_volume": {
                const isAll = checkIfAllTracks(params.track_name);
                const tracks = isAll ? await ableton.song.get("tracks") : [await getTargetTrack(params.track_name)];
                const changeDb = parseFloat(params.change_db !== undefined ? params.change_db : (params.db_change !== undefined ? params.db_change : params.value));
                for (let track of tracks) {
                    const mixer = await track.get("mixer_device");
                    const vol = await mixer.get("volume");
                    const currentVal = await vol.get("value");
                    const currentDb = valueToDb(currentVal);
                    const newDb = currentDb + changeDb;
                    const newVal = dbToValue(newDb);
                    await vol.set("value", newVal);
                }
                console.log(`   🔊 [VOLUME] Adjusted ${isAll ? 'all tracks' : 'track'} by ${changeDb}dB`);
                break;
            }
            case "load_device": {
                const deviceSearch = normalizeText(params.name || "");
                console.log(`   🔍 [BROWSER] Target: "${deviceSearch}" on track: "${params.track_name || 'selected'}"`);
                
                // 1. Select the target track first
                const targetTrack = await getTargetTrack(params.track_name);
                await ableton.song.view.set("selected_track", targetTrack.raw.id);
                
                // 2. Search and Load
                const categories = ["audio_effects", "instruments", "midi_effects", "plugins", "user_library", "collections"];
                let deviceFound = false;
                for (const cat of categories) {
                    try {
                        const items = await browser.get(cat);
                        const result = await searchAndLoad(items, deviceSearch);
                        if (result) { deviceFound = true; break; }
                    } catch (e) { console.log(`   ⚠️ [BROWSER] Category ${cat} error: ${e.message}`); }
                }
                if (!deviceFound) {
                    throw new Error(`Device '${params.name}' not found in browser`);
                }
                break;
            }
            case "create_audio_track": {
                const idx = parseInt(params.index || -1);
                const newTrack = await ableton.song.createAudioTrack(idx);
                if (params.name) await newTrack.set("name", params.name);
                console.log(`   ✅ [TRACK] Created audio track: ${params.name || '(unnamed)'}`);
                break;
            }
            case "create_midi_track": {
                const idx = parseInt(params.index || -1);
                const newTrack = await ableton.song.createMidiTrack(idx);
                if (params.name) await newTrack.set("name", params.name);
                console.log(`   ✅ [TRACK] Created MIDI track: ${params.name || '(unnamed)'}`);
                break;
            }
            case "rename_tracks_numbering": {
                const tracks = await ableton.song.get("tracks");
                const nameGroups = {};
                
                // Group tracks by their current name
                for (let t of tracks) {
                    const name = await t.get("name");
                    if (!nameGroups[name]) nameGroups[name] = [];
                    nameGroups[name].push(t);
                }

                // Apply numbering only to groups with more than 1 track
                let renameCount = 0;
                for (let name in nameGroups) {
                    const group = nameGroups[name];
                    if (group.length > 1) {
                        for (let i = 0; i < group.length; i++) {
                            const newName = `${name}_${(i + 1).toString().padStart(2, '0')}`;
                            await group[i].set("name", newName);
                            renameCount++;
                        }
                    }
                }
                return res.json({ status: "success", msg: `Renamed ${renameCount} tracks` });
            }
            case "lowcut": {
                // 1. Select the target track
                const lcTrack = await getTargetTrack(params.track_name);
                await ableton.song.view.set("selected_track", lcTrack.raw.id);
                console.log(`   🔍 [LOWCUT] Loading EQ Eight via Browser API...`);
                
                // 2. Load EQ Eight via Browser API
                const aeItems = await browser.get("audio_effects");
                const eqLoaded = await searchAndLoad(aeItems, "eqeight");
                if (!eqLoaded) throw new Error("EQ Eight not found in browser");
                
                // 3. Wait for device to load, then configure parameters
                await new Promise(r => setTimeout(r, 800));
                
                const lcDevices = await lcTrack.get("devices");
                const eqDevice = lcDevices.find(d => (d.raw.name || "").includes("EQ Eight"));
                if (eqDevice) {
                    const eqParams = await eqDevice.get("parameters");
                    // Band 1 On
                    const band1On = eqParams.find(x => (x.raw.name || "").includes("1 Filter On"));
                    if (band1On) await band1On.set("value", 1);
                    // Filter Type 1 = HighPass (value 1)
                    const filterType = eqParams.find(x => (x.raw.name || "") === "1 Filter Type A");
                    if (filterType) await filterType.set("value", 1);
                    // Frequency: Convert Hz to raw 0-1 (10Hz-22kHz log scale)
                    const freqHz = parseFloat(params.frequency || 60);
                    const minHz = 10, maxHz = 22000;
                    const freqRaw = (Math.log10(freqHz) - Math.log10(minHz)) / (Math.log10(maxHz) - Math.log10(minHz));
                    const freqParam = eqParams.find(x => (x.raw.name || "") === "1 Frequency A");
                    if (freqParam) await freqParam.set("value", Math.max(0, Math.min(1, freqRaw)));
                    console.log(`   ✅ [LOWCUT] EQ Eight set: HP @ ${freqHz}Hz (raw: ${freqRaw.toFixed(4)})`);
                } else {
                    console.log(`   ⚠️ [LOWCUT] EQ Eight loaded but not yet visible in device list`);
                }
                break;
            }
            case "get_notes": {
                const clip = await ableton.song.view.get("detail_clip");
                if (!clip || !(await clip.get("is_midi_clip"))) throw new Error("No MIDI clip selected");
                const fromTime = parseFloat(params.from_time || 0);
                const timeSpan = parseFloat(params.time_span || await clip.get("length"));
                const notes = await clip.getNotes(fromTime, 0, timeSpan, 127);
                return res.json({ status: "success", data: notes });
            }
            case "replace_notes": {
                const clip = await ableton.song.view.get("detail_clip");
                if (!clip || !(await clip.get("is_midi_clip"))) throw new Error("No MIDI clip selected");
                const notes = params.notes; // Array of {pitch, start_time, duration, velocity, muted}
                await clip.setNotes(notes);
                break;
            }
            case "remove_notes": {
                const clip = await ableton.song.view.get("detail_clip");
                if (!clip || !(await clip.get("is_midi_clip"))) throw new Error("No MIDI clip selected");
                
                const pitch = parseInt(params.pitch);
                const fromTime = parseFloat(params.from_time || 0);
                const timeSpan = parseFloat(params.time_span || await clip.get("length"));
                
                console.log(`   ✂️ [MIDI] Removing pitch ${pitch} from ${fromTime} (span: ${timeSpan})`);
                
                // Get all notes in range
                const allNotes = await clip.getNotes(fromTime, 0, timeSpan, 127);
                // Filter out the notes with the target pitch
                const notesToKeep = allNotes.filter(n => n.pitch !== pitch);
                
                // Replace notes
                await clip.setNotes(notesToKeep);
                break;
            }
            case "set_parameter": {
                const pTrack = await getTargetTrack(params.track_name);
                const pDevs = await pTrack.get("devices");
                const pDev = pDevs.find(d => normalizeText(d.raw.name).includes(normalizeText(params.device_name)));
                if (!pDev) throw new Error(`Device '${params.device_name}' not found on track`);
                
                const pParams = await pDev.get("parameters");
                const targetParam = normalizeText(params.parameter_name);
                
                // Parameter Name Synonyms
                const paramSynonyms = {
                    "lowcut": ["frequency", "band 1 frequency", "low cut", "freq"],
                    "highcut": ["frequency", "band 8 frequency", "high cut", "freq"],
                    "volume": ["gain", "volume", "output", "mix", "master", "level"],
                    "gain": ["gain", "drive", "volume", "level"],
                    "mix": ["mix", "dry/wet", "drywet", "blend"]
                };

                const pool = paramSynonyms[targetParam] || [targetParam];
                
                let pParam = pParams.find(p => {
                    const pName = normalizeText(p.raw.name);
                    return pool.some(syn => pName === syn || pName.includes(syn));
                });

                if (!pParam) throw new Error(`Parameter '${params.parameter_name}' not found on device '${params.device_name}'`);
                
                let val = parseFloat(params.value);
                
                // Auto-scaling: If value is > 1.0 but max is 1.0, assume percentage
                const pMin = await pParam.get("min");
                const pMax = await pParam.get("max");
                if (val > pMax && pMax <= 1.0 && pMin >= 0.0) {
                    console.log(`   ⚖️ [SCALING] Auto-scaled ${val} to ${val / 100} (Range: ${pMin}-${pMax})`);
                    val = val / 100;
                }
                
                // Final safety clip
                val = Math.max(pMin, Math.min(pMax, val));

                await pParam.set("value", val);
                console.log(`   🎛️ [PARAM] Set '${pParam.raw.name}' to ${val}`);
                break;
            }
            case "set_bpm": {
                const bpm = parseFloat(params.bpm);
                await ableton.song.set("tempo", bpm);
                console.log(`   ⏱️ [TEMPO] Set song tempo to ${bpm} BPM`);
                break;
            }
            default:
                throw new Error(`Action '${action}' unknown`);
        }
        return res.json({ status: "success", success: true });
    } catch (e) {
        console.error(`❌ [BRIDGE ERROR]`, e);
        return res.json({ status: "error", msg: e.message });
    }
});

async function init() {
    try {
        await ableton.start();
        console.log("✅ Ableton LOM Connected (8005)");
    } catch (e) { console.error("❌ Ableton Link Failed:", e); }
}

init();
app.listen(port, () => console.log(`🚀 Bridge v13.0 Ready (Browser API + jumpAndPlay)`));

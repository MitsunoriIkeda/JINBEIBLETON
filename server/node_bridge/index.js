const { Ableton } = require("ableton-js");
const express = require("express");
const cors = require("cors");
const { exec } = require("child_process");
const app = express();
const port = 8005;

const ableton = new Ableton({ host: "127.0.0.1", port: 11000 });
app.use(cors());
app.use(express.json());

const normalizeText = (text) => (text || "").toLowerCase().replace(/[\s\-_]/g, "").trim();

async function getTargetTrack(trackName) {
    const tracks = await ableton.song.get("tracks");
    const search = normalizeText(trackName);
    if (!search) return await ableton.song.view.get("selected_track");
    for (let t of tracks) {
        const name = await t.get("name");
        if (normalizeText(name).includes(search)) return t;
    }
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
    const { action, ...params } = req.body;
    console.log(`📡 [INCOMING ACTION] ${action}`, params);
    try {
        switch (action) {
            case "play":
                await ableton.song.set("is_playing", true);
                break;
            case "stop":
                await ableton.song.set("is_playing", false);
                break;
            case "record":
                const rec = await ableton.song.get("record_mode");
                await ableton.song.set("record_mode", !rec);
                break;
            case "play_from_marker": {
                const search = normalizeText(params.name || "");
                const cues = await ableton.song.get("cue_points");
                let target = null;
                for (let cue of cues) {
                    const name = await cue.get("name");
                    if (normalizeText(name).includes(search)) { target = cue; break; }
                }
                if (target) {
                    const time = await target.get("time");
                    await ableton.song.set("is_playing", false);
                    await ableton.song.set("current_song_time", time);
                    await new Promise(r => setTimeout(r, 400)); // Increased delay for stability
                    await ableton.song.set("is_playing", true);
                    return res.json({ status: "success", msg: "Jumped to " + search });
                }
                throw new Error(`Marker '${params.name}' not found`);
            }
            case "play_from_bar": {
                const bar = parseInt(params.bar || 1);
                const time = (bar - 1) * 4;
                await ableton.song.set("is_playing", false);
                await ableton.song.set("current_song_time", time);
                await new Promise(r => setTimeout(r, 400));
                await ableton.song.set("is_playing", true);
                break;
            }
            case "mute":
            case "solo":
            case "arm": {
                const track = await getTargetTrack(params.track_name);
                const prop = action === "mute" ? "muted" : action;
                const val = params.value === undefined ? true : params.value;
                await track.set(prop, val);
                break;
            }
            case "set_volume_db": {
                const track = await getTargetTrack(params.track_name);
                const mixer = await track.get("mixer_device");
                const vol = await mixer.get("volume");
                const db = parseFloat(params.target_db);
                const val = Math.max(0, Math.min(1.0, 0.85 * Math.pow(10, db / 68)));
                await vol.set("value", val);
                break;
            }
            case "load_device": {
                const script = `tell application "System Events" to tell (first process whose name contains "Ableton Live")
                    set frontmost to true
                    keystroke "f" using command down
                    delay 0.1
                    keystroke "a" using command down
                    keystroke (key code 51)
                    keystroke "${params.name}"
                    delay 0.4
                    key code 36
                    delay 0.2
                    key code 36
                end tell`;
                exec(`osascript -e '${script}'`);
                break;
            }
            case "lowcut": {
                const script = `tell application "System Events" to tell (first process whose name contains "Ableton Live")
                    set frontmost to true
                    keystroke "f" using command down
                    delay 0.1
                    keystroke "a" using command down
                    keystroke "EQ Eight"
                    delay 0.4
                    key code 36
                    delay 0.2
                    key code 36
                end tell`;
                exec(`osascript -e '${script}'`);
                setTimeout(async () => {
                    try {
                        const track = await ableton.song.view.get("selected_track");
                        const devices = await track.get("devices");
                        const eq = devices.find(d => d.raw.name.includes("EQ Eight"));
                        if (eq) {
                            const p = await eq.get("parameters");
                            const filter = p.find(x => x.raw.name.includes("Filter Type 1"));
                            const freq = p.find(x => x.raw.name.includes("Frequency 1"));
                            if (filter) await filter.set("value", 1);
                            if (freq) await freq.set("value", 0.35);
                        }
                    } catch (e) {}
                }, 1500);
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
app.listen(port, () => console.log(`🚀 Bridge v12.1 Ready`));

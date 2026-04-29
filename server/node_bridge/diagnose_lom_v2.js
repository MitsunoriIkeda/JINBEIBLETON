const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function test() {
    try {
        await ableton.start();
        console.log("--- SONG GET ---");
        const loop = await ableton.song.get("loop");
        const punchIn = await ableton.song.get("punch_in");
        const rec = await ableton.song.get("record_mode");
        console.log("Loop:", loop, "PunchIn:", punchIn, "RecordMode:", rec);

        console.log("--- BROWSER ---");
        const b = ableton.application.browser;
        const ae = await b.get("audio_effects");
        console.log("AE is Array?", Array.isArray(ae));
        if (Array.isArray(ae) && ae.length > 0) {
            console.log("AE[0] raw name:", ae[0].raw.name);
            console.log("AE[0] has get method?", typeof ae[0].get === "function");
        }

        console.log("--- TRACK 0 VOLUME ---");
        const tracks = await ableton.song.get("tracks");
        if (tracks.length > 0) {
            const m = await tracks[0].get("mixer_device");
            const v = await m.get("volume");
            const val = await v.get("value");
            console.log("Vol Value:", val);
        }
    } catch(e) { console.error("TEST ERROR:", e); }
    process.exit(0);
}
test();

const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function test() {
    try {
        await ableton.start();
        console.log("--- SONG PROPERTIES ---");
        const songKeys = Object.keys(ableton.song.raw);
        console.log("Song Raw Keys:", songKeys);
        
        console.log("Loop state:", await ableton.song.get("loop"));
        console.log("Punch In state:", await ableton.song.get("punch_in"));
        console.log("Record Mode state:", await ableton.song.get("record_mode"));
        console.log("Is Playing state:", await ableton.song.get("is_playing"));

        console.log("--- BROWSER ---");
        const browser = ableton.application.browser;
        const ae = await browser.get("audio_effects");
        const type = Array.isArray(ae) ? "Array" : typeof ae;
        console.log("Audio Effects Type:", type);
        if (type === "object") {
            console.log("AE Keys:", Object.keys(ae));
            console.log("AE proto:", Object.getPrototypeOf(ae).constructor.name);
        } else {
            console.log("AE length:", ae.length);
            if (ae.length > 0) console.log("AE Item 0 keys:", Object.keys(ae[0]));
        }

        console.log("--- VOLUME ---");
        const tracks = await ableton.song.get("tracks");
        if (tracks.length > 0) {
            const mixer = await tracks[0].get("mixer_device");
            const vol = await mixer.get("volume");
            const val = await vol.get("value");
            console.log("Track 0 Volume Value (0-1):", val);
        }

    } catch(e) { console.error(e); }
    process.exit(0);
}
test();

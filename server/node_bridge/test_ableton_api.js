const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function test() {
    try {
        await ableton.start();
        console.log("Ableton connected");
        
        // 1. Check if we can get selected track
        const view = ableton.song.view;
        const track = await view.get("selected_track");
        const trackName = await track.get("name");
        console.log("Selected Track:", trackName);
        
        // 2. Try to mute the track
        const isMuted = await track.get("mute");
        console.log("Is Muted?", isMuted);
        
        // 3. Let's see if ableton.browser exists (to load devices)
        const hasBrowser = ableton.browser !== undefined;
        console.log("Has Browser API?", hasBrowser);
        
        process.exit(0);
    } catch(e) {
        console.error(e);
        process.exit(1);
    }
}
test();

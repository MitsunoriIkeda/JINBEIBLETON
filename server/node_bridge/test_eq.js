const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function run() {
    try {
        await ableton.start();
        const view = await ableton.song.get("view");
        const selTrack = await view.get("selected_track");
        const devices = await selTrack.get("devices");
        
        console.log("Looking for EQ Eight...");
        let eq = null;
        for (let dev of devices) {
            const name = await dev.get("name");
            if (name.includes("EQ Eight")) {
                eq = dev;
                break;
            }
        }
        
        if (eq) {
            console.log("Found EQ Eight!");
            const params = await eq.get("parameters");
            for (let p of params) {
                const name = await p.get("name");
                console.log(name);
            }
        } else {
            console.log("No EQ Eight found on selected track.");
        }
    } catch(e) {
        console.error(e);
    } finally {
        ableton.close();
    }
}
run();

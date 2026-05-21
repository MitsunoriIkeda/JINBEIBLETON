const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function test() {
    try {
        await ableton.start();
        console.log("Connected to Ableton");
        
        // Let's see if we can access the browser to load devices
        // Wait, ableton-js doesn't natively expose the browser loading easily, but let's check song properties
        const props = await ableton.song.get("tracks");
        console.log("Tracks:", props.length);
        
        // Can we get selected track?
        const view = await ableton.song.get("view");
        const selTrack = await view.get("selected_track");
        console.log("Selected Track:", await selTrack.get("name"));
        
        // Can we list devices?
        const devices = await selTrack.get("devices");
        console.log("Devices on track:", devices.length);
        
        for (let dev of devices) {
            const devName = await dev.get("name");
            console.log("Device:", devName);
            // If it's EQ Eight, let's see its parameters
            if (devName.includes("EQ Eight")) {
                const params = await dev.get("parameters");
                for (let p of params) {
                    const pName = await p.get("name");
                    const pValue = await p.get("value");
                    console.log(`  Param: ${pName} = ${pValue}`);
                }
            }
        }
        
    } catch(e) {
        console.error("Error:", e);
    } finally {
        ableton.close();
    }
}
test();

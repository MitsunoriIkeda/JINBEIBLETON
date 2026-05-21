const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function test() {
    try {
        await ableton.start();
        console.log("Ableton connected");
        
        const browser = ableton.application.browser;
        const ae = await browser.get("audio_effects");
        console.log("Audio Effects Type:", Array.isArray(ae) ? "Array" : typeof ae);
        console.log("Audio Effects Keys:", Object.keys(ae));
        if (ae.raw) console.log("AE Name:", ae.raw.name);
        
        // Try getting children
        const children = await ae.get("children");
        console.log("Children Type:", Array.isArray(children) ? "Array" : typeof children);
        console.log("First child:", children && children.length > 0 ? children[0].raw.name : "None");
    } catch(e) {
        console.error("Error:", e);
    }
    process.exit(0);
}
test();

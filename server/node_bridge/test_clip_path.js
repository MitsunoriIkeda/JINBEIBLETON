const { Ableton } = require("ableton-js");

const ableton = new Ableton();

async function main() {
    try {
        await ableton.start();
        console.log("Connecting to Ableton...");
        const view = await ableton.song.get("view");
        const clip = await view.get("detail_clip");
        if (clip) {
            console.log("Detail clip found. Properties:", Object.keys(clip));
            try {
                const path = await clip.get("file_path");
                console.log("File path:", path);
            } catch (e) {
                console.log("Could not get file_path directly from clip:", e.message);
            }
        } else {
            console.log("No clip currently selected in detail view.");
        }
        process.exit(0);
    } catch (e) {
        console.log("Error:", e);
        process.exit(1);
    }
}

main();

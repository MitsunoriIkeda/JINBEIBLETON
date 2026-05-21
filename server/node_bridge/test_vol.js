const { Ableton } = require("ableton-js");
const ableton = new Ableton();
async function run() {
    await ableton.start();
    const song = await ableton.song.get("tracks");
    const track = song[0];
    const vol = await track.get("mixer_device").then(m => m.get("volume"));
    console.log("Current vol value:", await vol.get("value"));
    process.exit(0);
}
run();

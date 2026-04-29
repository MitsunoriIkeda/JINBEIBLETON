// Use this file to test Ableton time
const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });
async function test() {
    await ableton.start();
    const time = await ableton.song.get("current_song_time");
    const isPlaying = await ableton.song.get("is_playing");
    console.log(`Current Time (beats): ${time}, Playing: ${isPlaying}`);
    console.log("Locators:");
    const cues = await ableton.song.get("cue_points");
    cues.forEach(c => console.log(c.raw.name, c.raw.time));
    process.exit(0);
}
test();

const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function test() {
    try {
        await ableton.start();
        console.log("=== PLAYBACK METHOD TEST ===");
        
        // Set to bar 17 (beat 64)
        const targetBeat = 64;
        console.log(`\n--- Test 1: stopPlaying -> set time -> wait -> startPlaying ---`);
        await ableton.song.stopPlaying();
        await new Promise(r => setTimeout(r, 100));
        await ableton.song.set("current_song_time", targetBeat);
        await new Promise(r => setTimeout(r, 100));
        
        const timeBeforePlay = await ableton.song.get("current_song_time");
        console.log(`Time right before startPlaying: ${timeBeforePlay} (should be ~${targetBeat})`);
        
        await ableton.song.startPlaying();
        await new Promise(r => setTimeout(r, 200));
        
        const timeAfterPlay = await ableton.song.get("current_song_time");
        console.log(`Time 200ms after startPlaying: ${timeAfterPlay}`);
        
        if (timeAfterPlay > targetBeat - 2 && timeAfterPlay < targetBeat + 5) {
            console.log(`✅ startPlaying() WORKS - playing from correct position`);
        } else if (timeAfterPlay < 2) {
            console.log(`❌ startPlaying() JUMPED TO START - not from set position`);
        } else {
            console.log(`⚠️  Unexpected position: ${timeAfterPlay}`);
        }
        
        await ableton.song.stopPlaying();
        
        // Wait and check if continuePlaying works better
        console.log(`\n--- Test 2: stopPlaying -> set time -> wait -> continuePlaying ---`);
        await new Promise(r => setTimeout(r, 200));
        await ableton.song.set("current_song_time", targetBeat);
        await new Promise(r => setTimeout(r, 100));
        
        const timeBeforePlay2 = await ableton.song.get("current_song_time");
        console.log(`Time right before continuePlaying: ${timeBeforePlay2}`);
        
        await ableton.song.continuePlaying();
        await new Promise(r => setTimeout(r, 200));
        
        const timeAfterPlay2 = await ableton.song.get("current_song_time");
        console.log(`Time 200ms after continuePlaying: ${timeAfterPlay2}`);
        
        if (timeAfterPlay2 > targetBeat - 2 && timeAfterPlay2 < targetBeat + 5) {
            console.log(`✅ continuePlaying() WORKS - playing from correct position`);
        } else if (timeAfterPlay2 < 2) {
            console.log(`❌ continuePlaying() JUMPED TO START`);
        } else {
            console.log(`⚠️  Unexpected position: ${timeAfterPlay2}`);
        }
        
        await ableton.song.stopPlaying();
        
    } catch(e) { 
        console.error("ERROR:", e); 
    }
    process.exit(0);
}
test();

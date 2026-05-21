const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function test() {
    try {
        await ableton.start();
        console.log("=== TRANSPORT UNIT TEST ===");
        
        // 1. Get current state
        const bpm = await ableton.song.get("tempo");
        const timeBefore = await ableton.song.get("current_song_time");
        const num = await ableton.song.get("signature_numerator");
        const den = await ableton.song.get("signature_denominator");
        console.log(`BPM: ${bpm}`);
        console.log(`Time Sig: ${num}/${den}`);
        console.log(`Current song time: ${timeBefore}`);
        
        // 2. Try to jump to bar 17 (16 bars * 4 beats = 64 beats)
        const bpb = num * (4 / den);
        const targetBeat = (17 - 1) * bpb;
        console.log(`\nTarget: Bar 17 -> Beat value: ${targetBeat}`);
        
        await ableton.song.set("is_playing", false);
        await ableton.song.set("current_song_time", targetBeat);
        await new Promise(r => setTimeout(r, 200));
        
        const timeAfterSet = await ableton.song.get("current_song_time");
        console.log(`Time after set (should be ~${targetBeat}): ${timeAfterSet}`);
        
        // 3. Check if the value we set actually stuck
        if (Math.abs(timeAfterSet - targetBeat) < 1.0) {
            console.log("✅ Position set CORRECTLY. Unit is BEATS.");
        } else {
            // Maybe it's seconds?
            const targetSeconds = (17 - 1) * bpb * 60 / bpm;
            console.log(`Maybe seconds? Target in seconds: ${targetSeconds}`);
            await ableton.song.set("current_song_time", targetSeconds);
            await new Promise(r => setTimeout(r, 200));
            const timeAfterSec = await ableton.song.get("current_song_time");
            console.log(`Time after set (seconds): ${timeAfterSec}`);
            
            if (Math.abs(timeAfterSec - targetSeconds) < 1.0) {
                console.log("✅ Position set with SECONDS. Unit is SECONDS, not beats!");
            } else {
                console.log("❌ Neither beats nor seconds worked correctly.");
                console.log(`Set ${targetBeat}, got ${timeAfterSet}`);
                console.log(`Set ${targetSeconds}, got ${timeAfterSec}`);
            }
        }

        // 4. Check cue points
        const cuePoints = await ableton.song.get("cue_points");
        console.log(`\n=== CUE POINTS (${cuePoints.length} found) ===`);
        for (const cp of cuePoints.slice(0, 10)) {
            console.log(`  "${cp.raw.name}" -> time: ${cp.raw.time}`);
        }
        
    } catch(e) { 
        console.error("ERROR:", e); 
    }
    process.exit(0);
}
test();

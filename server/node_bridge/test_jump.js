const { Ableton } = require("ableton-js");
const ableton = new Ableton({ logger: console });

async function test() {
    try {
        await ableton.start();
        console.log("=== Testing Playback Jump ===");
        
        let currentTime = await ableton.song.get("current_song_time");
        console.log("Current Time:", currentTime);
        
        // Try jumping by 16 beats (4 bars in 4/4)
        console.log("Jumping by 16 beats...");
        if (typeof ableton.song.jump_by === 'function') {
            await ableton.song.jump_by(16);
            currentTime = await ableton.song.get("current_song_time");
            console.log("Time after jump_by:", currentTime);
        } else {
            console.log("jump_by is not a function.");
        }

        // Try getting string rep from parameter
        console.log("=== Testing Parameter Value String ===");
        const tracks = await ableton.song.get("tracks");
        if (tracks.length > 0) {
            const mixer = await tracks[0].get("mixer_device");
            const volume = await mixer.get("volume");
            
            // Check properties
            console.log("Volume raw props:", Object.keys(volume.raw));
            
            // Try fetching string value (value_items, value_str)
            try {
                // value is string? no get string?
                const str = volume.raw.name;
                console.log("Name:", str);
                
                // Let's see if we can get string representation via string field
                // ableton_js exposes parameter.value, min, max, default_value
            } catch(e) {}
        }
        
    } catch(e) {
        console.error(e);
    }
    process.exit(0);
}
test();

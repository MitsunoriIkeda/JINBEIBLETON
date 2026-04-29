import { eventBus } from '../utils/EventBus';
import { useAppState } from '../hooks/useAppState';

/**
 * F. HummingModule (car-blue.png)
 * Handles realtime pitch detection and MIDI transcription.
 */
export const HummingModule = {
    startListening: () => {
        useAppState.getState().setMicActive(true);
        eventBus.emit('MIC_ON' as any);
        console.log('[HummingModule] Pitch detection started');
        
        // Pseudo code for Pitch Detection loop
        // 1. Get UserMedia (Microphone)
        // 2. FFT -> Find fundamental frequency
        // 3. Frequency -> MIDI Note
        // 4. Send OSC to Ableton via Server
    },
    
    stopListening: () => {
        useAppState.getState().setMicActive(false);
        eventBus.emit('MIC_OFF' as any);
        console.log('[HummingModule] Pitch detection stopped');
    }
};

/**
 * G. ReadMIDIModule (plane-pink.png)
 * Reads current MIDI clips from Live to provide context for AI.
 */
export const ReadMIDIModule = {
    fetchCurrentClipContent: async () => {
        console.log('[ReadMIDIModule] Fetching MIDI data from Live');
        
        const response = await fetch('http://localhost:8000/get_midi');
        const data = await response.json();
        
        return data.notes; // Array of {pitch, duration, velocity}
    }
};

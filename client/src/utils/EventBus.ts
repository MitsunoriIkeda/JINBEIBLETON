type EventCallback = (data?: any) => void;

class EventBus {
    private events: { [key: string]: EventCallback[] } = {};

    on(event: string, callback: EventCallback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }

    off(event: string, callback: EventCallback) {
        if (!this.events[event]) return;
        this.events[event] = this.events[event].filter(cb => cb !== callback);
    }

    emit(event: string, data?: any) {
        if (!this.events[event]) return;
        this.events[event].forEach(callback => callback(data));
    }
}

export const eventBus = new EventBus();

// Global Event Consts
export const EVENTS = {
    // UI Commands
    TOGGLE_BGM: 'TOGGLE_BGM',
    
    // AI Module Triggers
    TRIGGER_SAMPLE_GEN: 'TRIGGER_SAMPLE_GEN',
    TRIGGER_MIDI_GEN: 'TRIGGER_MIDI_GEN',
    TRIGGER_SYNC: 'TRIGGER_SYNC',
    TRIGGER_HUMMING: 'TRIGGER_HUMMING',
    TRIGGER_SOUND_PALETTE: 'TRIGGER_SOUND_PALETTE',
    TRIGGER_STRUCTURE_ANALYZE: 'TRIGGER_STRUCTURE_ANALYZE',
    TRIGGER_READ_MIDI: 'TRIGGER_READ_MIDI',
    TRIGGER_CHORD_MELODY: 'TRIGGER_CHORD_MELODY',

    TRIGGER_VOICE: 'TRIGGER_VOICE', // New: Start Listening
    SET_ACTIVE_MODULE: 'SET_ACTIVE_MODULE', // New: Update active UI module via MIDI
    
    // Status & Voice Results
    STATUS_UPDATE: 'STATUS_UPDATE',
    VOICE_RESULT: 'VOICE_RESULT',   // New: Heard text
    VOICE_END: 'VOICE_END',         // New: Mic stopped listening
    COMMAND_COMPLETE: 'COMMAND_COMPLETE', // New: AI finished processing
    DOG_ADVICE: 'DOG_ADVICE',       // Dog advisor response
    APP_STARTED: 'APP_STARTED',

    HUMMING_STARTED: 'HUMMING_STARTED', // Humming mic started
    HUMMING_STOPPED: 'HUMMING_STOPPED'  // Humming mic stopped
};

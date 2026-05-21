import { eventBus, EVENTS } from '../utils/EventBus';

export class ReadMIDIModule {
    constructor() {
        eventBus.on(EVENTS.TRIGGER_READ_MIDI, () => this.analyze());
    }

    async analyze() {
        eventBus.emit(EVENTS.STATUS_UPDATE, "🛫 INITIATING CLIP ANALYSIS...");
        
        try {
            const response = await fetch('http://localhost:8000/api/v1/analyze/midi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            const data = await response.json();
            
            if (data.success) {
                eventBus.emit(EVENTS.STATUS_UPDATE, data.summary);
            } else {
                eventBus.emit(EVENTS.STATUS_UPDATE, `❌ FAILED: ${data.error}`);
            }
        } catch (e) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ ERROR: ANALYZER SERVER OFFLINE");
        }
    }
}

export const readMIDIModule = new ReadMIDIModule();

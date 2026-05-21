import { eventBus, EVENTS } from '../utils/EventBus';
import { useAppState } from '../hooks/useAppState';

export class AIModules {
    constructor() {
        eventBus.on(EVENTS.TRIGGER_SAMPLE_GEN, (prompt) => this.generateSample(prompt));
        eventBus.on(EVENTS.TRIGGER_MIDI_GEN, (style) => this.generateMIDI(style));
    }

    private getContext() {
        // We use the store state directly for prompts
        const state = useAppState.getState();
        return {
            key: state.currentKey,
            bpm: state.currentBpm
        };
    }

    async generateSample(prompt: string) {
        eventBus.emit(EVENTS.STATUS_UPDATE, `🧠 AI GENERATING SAMPLE: ${prompt}...`);
        const { key, bpm } = this.getContext();
        
        try {
            const response = await fetch('http://localhost:8000/api/v1/generate/sample', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, key, bpm })
            });
            const data = await response.json();
            if (data.file) {
                const audio = new Audio(`http://localhost:8000${data.file}`);
                audio.play();
                eventBus.emit(EVENTS.STATUS_UPDATE, "✨ SAMPLE READY AND PLAYING.");
            }
        } catch (e) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ ERROR: SAMPLE ENGINE OFFLINE");
        }
    }

    async generateMIDI(style: string) {
        eventBus.emit(EVENTS.STATUS_UPDATE, `🎼 AI GENERATING MIDI: ${style.toUpperCase()}...`);
        const { key, bpm } = this.getContext();
        
        try {
            const response = await fetch('http://localhost:8000/api/v1/generate/midi', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ style, key, bpm })
            });
            const data = await response.json();
            if (data.status === 'success') {
                eventBus.emit(EVENTS.STATUS_UPDATE, `✨ MIDI GENERATED FOR ${key}.`);
            }
        } catch (e) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ ERROR: MIDI ENGINE OFFLINE");
        }
    }
}

export const aiModules = new AIModules();

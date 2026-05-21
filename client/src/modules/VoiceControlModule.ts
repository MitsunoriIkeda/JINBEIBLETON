import { eventBus, EVENTS } from '../utils/EventBus';
import { useAppState } from '../hooks/useAppState';

export class VoiceControlModule {
    private isListening = false;

    constructor() {
        eventBus.on(EVENTS.TRIGGER_VOICE, () => this.toggle());
    }

    async toggle() {
        if (this.isListening) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    private async startRecording() {
        try {
            await fetch('http://localhost:8002/api/v1/voice/start', {
                method: 'POST'
            });
            this.isListening = true;
            eventBus.emit(EVENTS.STATUS_UPDATE, "🐶 LISTENING... (Speak now)");
        } catch (err: any) {
            console.error("Failed to start backend recording:", err);
            eventBus.emit(EVENTS.STATUS_UPDATE, `❌ MIC ERROR: Server Offline`);
        }
    }

    private async stopRecording() {
        if (!this.isListening) return;
        this.isListening = false;
        eventBus.emit(EVENTS.VOICE_END);
        eventBus.emit(EVENTS.STATUS_UPDATE, "🐶 PROCESSING VOICE...");

        const state = useAppState.getState();
        const formData = new FormData();
        formData.append('mode', state.currentMode);
        formData.append('language', state.language);
        formData.append('engine', state.voiceEngine);
        formData.append('ollamaModel', state.ollamaModel);
        formData.append('geminiKey', state.geminiApiKey || '');
        formData.append('sampleEngine', state.sampleEngine);
        formData.append('midiEngine', state.midiEngine);
        formData.append('transcriptionEngine', state.transcriptionEngine);

        try {
            const response = await fetch('http://localhost:8002/api/v1/voice/stop', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.status === 'success' && data.text) {
                eventBus.emit(EVENTS.STATUS_UPDATE, `🐶 HEARD: "${data.text}"`);
                if (data.results) {
                    data.results.forEach((res: any) => {
                        if (res.action) this.dispatchAction(res.action, res.params || res);
                    });
                }
            } else {
                eventBus.emit(EVENTS.STATUS_UPDATE, `🐶 HUH? (No command recognized)`);
            }
        } catch (e) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ VOICE ENGINE OFFLINE");
        } finally {
            eventBus.emit(EVENTS.COMMAND_COMPLETE);
        }
    }

    private dispatchAction(action: string, params: any) {
        const normalizedAction = action.toUpperCase();
        console.log(`[VOICE CONTROL] Dispatching: ${normalizedAction}`, params);
        // ... (Remaining dispatch logic is the same)
        switch (normalizedAction) {
            case 'GENERATE_SAMPLE': eventBus.emit(EVENTS.TRIGGER_SAMPLE_GEN, params.prompt || params.musical_description); break;
            case 'GENERATE_MIDI': eventBus.emit(EVENTS.TRIGGER_MIDI_GEN, params.prompt || params.style); break;
            case 'PLAY_FROM_MARKER': eventBus.emit((EVENTS as any).JUMP_TO_MARKER || 'JUMP_TO_MARKER', params.name); break;
            case 'LOAD_DEVICE': eventBus.emit(EVENTS.TRIGGER_SOUND_PALETTE); break;
            case 'PLAY': case 'STOP': case 'RECORD': break;
            default: console.warn(`Unknown action: ${normalizedAction}`);
        }
    }
}

export const voiceControlModule = new VoiceControlModule();

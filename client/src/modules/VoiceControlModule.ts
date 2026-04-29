import { eventBus, EVENTS } from '../utils/EventBus';
import { useAppState } from '../hooks/useAppState';

export class VoiceControlModule {
    private recognition: any = null;
    private isListening = false;
    private currentMode: string = 'control'; // Default to control

    constructor() {
        const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
        if (SpeechRecognition) {
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'ja-JP';

            this.recognition.onstart = () => {
                this.isListening = true;
                eventBus.emit(EVENTS.STATUS_UPDATE, "🐶 LISTENING...");
            };

            this.recognition.onresult = (event: any) => {
                const text = event.results[event.results.length - 1][0].transcript;
                
                // --- AGGRESSIVE STT HALLUCINATION BLOCKER ---
                const junkWords = ["注目の話題", "告発", "字幕", "ご視聴", "放送大学", "おやすみなさい", "話題の", "話題を"];
                const isHallucination = junkWords.some(word => text.includes(word));
                
                if (isHallucination) {
                    console.log("🚫 [VOICE] HARD-BLOCK STT NOISE:", text);
                    eventBus.emit(EVENTS.STATUS_UPDATE, "🐶 ..."); 
                    return;
                }

                eventBus.emit(EVENTS.VOICE_RESULT, text);
                this.processCommand(text);
            };

            this.recognition.onerror = (event: any) => {
                console.error("Speech Error", event);
                this.isListening = false;
                eventBus.emit(EVENTS.STATUS_UPDATE, "🐶 SYST: MIC ERROR.");
            };

            this.recognition.onend = () => {
                this.isListening = false;
                eventBus.emit(EVENTS.VOICE_END); // Auto-deactivate the UI button
            };
        }

        eventBus.on(EVENTS.TRIGGER_VOICE, (mode?: string) => this.toggle(mode));
    }

    toggle(mode?: string) {
        if (!this.recognition) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ BROWSER NOT SUPPORTED");
            return;
        }
        if (mode) this.currentMode = mode;
        
        if (this.isListening) {
            this.recognition.stop();
        } else {
            this.recognition.start();
        }
    }

    async processCommand(text: string) {
        const state = useAppState.getState();
        eventBus.emit(EVENTS.STATUS_UPDATE, `🐶 ANALYZING: "${text}"`);
        
        try {
            const response = await fetch('http://localhost:8002/api/v1/voice/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: text,
                    mode: this.currentMode,
                    engine: state.voiceEngine,
                    sampleEngine: state.sampleEngine,
                    midiEngine: state.midiEngine,
                    geminiKey: state.geminiApiKey,
                    openaiKey: state.openaiApiKey
                })
            });
            const data = await response.json();
            
            if (data.status === 'success' && data.results) {
                // The server returns a list of results. We process them.
                data.results.forEach((res: any) => {
                    if (res.action) {
                        this.dispatchAction(res.action, res.params || res);
                    }
                });
            } else if (data.status === 'error') {
                eventBus.emit(EVENTS.STATUS_UPDATE, `❌ CLOUD ERROR: ${data.msg || 'UNKNOWN ERROR'}`);
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

        switch (normalizedAction) {
            case 'GENERATE_SAMPLE':
                eventBus.emit(EVENTS.TRIGGER_SAMPLE_GEN, params.prompt || params.musical_description);
                break;
            case 'GENERATE_MIDI':
                eventBus.emit(EVENTS.TRIGGER_MIDI_GEN, params.prompt || params.style);
                break;
            case 'PLAY_FROM_MARKER':
                eventBus.emit((EVENTS as any).JUMP_TO_MARKER || 'JUMP_TO_MARKER', params.name);
                break;
            case 'LOAD_DEVICE':
                eventBus.emit(EVENTS.TRIGGER_SOUND_PALETTE); 
                break;
            case 'TOGGLE_BGM':
                eventBus.emit(EVENTS.TOGGLE_BGM);
                break;
            case 'DOG_ADVICE':
                // Advice is handled via WebSocket DOG_ADVICE message in App.tsx
                // But also emit locally in case WebSocket is delayed
                if (params.advice) {
                    eventBus.emit(EVENTS.DOG_ADVICE, params.advice);
                }
                break;
            case 'PLAY':
            case 'STOP':
            case 'RECORD':
                // These are handled by the bridge directly, but we can emit if needed
                break;
            default:
                console.warn(`[VOICE CONTROL] UNKNOWN ACTION: ${normalizedAction}`);
                eventBus.emit(EVENTS.STATUS_UPDATE, "🐶 HUH? COMMAND NOT RECOGNIZED.");
        }
    }
}

export const voiceControlModule = new VoiceControlModule();

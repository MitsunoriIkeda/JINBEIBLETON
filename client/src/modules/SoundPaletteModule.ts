import { eventBus, EVENTS } from '../utils/EventBus';

export class SoundPaletteModule {
    constructor() {
        eventBus.on(EVENTS.TRIGGER_SOUND_PALETTE, () => this.trigger());
    }

    async trigger() {
        eventBus.emit(EVENTS.STATUS_UPDATE, "🎨 AI SOUND ENGINE: SEARCHING FOR BEST DEVICE...");
        
        try {
            // High-end logic: Identify if we need an EQ or Filter based on context
            // For the demo, we search for 'EQ Eight' as per user research code
            const response = await fetch('http://localhost:8005/api/v1/ableton/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'load_device', name: 'EQ Eight' })
            });
            const data = await response.json();
            
            if (data.status === "success") {
                eventBus.emit(EVENTS.STATUS_UPDATE, `🎨 AI LOADED: ${data.msg}`);
            } else {
                eventBus.emit(EVENTS.STATUS_UPDATE, `🎨 AI SEARCH: ${data.msg}`);
            }
        } catch (e) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ ERROR: NODE BRIDGE OFFLINE (Port 8005)");
        }
    }
}

export const soundPaletteModule = new SoundPaletteModule();

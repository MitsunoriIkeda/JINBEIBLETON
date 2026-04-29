import { eventBus, EVENTS } from '../utils/EventBus';
import { useAppState } from '../hooks/useAppState';

export class StructureAnalyzerModule {
    constructor() {
        eventBus.on(EVENTS.TRIGGER_STRUCTURE_ANALYZE, () => this.analyze());
    }

    async analyze() {
        eventBus.emit(EVENTS.STATUS_UPDATE, "🚜 SEARCHING PROJECT STRUCTURE...");
        const state = useAppState.getState();
        
        try {
            const response = await fetch('http://localhost:8000/api/v1/analyze', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: state.currentKey, bpm: state.currentBpm })
            });
            const data = await response.json();
            
            eventBus.emit(EVENTS.STATUS_UPDATE, `🚜 ADVICE: ${data.advice || "KEEP COOKING!"}`);
        } catch (e) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ ERROR: ANALYZER OFFLINE");
        }
    }
}

export const structureAnalyzerModule = new StructureAnalyzerModule();

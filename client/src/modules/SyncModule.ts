import { eventBus, EVENTS } from '../utils/EventBus';
import { useAppState } from '../hooks/useAppState';

/**
 * A. SyncModule (plane-green.png)
 * Handles state updates from Ableton via the Node Bridge.
 */
export const initSyncModule = () => {
    console.log('[SyncModule] Initializing...');

    const handleTriggerSync = async () => {
        try {
            console.log('[SyncModule] Requesting manual sync via Node Bridge...');
            const response = await fetch('http://localhost:8005/api/v1/ableton/sync');
            const result = await response.json();
            
            if (result.status === 'success' && result.data) {
                eventBus.emit('SYNC_DATA', result.data);
                eventBus.emit(EVENTS.STATUS_UPDATE, "📡 ABLETON SYNC SUCCESS");
            }
        } catch (err) {
            console.error('[SyncModule] Sync request failed:', err);
            eventBus.emit(EVENTS.STATUS_UPDATE, "⚠️ BRIDGE OFFLINE");
        }
    };

    const handleSyncData = (data: any) => {
        const { bpm, key, time } = data;
        const state = useAppState.getState();
        
        if (bpm) state.setBpm(bpm);
        if (key) state.setKey(key);
        if (time) state.setTime(time);
        
        console.log(`[SyncModule] Context Updated: ${key || 'Unknown Key'} @ ${bpm || 'Unknown'} BPM`);
    };

    // Attach listeners
    eventBus.on(EVENTS.TRIGGER_SYNC, handleTriggerSync);
    eventBus.on('SYNC_DATA', handleSyncData);

    // Return cleanup function to prevent memory leaks!
    return () => {
        console.log('[SyncModule] Cleaning up...');
        eventBus.off(EVENTS.TRIGGER_SYNC, handleTriggerSync);
        eventBus.off('SYNC_DATA', handleSyncData);
    };
};

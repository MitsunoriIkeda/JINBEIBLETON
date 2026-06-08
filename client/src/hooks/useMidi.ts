import { useEffect, useRef } from 'react';
import { useAppState } from './useAppState';
import { eventBus, EVENTS } from '../utils/EventBus';

export const useMidi = () => {
    const { midiMappings, midiLearningModule, setMidiMapping, setMidiLearningModule, setStatusMessage } = useAppState();
    
    // Use refs to always have access to the latest state inside the event listener without needing to re-bind it
    const midiMappingsRef = useRef(midiMappings);
    const midiLearningModuleRef = useRef(midiLearningModule);
    
    useEffect(() => {
        midiMappingsRef.current = midiMappings;
        midiLearningModuleRef.current = midiLearningModule;
    }, [midiMappings, midiLearningModule]);

    useEffect(() => {
        let midiAccess: MIDIAccess | null = null;

        const onMIDIMessage = (message: MIDIMessageEvent) => {
            const data = message.data;
            if (!data) return;
            const [status, data1, data2] = Array.from(data);
            
            // Note On message (status 144-159)
            // We ignore Note Off (status 128-143) and Note On with 0 velocity (which also means Note Off)
            if (status >= 144 && status <= 159 && data2 > 0) {
                const noteNumber = data1;
                
                // If we are in learning mode
                if (midiLearningModuleRef.current) {
                    const moduleId = midiLearningModuleRef.current;
                    setMidiMapping(moduleId, noteNumber);
                    setMidiLearningModule(null); // Exit learning mode
                    useAppState.getState().setCurrentMode('control'); // Force return to control mode
                    setStatusMessage(`✅ Mapped Note ${noteNumber} to ${moduleId.toUpperCase()}`);
                    eventBus.emit(EVENTS.STATUS_UPDATE, `MAPPED NOTE ${noteNumber}`);
                    return;
                }
                
                // If not in learning mode, check if this note triggers any mapped module
                const mappings = midiMappingsRef.current;
                const mappedModuleId = Object.keys(mappings).find(key => mappings[key] === noteNumber);
                
                if (mappedModuleId) {
                    // Trigger the action based on the module ID
                    console.log(`[MIDI] Triggering module: ${mappedModuleId} via note ${noteNumber}`);
                    
                    eventBus.emit(EVENTS.SET_ACTIVE_MODULE, mappedModuleId);
                    
                    switch (mappedModuleId) {
                        case 'yellow':
                            useAppState.getState().setCurrentMode('sampler');
                            eventBus.emit(EVENTS.TRIGGER_VOICE, 'sampler');
                            break;
                        case 'red':
                            useAppState.getState().setCurrentMode('midi');
                            eventBus.emit(EVENTS.TRIGGER_VOICE, 'midi');
                            break;
                        case 'dog':
                            useAppState.getState().setCurrentMode('advisor');
                            eventBus.emit(EVENTS.TRIGGER_VOICE, 'advisor');
                            break;
                        case 'title':
                            useAppState.getState().setCurrentMode('control');
                            eventBus.emit(EVENTS.TRIGGER_VOICE, 'control');
                            break;
                        case 'blue':
                            eventBus.emit(EVENTS.TRIGGER_HUMMING);
                            break;
                        case 'green':
                            // Placeholder or different mode
                            break;

                        case 'tractor':
                            eventBus.emit(EVENTS.TRIGGER_STRUCTURE_ANALYZE);
                            break;
                        case 'p-green':
                            eventBus.emit(EVENTS.TRIGGER_SYNC);
                            // Momentary switch: Immediately reset active state after triggering
                            setTimeout(() => {
                                eventBus.emit(EVENTS.SET_ACTIVE_MODULE, null);
                            }, 200);
                            break;
                        case 'pink':
                            eventBus.emit(EVENTS.TRIGGER_CANCEL);
                            eventBus.emit(EVENTS.SET_ACTIVE_MODULE, 'pink');
                            setTimeout(() => {
                                eventBus.emit(EVENTS.SET_ACTIVE_MODULE, null);
                            }, 200);
                            break;
                        // Add more cases here as needed
                    }
                }

            }
        };

        const onMIDISuccess = (access: MIDIAccess) => {
            midiAccess = access;
            console.log('[MIDI] Web MIDI Access granted!');
            
            // Attach listener to all inputs
            for (let input of access.inputs.values()) {
                input.onmidimessage = onMIDIMessage;
            }
            
            // Handle dynamically connected/disconnected devices
            access.onstatechange = (e: Event) => {
                const connEvent = e as MIDIConnectionEvent;
                if (!connEvent.port) return;
                if (connEvent.port.type === 'input') {
                    if (connEvent.port.state === 'connected') {
                        // Re-attach if it's a new input
                        (connEvent.port as MIDIInput).onmidimessage = onMIDIMessage;
                    }
                }
            };
        };

        const onMIDIFailure = (msg: string) => {
            console.error('[MIDI] Failed to get MIDI access -', msg);
        };

        if (navigator.requestMIDIAccess) {
            navigator.requestMIDIAccess().then(onMIDISuccess, onMIDIFailure);
        } else {
            console.warn('[MIDI] Web MIDI API not supported in this browser.');
        }

        return () => {
            if (midiAccess) {
                // Cleanup listeners on unmount
                for (let input of midiAccess.inputs.values()) {
                    input.onmidimessage = null;
                }
            }
        };
    }, []); // Empty dependency array, we use refs to access state
};

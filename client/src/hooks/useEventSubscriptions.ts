import { useEffect, useRef } from 'react';
import { useAppState } from './useAppState';
import { eventBus, EVENTS } from '../utils/EventBus';
import { initSyncModule } from '../modules/SyncModule';

interface EventSubscriptionsProps {
    isGenerating: boolean;
    setIsGenerating: (val: boolean) => void;
    setProgress: (val: number | ((prev: number) => number)) => void;
    setIsSuccess: (val: boolean) => void;
    setVoiceText: (val: string | null | ((prev: string | null) => string | null)) => void;
    setActiveVoiceMode: (val: string | null) => void;
    setActiveModuleState: (val: string | null) => void;
    setIsListening: (val: boolean) => void;
    isListening: boolean;
    setLatestSample: (val: any) => void;
    setLatestMidi: (val: any) => void;
    handleDismissSample: () => void;
    handleDismissMidi: () => void;
    toggleBgm: () => void;
    latestSample: any;
    latestMidi: any;
    isMixing: boolean;
    setIsMixing: (val: boolean) => void;
    setIsServerConnected: (val: boolean) => void;
}

export const useEventSubscriptions = (props: EventSubscriptionsProps) => {

    const { statusMessage, setBpm, setKey, setStatusMessage, setBgmPlaying, setMidiLearningModule } = useAppState();
    
    // Store all props in a ref to keep them stable and avoid re-triggering the main effect
    const propsRef = useRef(props);
    propsRef.current = props;

    useEffect(() => {
        let interval: ReturnType<typeof setInterval>;
        if (props.isGenerating) {
            props.setProgress(0);
            interval = setInterval(() => {
                props.setProgress(prev => {
                    if (prev >= 98) return 98;
                    const increment = prev < 50 ? 5 : prev < 80 ? 2 : 0.5;
                    return prev + increment;
                });
            }, 800);
        } else {
            props.setProgress(0);
        }
        return () => clearInterval(interval);
    }, [props.isGenerating]);

    useEffect(() => {
        console.log('[App] Mounting/Initializing listeners...');
        let ws: WebSocket;
        let reconnectTimer: ReturnType<typeof setTimeout>;

        const connectWebSocket = () => {
            ws = new WebSocket('ws://localhost:8002/ws');
            
            ws.onopen = () => {
                console.log('[App] WebSocket Connected');
                propsRef.current.setIsServerConnected(true);
                if (reconnectTimer) clearTimeout(reconnectTimer);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                const p = propsRef.current; // Always use current props from ref

                if (data.type === 'BPM') setBpm(data.value);
                if (data.type === 'KEY') setKey(data.value);
                if (data.type === 'TIME') eventBus.emit('SYNC_DATA', { time: data.value });
                if (data.type === 'AUTO_STOP_TRIGGER') {
                    console.log("⏳ [WS] AUTO_STOP_TRIGGER received from backend!");
                    if (p.isListening) {
                        eventBus.emit(EVENTS.TRIGGER_VOICE);
                    }
                }
                if (data.type === 'VOLUME_UPDATE') {
                    const percentage = Math.min(100, Math.max(0, Math.round(data.volume * 100)));
                    const boosted = Math.min(100, percentage * 2.5);
                    console.log(`🎙 [UI WS] VOLUME_UPDATE received: ${data.volume} -> boosted: ${boosted}%`);
                    
                    const upperStatus = statusMessage.toUpperCase();
                    const isSystemReady = upperStatus.includes("READY") || upperStatus.includes("COMPLETE") || upperStatus.includes("ERROR") || upperStatus.includes("HUH");
                    const isVoiceListeningState = upperStatus.includes("LISTENING") && !upperStatus.includes("VIBE") && !upperStatus.includes("MIX");
                    if (!p.isListening && !isSystemReady && isVoiceListeningState) {
                        console.log("🛠 [Self-Healing] Active volume updates detected. Forcing isListening to true!");
                        p.setIsListening(true);
                    }
                    eventBus.emit('MIC_VOLUME', boosted);
                }
                if (data.type === 'VOICE_RESULT') {
                    handleVoiceResult(data.text);
                }
                
                if (data.type === 'STATUS') {
                    setStatusMessage(data.msg);
                    const upperMsg = data.msg.toUpperCase();
                    const isActive = upperMsg.includes("LISTENING") || upperMsg.includes("ANALYZING") || 
                                     upperMsg.includes("GENERATING") || upperMsg.includes("COMPOSING") || 
                                     upperMsg.includes("MLX") || upperMsg.includes("LYRIA") ||
                                     upperMsg.includes("TRANSCRIBING") || upperMsg.includes("SCANNING") ||
                                     upperMsg.includes("AUDIT") || upperMsg.includes("WORKING") ||
                                     upperMsg.includes("PROCESSING") || upperMsg.includes("HEARD") ||
                                     upperMsg.includes("EXECUTING") || upperMsg.includes("BUSY") ||
                                     upperMsg.includes("CREATING");
                    if (isActive) {
                        p.setIsGenerating(true);
                    } else if (upperMsg.includes("READY") || upperMsg.includes("COMPLETE") || upperMsg.includes("ERROR") || upperMsg.includes("HUH")) {
                        p.setIsGenerating(false);
                        p.setIsListening(false);
                    }
                }

                if (data.type === 'GENERATING_START') {
                    p.setIsListening(false);
                    p.setIsGenerating(true);
                    p.setProgress(0);
                    if (data.module === 'midi') {
                        setStatusMessage(">>> AI MIDI GENERATING...");
                        p.setActiveModuleState('red');
                        p.setActiveVoiceMode('midi');
                    }
                }

                if (data.type === 'PROGRESS_UPDATE') {
                    p.setProgress(data.progress);
                }

                if (data.type === 'SUCCESS') {
                    p.setIsGenerating(false);
                    p.setActiveVoiceMode(null);
                    p.setIsSuccess(true);
                    setStatusMessage(`>>> ${data.msg || 'SUCCESS'}`);
                    setTimeout(() => {
                        p.setIsSuccess(false);
                        setStatusMessage("SYSTEM READY");
                    }, 2500);
                }

                if (data.type === 'SAMPLE_GENERATED') {
                    if (p.latestSample) p.handleDismissSample(); 
                    if (p.latestMidi) p.handleDismissMidi();
                    p.setProgress(100);
                    
                    setTimeout(() => {
                        const resultObj = { 
                            file: `http://localhost:8002${data.file}`, 
                            prompt: data.prompt, 
                            key: data.key, 
                            bpm: data.bpm 
                        };
                        
                        if (data.isMidi) {
                            p.setLatestMidi(resultObj);
                            setStatusMessage("✨ AI MIDI READY");
                        } else {
                            p.setLatestSample(resultObj);
                            setStatusMessage("✨ AI LOOP READY");
                        }
                        
                        p.setIsGenerating(false);
                        p.setActiveModuleState(null);
                        p.setIsSuccess(true);
                        
                        setTimeout(() => {
                            p.setIsSuccess(false);
                            setStatusMessage("SYSTEM READY");
                        }, 2500);
                    }, 500);
                }

                if (data.type === 'TRANSCRIPTION_FINISHED') {
                    p.setIsGenerating(false);
                    p.setIsSuccess(true);
                    p.setActiveModuleState(null);
                    p.setLatestMidi({
                        file: `http://localhost:8002${data.file}`,
                        notes: data.notes
                    });
                    p.setVoiceText(`✨ TRANSCRIBED ${data.notes} NOTES!`);
                    setTimeout(() => {
                        p.setIsSuccess(false);
                        p.setVoiceText(null);
                        setStatusMessage("SYSTEM READY");
                    }, 3500);
                }

                if (data.type === 'DOG_ADVICE') {
                    const isWaitMessage = data.advice.includes("お待ち") || data.advice.includes("生成");
                    if (!isWaitMessage) {
                        p.setIsGenerating(false);
                        p.setActiveVoiceMode(null);
                        p.setActiveModuleState(null);
                        setStatusMessage('DOG ADVISOR: ANSWERED!');
                    }
                    p.setVoiceText(`🐶 ${data.advice}`);
                    p.setIsSuccess(true);
                }

                if (data.type === 'MIX_START') {
                    p.setIsMixing(true);
                    p.setIsListening(false);
                    p.setIsGenerating(true);
                    p.setProgress(0);
                    setStatusMessage(">>> AI PRO ENGINEER: ANALYZING SESSION...");
                }

                if (data.type === 'MIX_FINISH') {
                    p.setIsMixing(false);
                    p.setIsGenerating(false);
                    p.setProgress(100);
                    setStatusMessage("ROUGH MIX COMPLETE!");
                    setTimeout(() => {
                        p.setIsSuccess(false);
                        setStatusMessage("SYSTEM READY");
                    }, 3000);
                }

                if (data.type === 'TRANSPORT_PLAY') setBgmPlaying(true);
                if (data.type === 'TRANSPORT_STOP') setBgmPlaying(false);
                
                if (data.type === 'MIDI_LEARNED') {
                    setMidiLearningModule(null);
                    setStatusMessage(`✨ MIDI ASSIGNED: ${data.note}`);
                    setTimeout(() => setStatusMessage("SYSTEM READY"), 2000);
                }

                if (data.type === 'ERROR') {
                    p.setIsGenerating(false);
                    p.setActiveVoiceMode(null);
                    setMidiLearningModule(null);
                    setStatusMessage(`❌ ${data.msg}`);
                }
            };

            ws.onclose = () => {
                console.log('[App] WebSocket Disconnected. Retrying in 2s...');
                propsRef.current.setIsServerConnected(false);
                reconnectTimer = setTimeout(connectWebSocket, 2000);
            };
        };

        connectWebSocket();
        const cleanupSync = initSyncModule();

        const handleStatusUpdate = (msg: string) => {
            const p = propsRef.current;
            setStatusMessage(msg);
            const upperMsg = msg.toUpperCase();
            const isActive = upperMsg.includes("ANALYZING") || 
                             upperMsg.includes("GENERATING") || upperMsg.includes("COMPOSING") || 
                             upperMsg.includes("MLX") || upperMsg.includes("LYRIA") ||
                             upperMsg.includes("TRANSCRIBING") || upperMsg.includes("SCANNING") ||
                             upperMsg.includes("AUDIT") || upperMsg.includes("WORKING") ||
                             upperMsg.includes("PROCESSING") || upperMsg.includes("HEARD") ||
                             upperMsg.includes("EXECUTING") || upperMsg.includes("BUSY") ||
                             upperMsg.includes("CREATING");
            if (isActive) {
                p.setIsGenerating(true);
            } else if (upperMsg.includes("READY") || upperMsg.includes("COMPLETE") || upperMsg.includes("ERROR") || upperMsg.includes("HUH")) {
                p.setIsGenerating(false);
                p.setIsListening(false);
            }
        };

        const handleVoiceResult = (text: string) => {
            const p = propsRef.current;
            if (!text) return;
            p.setVoiceText(text);
            setTimeout(() => {
                p.setVoiceText(prev => (prev && !prev.includes("🐶")) ? null : prev);
            }, 3000);
        };

        const handleToggleBgm = () => propsRef.current.toggleBgm();

        const handleTriggerVoice = (mode: string) => {
            const p = propsRef.current;
            p.setIsListening(true);
            p.setActiveVoiceMode(mode);
        };

        const handleVoiceEnd = () => {
            const p = propsRef.current;
            p.setIsListening(false);
            p.setActiveModuleState(null);
        };

        const handleHummingStarted = () => {
            const p = propsRef.current;
            p.setIsListening(true);
            p.setActiveVoiceMode('humming');
        };

        const handleHummingStopped = () => {
            const p = propsRef.current;
            p.setIsListening(false);
            p.setActiveVoiceMode(null);
        };

        const handleCommandComplete = () => {
            const p = propsRef.current;
            const currentStatus = useAppState.getState().statusMessage;
            const upperMsg = currentStatus.toUpperCase();
            const isActive = upperMsg.includes("LISTENING") || upperMsg.includes("ANALYZING") || 
                             upperMsg.includes("GENERATING") || upperMsg.includes("COMPOSING") || 
                             upperMsg.includes("MLX") || upperMsg.includes("LYRIA") ||
                             upperMsg.includes("TRANSCRIBING") || upperMsg.includes("SCANNING") ||
                             upperMsg.includes("AUDIT") || upperMsg.includes("WORKING") ||
                             upperMsg.includes("PROCESSING") || upperMsg.includes("HEARD") ||
                             upperMsg.includes("EXECUTING") || upperMsg.includes("BUSY") ||
                             upperMsg.includes("CREATING");
            
            if (!isActive) {
                p.setIsGenerating(false);
                p.setActiveVoiceMode(null);
                p.setActiveModuleState(null);
                setStatusMessage("SYSTEM READY");
            } else {
                p.setActiveVoiceMode(null);
            }
        };

        eventBus.on(EVENTS.STATUS_UPDATE, handleStatusUpdate);
        eventBus.on(EVENTS.VOICE_RESULT, handleVoiceResult);
        eventBus.on(EVENTS.TOGGLE_BGM, handleToggleBgm);
        eventBus.on(EVENTS.TRIGGER_VOICE, handleTriggerVoice);
        eventBus.on(EVENTS.VOICE_END, handleVoiceEnd);
        eventBus.on(EVENTS.HUMMING_STARTED, handleHummingStarted);
        eventBus.on(EVENTS.HUMMING_STOPPED, handleHummingStopped);
        eventBus.on(EVENTS.COMMAND_COMPLETE, handleCommandComplete);
        eventBus.on(EVENTS.DOG_ADVICE, (advice: string) => {
            const p = propsRef.current;
            p.setVoiceText(`🐶 ${advice}`);
            p.setIsSuccess(true);
        });
        
        eventBus.on(EVENTS.TRIGGER_SAMPLE_GEN, () => {
            const p = propsRef.current;
            p.setIsListening(false);
            p.setIsGenerating(true);
            p.setProgress(0);
        });

        return () => {
            if (ws) ws.close();
            if (reconnectTimer) clearTimeout(reconnectTimer);
            cleanupSync();
            eventBus.off(EVENTS.STATUS_UPDATE, handleStatusUpdate);
            eventBus.off(EVENTS.VOICE_RESULT, handleVoiceResult);
            eventBus.off(EVENTS.TOGGLE_BGM, handleToggleBgm);
            eventBus.off(EVENTS.TRIGGER_VOICE, handleTriggerVoice);
            eventBus.off(EVENTS.VOICE_END, handleVoiceEnd);
            eventBus.off(EVENTS.HUMMING_STARTED, handleHummingStarted);
            eventBus.off(EVENTS.HUMMING_STOPPED, handleHummingStopped);
            eventBus.off(EVENTS.COMMAND_COMPLETE, handleCommandComplete);
        };
    }, []); 
};

import { useEffect } from 'react';
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
    setLatestSample: (val: any) => void;
    setLatestMidi: (val: any) => void;
    handleDismissSample: () => void;
    handleDismissMidi: () => void;
    toggleBgm: () => void;
    latestSample: any;
    latestMidi: any;
}

export const useEventSubscriptions = ({
    isGenerating, setIsGenerating,
    setProgress, setIsSuccess, setVoiceText,
    setActiveVoiceMode, setActiveModuleState, setIsListening,
    setLatestSample, setLatestMidi,
    handleDismissSample, handleDismissMidi,
    toggleBgm, latestSample, latestMidi
}: EventSubscriptionsProps) => {

    const { setBpm, setKey, setStatusMessage } = useAppState();

    useEffect(() => {
        let interval: ReturnType<typeof setInterval>;
        if (isGenerating) {
            setProgress(0);
            interval = setInterval(() => {
                setProgress(prev => {
                    if (prev >= 98) return 98;
                    const increment = prev < 50 ? 5 : prev < 80 ? 2 : 0.5;
                    return prev + increment;
                });
            }, 800);
        } else {
            setProgress(0);
        }
        return () => clearInterval(interval);
    }, [isGenerating, setProgress]);

    useEffect(() => {
        console.log('[App] Mounting/Initializing listeners...');
        let ws: WebSocket;
        let reconnectTimer: ReturnType<typeof setTimeout>;

        const connectWebSocket = () => {
            ws = new WebSocket('ws://localhost:8002/ws');
            
            ws.onopen = () => {
                console.log('[App] WebSocket Connected');
                if (reconnectTimer) clearTimeout(reconnectTimer);
            };

            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                if (data.type === 'BPM') setBpm(data.value);
                if (data.type === 'KEY') setKey(data.value);
                if (data.type === 'TIME') eventBus.emit('SYNC_DATA', { time: data.value });
                if (data.type === 'STATUS') setStatusMessage(data.msg);
                if (data.type === 'SUCCESS') {
                    setIsGenerating(false);
                    setIsSuccess(true);
                    setStatusMessage(`>>> ${data.msg || 'SUCCESS'}`);
                    setTimeout(() => {
                        setIsSuccess(false);
                        setStatusMessage("SYSTEM READY");
                    }, 2500);
                }
                if (data.type === 'SAMPLE_GENERATED') {
                    if (latestSample) handleDismissSample(); 
                    if (latestMidi) handleDismissMidi();
                    setProgress(100);
                    
                    setTimeout(() => {
                        const resultObj = { 
                            file: `http://localhost:5173${data.file}`, 
                            prompt: data.prompt, 
                            key: data.key, 
                            bpm: data.bpm 
                        };
                        
                        if (data.isMidi) {
                            setLatestMidi(resultObj);
                            setStatusMessage("✨ AI MIDI READY");
                        } else {
                            setLatestSample(resultObj);
                            setStatusMessage("✨ AI LOOP READY");
                        }
                        
                        setIsGenerating(false);
                        setActiveModuleState(null); // Stop vibration
                        setIsSuccess(true);
                        
                        setTimeout(() => {
                            setIsSuccess(false);
                            setStatusMessage("SYSTEM READY");
                        }, 2500);
                    }, 500);
                }
                if (data.type === 'TRANSCRIPTION_FINISHED') {
                    setIsGenerating(false);
                    setIsSuccess(true);
                    setActiveModuleState(null); // Stop vibration
                    setLatestMidi({
                        file: `http://localhost:5173${data.file}`,
                        notes: data.notes
                    });
                    setVoiceText(`✨ TRANSCRIBED ${data.notes} NOTES!`);
                    setTimeout(() => {
                        setIsSuccess(false);
                        setVoiceText(null);
                        setStatusMessage("SYSTEM READY");
                    }, 3500);
                }
                if (data.type === 'DOG_ADVICE') {
                    setIsGenerating(false);
                    setActiveModuleState(null);
                    setVoiceText(`🐶 ${data.advice}`);
                    setStatusMessage('DOG ADVISOR: ANSWERED!');
                    setIsSuccess(true);
                }
                if (data.type === 'ERROR') {
                    setIsGenerating(false);
                    setStatusMessage(`❌ ${data.msg}`);
                }
            };

            ws.onclose = () => {
                console.log('[App] WebSocket Disconnected. Retrying in 2s...');
                reconnectTimer = setTimeout(connectWebSocket, 2000);
            };
        };

        connectWebSocket();
        const cleanupSync = initSyncModule();

        const handleStatusUpdate = (msg: string) => {
            setStatusMessage(msg);
            const upperMsg = msg.toUpperCase();
            const isActive = upperMsg.includes("LISTENING") || upperMsg.includes("ANALYZING") || 
                             upperMsg.includes("GENERATING") || upperMsg.includes("COMPOSING") || 
                             upperMsg.includes("MLX") || upperMsg.includes("LYRIA") ||
                             upperMsg.includes("TRANSCRIBING");
            setIsGenerating(isActive);
        };

        const handleVoiceResult = (text: string) => {
            if (!text) return;
            const junkPatterns = ["注目の話題", "告発", "字幕", "ご視聴", "放送大学", "おやすみなさい", "話題の", "話題を"];
            if (junkPatterns.some(pattern => text.includes(pattern))) {
                console.log("🚫 STT HALLUCINATION BLOCKED:", text);
                return;
            }
            setVoiceText(text);
            setTimeout(() => {
                setVoiceText(prev => (prev && !prev.includes("🐶")) ? null : prev);
            }, 3000);
        };

        const handleToggleBgm = () => toggleBgm();

        const handleTriggerVoice = (mode: string) => {
            setIsListening(true);
            setActiveVoiceMode(mode);
        };
        const handleVoiceEnd = () => {
            setIsListening(false);
            setActiveVoiceMode(null);
        };

        const handleHummingStarted = () => {
            setIsListening(true);
            setActiveVoiceMode('humming');
        };

        const handleHummingStopped = () => {
            setIsListening(false);
            setActiveVoiceMode(null);
        };

        const handleCommandComplete = () => {
            setIsGenerating(false);
            setActiveModuleState(null);
            setStatusMessage("SYSTEM READY");
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
            setVoiceText(`🐶 ${advice}`);
            setIsSuccess(true);
        });
        
        eventBus.on(EVENTS.TRIGGER_SAMPLE_GEN, () => {
            setIsGenerating(true);
            setProgress(0);
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
    }, [
        // REMOVED latestMidi, latestSample to prevent reconnection loop
        setIsGenerating, setIsSuccess, setVoiceText, 
        setActiveModuleState, setLatestMidi, setLatestSample, 
        setProgress, setStatusMessage, setBpm, setKey, 
        setIsListening, setActiveVoiceMode, toggleBgm, 
        handleDismissSample, handleDismissMidi
    ]); 
};

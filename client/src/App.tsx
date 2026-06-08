import React, { useState, useRef, useEffect } from 'react';
import { useAppState } from './hooks/useAppState';
import { useAudioTranscription } from './hooks/useAudioTranscription';
import { useEventSubscriptions } from './hooks/useEventSubscriptions';
import { useMidi } from './hooks/useMidi';
import { motion, AnimatePresence } from 'framer-motion';
import { eventBus, EVENTS } from './utils/EventBus';

// Initialize all modules to start listening to the EventBus
import './modules/ControlModules';
import './modules/VoiceControlModule';
import './modules/HummingModule';
import './modules/SoundPaletteModule';
import './modules/UtilityModules';

import { ConfigModal } from './components/ConfigModal';
import { UpdateNotifier } from './components/UpdateNotifier';

import { Console } from './components/Console';
import { DropZoneOverlay } from './components/DropZoneOverlay';
import { Stage } from './components/Stage';

import './App.css';

const App: React.FC = () => {
    const { 
        currentBpm, currentKey,
        isBgmPlaying,
        sampleEngine,
        setBgmPlaying,
        setStatusMessage
    } = useAppState();

    useMidi(); // Initialize Global MIDI Listener

    const [isListening, setIsListening] = useState(false);
    const [activeVoiceMode, setActiveVoiceMode] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [progress, setProgress] = useState(0);
    const [latestSample, setLatestSample] = useState<{file: string, prompt: string, key: string, bpm: number} | null>(null);
    const [activeModule, setActiveModuleState] = useState<string | null>(null);
    const [voiceText, setVoiceText] = useState<string | null>(null);
    const [isConfigOpen, setConfigOpen] = useState(false);
    // Removed splice search state
    const [isSuccess, setIsSuccess] = useState(false);
    const [isPoofing, setIsPoofing] = useState(false); 
    const [isMixing, setIsMixing] = useState(false);
    const [isServerConnected, setIsServerConnected] = useState(true);
    
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const previewAudioRef = useRef<HTMLAudioElement | null>(null);
    const [isPreviewPlaying, setIsPreviewPlaying] = useState(false);

    // Dismiss the latest sample with a 'poof'
    const handleDismissSample = React.useCallback(() => {
        if (!latestSample) return;
        setIsPoofing(true);
        setTimeout(() => {
            setLatestSample(null);
            setIsPoofing(false);
            if (previewAudioRef.current) previewAudioRef.current.pause();
            setIsPreviewPlaying(false);
        }, 500); 
    }, [latestSample]);

    const [latestMidi, setLatestMidi] = useState<{file: string, notes: number} | null>(null);

    // Dismiss logic for MIDI
    const handleDismissMidi = React.useCallback(() => {
        setLatestMidi(null);
    }, []);

    // Activate a module exclusively
    const activateModule = React.useCallback((id: string) => {
        // REMOVED: handleDismissSample() - Let the user decide when to dismiss
        setActiveModuleState(prev => prev === id ? null : id); 
    }, []);

    // Short momentary pulse
    const triggerShortVibration = React.useCallback((id: string, durationMs: number = 300) => {
        // REMOVED: handleDismissSample() - Keep sample visible
        setActiveModuleState(id);
        setTimeout(() => setActiveModuleState(prev => prev === id ? null : prev), durationMs);
    }, []);

    const { isDragging, handleDragOver, handleDragLeave, handleDrop } = useAudioTranscription(setIsGenerating);

    useEffect(() => {
        const handleStart = () => {
            if (audioRef.current && isBgmPlaying) {
                audioRef.current.play().catch(e => console.log("Autoplay prevented:", e));
            }
        };
        const handleSetActiveModule = (id: string) => activateModule(id);
        
        eventBus.on(EVENTS.APP_STARTED, handleStart);
        eventBus.on(EVENTS.SET_ACTIVE_MODULE, handleSetActiveModule);

        return () => {
            eventBus.off(EVENTS.APP_STARTED, handleStart);
            eventBus.off(EVENTS.SET_ACTIVE_MODULE, handleSetActiveModule);
        };
    }, [isBgmPlaying, activateModule]);

    const toggleBgm = React.useCallback(() => {
        const nextState = !isBgmPlaying;
        console.log(`🎵 [BGM] Toggling to: ${nextState}`);
        setBgmPlaying(nextState);
        if (audioRef.current) {
            if (nextState) {
                audioRef.current.currentTime = 0;
                audioRef.current.play().then(() => {
                    console.log("✅ [BGM] Playback started successfully");
                }).catch(e => {
                    console.error("❌ [BGM] Playback failed:", e);
                });
            } else {
                audioRef.current.pause();
                console.log("⏸️ [BGM] Playback paused");
            }
        } else {
            console.warn("⚠️ [BGM] Audio element not found!");
        }
        let statusText = nextState ? "BGM ON" : "BGM OFF";
        if (isGenerating) {
            statusText = sampleEngine === 'cloud_lyria' 
              ? '>>> GEMINI LYRIA IS COMPOSING...' 
              : '>>> LOCAL MLX ENGINE IS COMPOSING...';
        } else if (isListening) {
            statusText = '🐶 LISTENING...';
        }
        setStatusMessage(statusText);
    }, [isBgmPlaying, setBgmPlaying, isGenerating, sampleEngine, isListening, setStatusMessage]);





    const handleCancelAll = React.useCallback(() => {
        setIsGenerating(false);
        setIsListening(false);
        setStatusMessage("SYSTEM READY");
        setProgress(0);
        setActiveModuleState(null);
        setVoiceText(null);
        setIsSuccess(false);
        handleDismissSample();
        handleDismissMidi();
        if (navigator.vibrate) navigator.vibrate([50, 30, 50]); // Feedback pulse
        console.log("🛑 [SYSTEM] EMERGENCY CANCEL TRIGGERED");
    }, [setStatusMessage, handleDismissSample, handleDismissMidi]);

    useEventSubscriptions({
        isGenerating, setIsGenerating,
        setProgress, setIsSuccess, setVoiceText,
        setActiveVoiceMode, setActiveModuleState, setIsListening, isListening,
        setLatestSample, setLatestMidi,
        handleDismissSample, handleDismissMidi,
        toggleBgm, latestSample, latestMidi,
        isMixing, setIsMixing,
        setIsServerConnected,
        handleCancelAll
    });

    return (
        <div 
            className="app-viewport"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            {/* --- SERVER DISCONNECTED OVERLAY --- */}
            <AnimatePresence>
                {!isServerConnected && (
                    <motion.div 
                        className="server-disconnected-overlay"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                    >
                        <div className="reconnect-content retro-text">
                            <div className="reconnect-spinner"></div>
                            <span>OFFLINE: RECONNECTING TO CORE...</span>
                            <p className="reconnect-subtext">Ensure Python Server (8002) is running</p>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <div className="stage-container">
                {/* Invisible drag bar for window movement (Top 40px) */}
                <div className="window-drag-bar" />
                <img src="./assets/bg-2.png" className="full-layer no-click" alt="Background" />

                <Stage 
                    voiceText={voiceText} setVoiceText={setVoiceText} setIsSuccess={setIsSuccess}
                    activeModule={activeModule} isListening={isListening} activeVoiceMode={activeVoiceMode}
                    isGenerating={isGenerating} isMixing={isMixing}
                    latestSample={latestSample} latestMidi={latestMidi} isPoofing={isPoofing}
                    isPreviewPlaying={isPreviewPlaying} setIsPreviewPlaying={setIsPreviewPlaying} previewAudioRef={previewAudioRef}
                    activateModule={activateModule} triggerShortVibration={triggerShortVibration}
                    isBgmPlaying={isBgmPlaying} toggleBgm={toggleBgm} currentBpm={currentBpm}
                    handleCancelAll={handleCancelAll}
                    onOpenConfig={() => setConfigOpen(true)}
                />

                <DropZoneOverlay isDragging={isDragging} />

                <ConfigModal isOpen={isConfigOpen} onClose={() => setConfigOpen(false)} />

                <UpdateNotifier />

                <audio ref={audioRef} src="./assets/bgm.mp3" loop />

                <div className="header-left">
                    <div className="status-item"><div className="label-small retro-text">BPM</div><div className="value-pnm retro-text">{currentBpm}</div></div>
                    <div className="status-item"><div className="label-small retro-text">KEY</div><div className="value-pnm retro-text">{currentKey}</div></div>
                </div>

                {/* --- STATUS CONSOLE (FULLY RESTORED) --- */}
                <Console 
                    isListening={isListening}
                    isGenerating={isGenerating} setIsGenerating={setIsGenerating}
                    activeModule={activeModule} setActiveModuleState={setActiveModuleState}
                    isSuccess={isSuccess} setIsSuccess={setIsSuccess}
                    progress={progress} setProgress={setProgress}
                    setVoiceText={setVoiceText}
                    setActiveVoiceMode={setActiveVoiceMode}
                />

                {/* --- GLOBAL SPEECH BUBBLE (ENSURED TOP LAYER) --- */}
                <AnimatePresence>
                    {voiceText && (
                        <motion.div 
                            className="forced-speech-bubble-container"
                            style={{
                                position: 'fixed',
                                left: '30%',
                                top: '35%', 
                                transform: 'translate(-50%, -50%)',
                                zIndex: 9999999,
                                pointerEvents: 'none'
                            }}
                            initial={{ opacity: 0, scale: 0.8 }}
                            animate={{ opacity: 1, scale: 1 }}
                            exit={{ opacity: 0, scale: 0.8 }}
                        >
                            <div className="speech-bubble" style={{ background: 'white', color: '#333', pointerEvents: 'auto', border: '4px solid #fff' }}>
                                {voiceText}
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
            </div>
        </div>
    );
};

export default App;

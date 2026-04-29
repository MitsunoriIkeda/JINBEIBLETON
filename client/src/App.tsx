import React, { useState, useRef } from 'react';
import { useAppState } from './hooks/useAppState';
import { useAudioTranscription } from './hooks/useAudioTranscription';
import { useEventSubscriptions } from './hooks/useEventSubscriptions';

// Initialize all modules to start listening to the EventBus
import './modules/ControlModules';
import './modules/VoiceControlModule';
import './modules/HummingModule';
import './modules/SoundPaletteModule';
import './modules/UtilityModules';

import { ConfigModal } from './components/ConfigModal';
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

    const [isListening, setIsListening] = useState(false);
    const [activeVoiceMode, setActiveVoiceMode] = useState<string | null>(null);
    const [isGenerating, setIsGenerating] = useState(false);
    const [progress, setProgress] = useState(0);
    const [latestSample, setLatestSample] = useState<{file: string, prompt: string, key: string, bpm: number} | null>(null);
    const [activeModule, setActiveModuleState] = useState<string | null>(null);
    const [voiceText, setVoiceText] = useState<string | null>(null);
    const [isConfigOpen, setConfigOpen] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);
    const [isPoofing, setIsPoofing] = useState(false); 
    
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

    // Activate a module exclusively — triggers 'poof' on existing sample
    const activateModule = React.useCallback((id: string) => {
        if (latestSample) handleDismissSample(); 
        if (latestMidi) handleDismissMidi();
        setActiveModuleState(prev => prev === id ? null : id); 
    }, [latestSample, latestMidi, handleDismissSample, handleDismissMidi]);

    // Short momentary pulse (for non-toggle buttons like Sync)
    const triggerShortVibration = React.useCallback((id: string, durationMs: number = 300) => {
        if (latestSample) handleDismissSample(); 
        if (latestMidi) handleDismissMidi();
        setActiveModuleState(id);
        setTimeout(() => setActiveModuleState(prev => prev === id ? null : prev), durationMs);
    }, [latestSample, latestMidi, handleDismissSample, handleDismissMidi]);

    const { isDragging, handleDragOver, handleDragLeave, handleDrop } = useAudioTranscription(setIsGenerating);

    const toggleBgm = React.useCallback(() => {
        const nextState = !isBgmPlaying;
        setBgmPlaying(nextState);
        if (audioRef.current) {
            if (nextState) {
                audioRef.current.currentTime = 0;
                audioRef.current.play();
            } else {
                audioRef.current.pause();
            }
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

    useEventSubscriptions({
        isGenerating, setIsGenerating,
        setProgress, setIsSuccess, setVoiceText,
        setActiveVoiceMode, setActiveModuleState, setIsListening,
        setLatestSample, setLatestMidi,
        handleDismissSample, handleDismissMidi,
        toggleBgm, latestSample, latestMidi
    });

    return (
        <div 
            className="app-viewport"
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
        >
            <div className="stage-container">
                <img src="/assets/bg-2.png" className="full-layer no-click" alt="Background" />

                <Stage 
                    voiceText={voiceText} setVoiceText={setVoiceText} setIsSuccess={setIsSuccess}
                    activeModule={activeModule} isListening={isListening} activeVoiceMode={activeVoiceMode}
                    latestSample={latestSample} latestMidi={latestMidi} isPoofing={isPoofing}
                    isPreviewPlaying={isPreviewPlaying} setIsPreviewPlaying={setIsPreviewPlaying} previewAudioRef={previewAudioRef}
                    activateModule={activateModule} triggerShortVibration={triggerShortVibration}
                    isBgmPlaying={isBgmPlaying} toggleBgm={toggleBgm} currentBpm={currentBpm}
                />

                <DropZoneOverlay isDragging={isDragging} />

                <ConfigModal isOpen={isConfigOpen} onClose={() => setConfigOpen(false)} />

                <audio ref={audioRef} src="/assets/bgm.mp3" loop />

                <div className="header-left">
                    <div className="status-item"><div className="label-small retro-text">BPM</div><div className="value-pnm retro-text">{currentBpm}</div></div>
                    <div className="status-item"><div className="label-small retro-text">KEY</div><div className="value-pnm retro-text">{currentKey}</div></div>
                </div>

                <div className="header-right">
                    <button className="config-btn btn-yellow" onClick={() => setConfigOpen(true)} style={{ width: 'auto', padding: '0 20px' }}>
                        ⚙️ AI CONFIG ▾
                    </button>
                </div>

                {/* --- STATUS CONSOLE (FULLY RESTORED) --- */}
                <Console 
                    isGenerating={isGenerating} setIsGenerating={setIsGenerating}
                    activeModule={activeModule} setActiveModuleState={setActiveModuleState}
                    isSuccess={isSuccess} setIsSuccess={setIsSuccess}
                    progress={progress} setProgress={setProgress}
                    setVoiceText={setVoiceText}
                />
            </div>
        </div>
    );
};

export default App;

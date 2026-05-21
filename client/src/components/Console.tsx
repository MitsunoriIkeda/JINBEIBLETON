import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { useAppState } from '../hooks/useAppState';
import { eventBus, EVENTS } from '../utils/EventBus';

interface ConsoleProps {
    isListening: boolean;
    isGenerating: boolean;
    setIsGenerating: (val: boolean) => void;
    activeModule: string | null;
    setActiveModuleState: (val: string | null) => void;
    isSuccess: boolean;
    setIsSuccess: (val: boolean) => void;
    progress: number;
    setProgress: (val: number) => void;
    setVoiceText: (val: string | null | ((prev: string | null) => string | null)) => void;
    setActiveVoiceMode: (val: string | null) => void;
}

export const Console: React.FC<ConsoleProps> = ({
    isListening,
    isGenerating, setIsGenerating,
    activeModule: _activeModule, setActiveModuleState,
    isSuccess, setIsSuccess,
    progress, setProgress,
    setVoiceText,
    setActiveVoiceMode
}) => {

    const { statusMessage, setStatusMessage, voiceEngine, sampleEngine, midiEngine, ollamaModel, geminiApiKey, openaiApiKey, claudeApiKey, setCurrentMode, currentMode } = useAppState();
    const [commandMode, setCommandMode] = useState('control');
    const [micVolume, setMicVolume] = useState(0);

    useEffect(() => {
        const onVolume = (vol: number) => {
            console.log(`🎙 [UI Console] MIC_VOLUME state updated: ${vol}%`);
            setMicVolume(vol);
        };
        eventBus.on('MIC_VOLUME', onVolume);
        return () => {
            eventBus.off('MIC_VOLUME', onVolume);
        };
    }, []);

    // Sync local commandMode with global currentMode
    useEffect(() => {
        if (currentMode) {
            setCommandMode(currentMode);
        }
    }, [currentMode]);

    useEffect(() => {
        // Mode change cleanup or other side effects can go here
        
        const onChordMelody = () => {
            setCommandMode('midi');
            setCurrentMode('midi');
            handleChordToMelody();
        };

        eventBus.on(EVENTS.TRIGGER_CHORD_MELODY, onChordMelody);

        return () => {
            eventBus.off(EVENTS.TRIGGER_CHORD_MELODY, onChordMelody);
        };
    }, [voiceEngine, sampleEngine, midiEngine, ollamaModel, geminiApiKey, openaiApiKey, claudeApiKey]);


    const handleCommandSubmit = async (val: string, forceMode?: string) => {
        if (!val.trim()) return;
        setStatusMessage(">>> ANALYZING COMMAND...");
        setIsGenerating(true);
        const currentReqMode = forceMode || commandMode;
        setActiveVoiceMode(currentReqMode);
        try {
            const resp = await fetch('http://localhost:8002/api/v1/voice/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: val, 
                    mode: currentReqMode, 
                    engine: voiceEngine,
                    sampleEngine: sampleEngine,
                    midiEngine: midiEngine,
                    ollamaModel: ollamaModel,
                    geminiKey: geminiApiKey,
                    openaiKey: openaiApiKey,
                    claudeKey: claudeApiKey
                })

            });
            const result = await resp.json();
            if (result.status === 'success') {
                setProgress(100);
                setTimeout(() => {
                    setIsGenerating(false);
                    setIsSuccess(true);
                    
                    if (commandMode !== 'advisor') {
                        setVoiceText(val);
                        setTimeout(() => {
                            setVoiceText(prev => prev?.startsWith("🐶") ? prev : null);
                        }, 3000);
                    }
                    
                    setStatusMessage("COMMAND EXECUTED (SUCCESS)");
                    setTimeout(() => {
                        setIsSuccess(false);
                        setStatusMessage("SYSTEM READY");
                    }, 2500);
                }, 500);
            } else {
                setStatusMessage("COMMAND ERROR");
                setIsGenerating(false);
            }
        } catch (err) {
            setStatusMessage("NETWORK ERROR");
            setIsGenerating(false);
        } finally {
            setActiveModuleState(null);
            // Don't clear activeVoiceMode here, let the SUCCESS/ERROR events handle it or leave it for animation
        }
    };

    const handleChordToMelody = async () => {
        setStatusMessage('FETCHING CHORDS...');
        setProgress(20);
        setIsGenerating(true);
        try {
            const bridgeRes = await fetch('http://localhost:8005/api/v1/ableton/execute', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ action: 'get_notes' })
            });
            const bridgeData = await bridgeRes.json();
            if (bridgeData.status !== 'success' || !bridgeData.data || bridgeData.data.length === 0) {
                setStatusMessage('ERROR: NO CHORDS FOUND (SELECT CLIP)');
                setProgress(0);
                setIsGenerating(false);
                return;
            }
            
            setStatusMessage('COMPOSING MELODY FROM CHORDS...');
            setProgress(40);
            const resp = await fetch('http://localhost:8002/api/v1/voice/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: "このコード進行に完璧に合うメロディを作って", 
                    mode: "melody", 
                    engine: voiceEngine,
                    sampleEngine: sampleEngine,
                    midiEngine: midiEngine,
                    ollamaModel: ollamaModel,
                    geminiKey: geminiApiKey,
                    openaiKey: openaiApiKey,
                    claudeKey: claudeApiKey,
                    chordNotes: bridgeData.data
                })
            });
            const result = await resp.json();
            if (result.status === 'success') {
                setProgress(100);
                setTimeout(() => {
                    setIsGenerating(false);
                    setIsSuccess(true);
                    setStatusMessage("MELODY GENERATED (SUCCESS)");
                    setTimeout(() => {
                        setIsSuccess(false);
                        setStatusMessage("SYSTEM READY");
                    }, 2500);
                }, 500);
            } else {
                setStatusMessage("COMMAND ERROR");
                setIsGenerating(false);
            }
        } catch (e) {
            setStatusMessage('ERROR: SERVER CONNECTION FAILED');
            setProgress(0);
            setIsGenerating(false);
        } finally {
            setActiveModuleState(null);
        }
    };

    return (
        <div 
            className={`status-console 
                ${isGenerating && (statusMessage.toUpperCase().includes("COMPOSING") || statusMessage.toUpperCase().includes("MLX") || statusMessage.toUpperCase().includes("ANALYZING")) ? 'thinking' : (isGenerating ? 'waiting-glow' : '')} 
                ${isSuccess ? 'success-glow' : ''}
            `} 
            onClick={() => setStatusMessage("SYSTEM READY")}
        >
            <div className="console-header retro-text">
                STATUS: {isListening ? "VOICE LISTENING..." : (isGenerating ? "AI WORKING..." : (isSuccess ? "EXECUTION COMPLETE" : "SYSTEM READY"))}
            </div>
            <div className="console-body retro-text">
                <div 
                    className={isGenerating ? "blinking-green" : ""} 
                    style={{ 
                        color: isSuccess ? '#00ffff' : '#00ff00',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        width: '100%'
                    }}
                    title={statusMessage}
                >
                    {isGenerating && (statusMessage.toUpperCase().includes("COMPOSING") || statusMessage.toUpperCase().includes("MIDI") || statusMessage.toUpperCase().includes("MLX"))
                        ? (statusMessage.toUpperCase().includes("MIDI") 
                            ? `>>> AI MIDI COMPOSER (${midiEngine === 'cloud_openai' ? 'OPENAI' : midiEngine === 'cloud_claude' ? 'CLAUDE' : midiEngine === 'cloud_gemini' ? 'GEMINI 3' : 'LOCAL OLLAMA'}) IS BUSY...` 
                            : (sampleEngine === 'local_mlx' ? ">>> LOCAL MLX ENGINE IS COMPOSING..." : ">>> GEMINI 3 IS COMPOSING..."))
                        : `${(statusMessage.startsWith('>>>') || isGenerating) ? '' : '>>> '}${statusMessage}`}
                </div>
                {isListening && (
                    <div style={{ position: 'relative', width: '100%' }}>
                        <div className="progress-container mic-meter">
                            <motion.div 
                                className="progress-fill mic-fill" 
                                initial={{ width: 0 }}
                                animate={{ width: `${micVolume}%` }}
                                transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                            />
                        </div>
                        <div className="progress-text retro-text">MIC LEVEL</div>
                    </div>
                )}
                {isGenerating && !isListening && (
                    <div style={{ position: 'relative', width: '100%' }}>
                        <div className="progress-container">
                            {progress === 0 ? (
                                <motion.div 
                                    className="progress-fill" 
                                    initial={{ width: "20%", left: "0%" }}
                                    animate={{ 
                                        left: ["0%", "80%", "0%"]
                                    }}
                                    transition={{ 
                                        repeat: Infinity,
                                        duration: 1.5,
                                        ease: "easeInOut"
                                    }}
                                    style={{ position: 'absolute' }}
                                />
                            ) : (
                                <motion.div 
                                    className="progress-fill" 
                                    initial={{ width: 0 }}
                                    animate={{ width: `${progress}%` }}
                                />
                            )}
                        </div>
                        <div className="progress-text retro-text">
                            {progress === 0 ? "AI WORKING..." : `${Math.round(progress)}%`}
                        </div>
                    </div>
                )}
            </div>
            <div className="console-footer">
                <div className="mode-tabs">
                    <div className={`mode-tab ctrl ${commandMode === 'control' ? 'active' : ''}`} onClick={(e) => { 
                        e.stopPropagation(); 
                        setCommandMode('control'); 
                        setCurrentMode('control');
                    }}>🎛 CTRL</div>
                    <div className={`mode-tab sampler ${commandMode === 'sampler' ? 'active' : ''}`} onClick={(e) => { 
                        e.stopPropagation(); 
                        setCommandMode('sampler'); 
                        setCurrentMode('sampler');
                    }}>🎵 SAMPLE</div>
                    <div className={`mode-tab midi ${commandMode === 'midi' ? 'active' : ''}`} onClick={(e) => { 
                        e.stopPropagation(); 
                        setCommandMode('midi'); 
                        setCurrentMode('midi');
                    }}>🎹 MIDI</div>
                    <div className={`mode-tab learning ${commandMode === 'learning' ? 'active' : ''}`} onClick={(e) => { 
                        e.stopPropagation(); 
                        setCommandMode('learning'); 
                        setCurrentMode('learning');
                    }}>🚜 LEARN</div>
                    <div className={`mode-tab advisor ${commandMode === 'advisor' ? 'active' : ''}`} onClick={(e) => { 
                        e.stopPropagation(); 
                        setCommandMode('advisor'); 
                        setCurrentMode('advisor');
                    }}>🐶 ADVISOR</div>
                </div>
                <input 
                    type="text" 
                    className={`command-input retro-text mode-${commandMode}`} 
                    placeholder={`ENTER ${commandMode.toUpperCase()} COMMAND...`} 
                    onClick={(e) => e.stopPropagation()}
                    onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                            const val = e.currentTarget.value;
                            e.currentTarget.value = "";
                            handleCommandSubmit(val);
                        }
                    }}
                />
            </div>
        </div>
    );
};

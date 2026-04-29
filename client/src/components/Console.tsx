import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { useAppState } from '../hooks/useAppState';

interface ConsoleProps {
    isGenerating: boolean;
    setIsGenerating: (val: boolean) => void;
    activeModule: string | null;
    setActiveModuleState: (val: string | null) => void;
    isSuccess: boolean;
    setIsSuccess: (val: boolean) => void;
    progress: number;
    setProgress: (val: number) => void;
    setVoiceText: (val: string | null | ((prev: string | null) => string | null)) => void;
}

export const Console: React.FC<ConsoleProps> = ({
    isGenerating, setIsGenerating,
    activeModule, setActiveModuleState,
    isSuccess, setIsSuccess,
    progress, setProgress,
    setVoiceText
}) => {
    const { statusMessage, setStatusMessage, voiceEngine, sampleEngine, midiEngine } = useAppState();
    const [commandMode, setCommandMode] = useState('control');

    const handleCommandSubmit = async (val: string) => {
        if (!val.trim()) return;
        setStatusMessage("EXECUTING COMMAND...");
        setIsGenerating(true);
        try {
            const resp = await fetch('http://localhost:8002/api/v1/voice/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    text: val, 
                    mode: commandMode, 
                    engine: voiceEngine,
                    sample_engine: sampleEngine
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
        }
    };

    return (
        <div 
            className={`status-console 
                ${isGenerating && activeModule === 'yellow' ? 'thinking' : ''} 
                ${isGenerating && activeModule !== 'yellow' ? 'waiting-glow' : ''} 
                ${isSuccess ? 'success-glow' : ''}
            `} 
            onClick={() => setStatusMessage("SYSTEM READY")}
        >
            <div className="console-header retro-text">
                STATUS: {isGenerating ? "AI ANALYZING..." : (isSuccess ? "EXECUTION COMPLETE" : "SYSTEM READY")}
            </div>
            <div className="console-body retro-text">
                <div className={isGenerating ? "blinking-green" : ""} style={{ color: isSuccess ? '#00ffff' : '#00ff00' }}>
                    {isGenerating && (statusMessage.toUpperCase().includes("COMPOSING") || statusMessage.toUpperCase().includes("MIDI") || statusMessage.toUpperCase().includes("MLX"))
                        ? (statusMessage.toUpperCase().includes("MIDI") 
                            ? `>>> AI MIDI COMPOSER (${midiEngine === 'cloud_openai' ? 'OPENAI' : midiEngine === 'cloud_gemini' ? 'GEMINI 3' : 'LOCAL OLLAMA'}) IS BUSY...` 
                            : (sampleEngine === 'local_mlx' ? ">>> LOCAL MLX ENGINE IS COMPOSING..." : ">>> GEMINI 3 IS COMPOSING..."))
                        : `${(statusMessage.startsWith('>>>') || isGenerating) ? '' : '>>> '}${statusMessage}`}
                </div>
                {isGenerating && activeModule === 'yellow' && (statusMessage.toUpperCase().includes("COMPOSING") || statusMessage.toUpperCase().includes("MLX")) && (
                    <div className="progress-container">
                        <motion.div 
                            className="progress-fill" 
                            initial={{ width: 0 }}
                            animate={{ width: `${progress}%` }}
                        />
                        <div className="progress-text retro-text">{Math.round(progress)}%</div>
                    </div>
                )}
            </div>
            <div className="console-footer">
                <div className="mode-tabs">
                    <div className={`mode-tab ctrl ${commandMode === 'control' ? 'active' : ''}`} onClick={(e) => { e.stopPropagation(); setCommandMode('control'); }}>🎛 CTRL</div>
                    <div className={`mode-tab sampler ${commandMode === 'sampler' ? 'active' : ''}`} onClick={(e) => { e.stopPropagation(); setCommandMode('sampler'); }}>🎵 SAMPLE</div>
                    <div className={`mode-tab midi ${commandMode === 'midi' ? 'active' : ''}`} onClick={(e) => { e.stopPropagation(); setCommandMode('midi'); }}>🎹 MIDI</div>
                    <div className={`mode-tab advisor ${commandMode === 'advisor' ? 'active' : ''}`} onClick={(e) => { e.stopPropagation(); setCommandMode('advisor'); }}>🐶 ADVISOR</div>
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

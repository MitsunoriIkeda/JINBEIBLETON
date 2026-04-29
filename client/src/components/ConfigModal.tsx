import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppState } from '../hooks/useAppState';

interface ConfigModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const ConfigModal: React.FC<ConfigModalProps> = ({ isOpen, onClose }) => {
    const { 
        voiceEngine, sampleEngine, transcriptionEngine, midiEngine,
        geminiApiKey, openaiApiKey,
        setVoiceEngine, setSampleEngine, setTranscriptionEngine, setMidiEngine,
        setGeminiApiKey, setOpenaiApiKey
    } = useAppState();

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div className="config-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                    <motion.div className="config-window" initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }}>
                        <div className="window-header retro-text">AI SYSTEM CONFIGURATION</div>
                        <div className="window-body">
                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#ff00ff'}}>VOICE COMMAND AI:</label>
                                <div className="model-grid">
                                    <div className={`model-card ${voiceEngine === 'local_ollama' ? 'active' : ''}`} onClick={() => setVoiceEngine('local_ollama')}>LOCAL (OLLAMA / GEMMA4)</div>
                                    <div className={`model-card ${voiceEngine === 'cloud_gemini' ? 'active' : ''}`} onClick={() => setVoiceEngine('cloud_gemini')}>CLOUD (GEMINI 3)</div>
                                    <div className={`model-card ${voiceEngine === 'cloud_openai' ? 'active' : ''}`} onClick={() => setVoiceEngine('cloud_openai')}>CLOUD (GPT-4O)</div>
                                </div>
                            </div>
                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#00ffff'}}>SAMPLE GENERATOR AI:</label>
                                <div className="model-grid">
                                    <div className={`model-card ${sampleEngine === 'local_mlx' ? 'active' : ''}`} onClick={() => setSampleEngine('local_mlx')}>LOCAL (MLX MUSICGEN)</div>
                                    <div className={`model-card ${sampleEngine === 'cloud_lyria' ? 'active' : ''}`} onClick={() => setSampleEngine('cloud_lyria')}>CLOUD (GEMINI 3 LYRIA)</div>
                                </div>
                            </div>
                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#ffff00'}}>MIDI GENERATOR AI:</label>
                                <div className="model-grid">
                                    <div className={`model-card ${midiEngine === 'local_ollama' ? 'active' : ''}`} onClick={() => setMidiEngine('local_ollama')}>LOCAL (OLLAMA / GEMMA4)</div>
                                    <div className={`model-card ${midiEngine === 'cloud_gemini' ? 'active' : ''}`} onClick={() => setMidiEngine('cloud_gemini')}>CLOUD (GEMINI 3)</div>
                                    <div className={`model-card ${midiEngine === 'cloud_openai' ? 'active' : ''}`} onClick={() => setMidiEngine('cloud_openai')}>CLOUD (GPT-4O)</div>
                                </div>
                            </div>
                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#00ff00'}}>AUDIO-TO-MIDI ENGINE (LOCAL):</label>
                                <div className="model-grid">
                                    <div className={`model-card ${transcriptionEngine === 'basic-pitch' ? 'active' : ''}`} onClick={() => setTranscriptionEngine('basic-pitch')}>BASIC PITCH (FAST)</div>
                                    <div className={`model-card ${transcriptionEngine === 'mt3' ? 'active' : ''}`} onClick={() => setTranscriptionEngine('mt3')}>MT3 (MULTITRACK)</div>
                                    <div className={`model-card ${transcriptionEngine === 'giantmidi-piano' ? 'active' : ''}`} onClick={() => setTranscriptionEngine('giantmidi-piano')}>GIANTMIDI (SOLO PIANO)</div>
                                </div>
                            </div>
                            <div className="config-group" style={{marginTop: '10px', display: 'flex', alignItems: 'center', gap: '10px'}}>
                                <label className="retro-text label-small" style={{marginBottom: 0, whiteSpace: 'nowrap', width: '120px'}}>GEMINI KEY:</label>
                                <input type="password" value={geminiApiKey} onChange={(e) => setGeminiApiKey(e.target.value)} className="config-input retro-text" placeholder="AIZA..." />
                            </div>
                            <div className="config-group" style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                                <label className="retro-text label-small" style={{marginBottom: 0, whiteSpace: 'nowrap', width: '120px'}}>OPENAI KEY:</label>
                                <input type="password" value={openaiApiKey} onChange={(e) => setOpenaiApiKey(e.target.value)} className="config-input retro-text" placeholder="SK-..." />
                            </div>
                            <button className="confirm-btn retro-text" onClick={onClose}>CONFIRM & APPLY</button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

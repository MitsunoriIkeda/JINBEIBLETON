import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppState } from '../hooks/useAppState';

interface ConfigModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const ConfigModal: React.FC<ConfigModalProps> = ({ isOpen, onClose }) => {
    const { 
        voiceEngine, sampleEngine, transcriptionEngine, midiEngine,
        geminiApiKey, openaiApiKey, claudeApiKey, hfToken, ollamaModel,
        localAiProvider, localAiBaseUrl, language, micDeviceId,
        setVoiceEngine, setSampleEngine, setTranscriptionEngine, setMidiEngine,
        setGeminiApiKey, setOpenaiApiKey, setClaudeApiKey, setHfToken, setOllamaModel,
        setLocalAiProvider, setLocalAiBaseUrl, setLanguage, setMicDeviceId
    } = useAppState();
 
    const [availableModels, setAvailableModels] = useState<string[]>([]);
    const [availableMics, setAvailableMics] = useState<MediaDeviceInfo[]>([]);
    const [availableTranscribers, setAvailableTranscribers] = useState<{ [key: string]: boolean }>({
        'mt3': true,
        'giantmidi-piano': true,
        'muscriptor': true
    });
 
    useEffect(() => {
        if (isOpen) {
            // Fetch local models
            fetch('http://localhost:8002/api/v1/models/local', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ baseUrl: localAiBaseUrl, provider: localAiProvider })
            })
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'success' && data.models) {
                        setAvailableModels(data.models);
                    }
                })
                .catch(err => console.error("Failed to fetch local models:", err));

            // Fetch system status (available transcription engines)
            fetch('http://localhost:8002/api/v1/system/status')
                .then(res => res.json())
                .then(data => {
                    if (data.status === 'online' && data.engines) {
                        setAvailableTranscribers(data.engines);
                    }
                })
                .catch(err => console.error("Failed to fetch system status:", err));

            // Enumerate microphones
            navigator.mediaDevices.enumerateDevices()
                .then(devices => {
                    const mics = devices.filter(d => d.kind === 'audioinput');
                    setAvailableMics(mics);
                    console.log("🎤 Available Microphones:", mics);
                })
                .catch(err => console.error("Failed to list mics:", err));
        }
    }, [isOpen, localAiBaseUrl, localAiProvider]);

    const handleProviderChange = (provider: 'ollama' | 'lm-studio' | 'custom') => {
        setLocalAiProvider(provider);
        if (provider === 'ollama') setLocalAiBaseUrl('http://localhost:11434');
        if (provider === 'lm-studio') setLocalAiBaseUrl('http://localhost:1234');
    };
 
    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div className="config-overlay" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}>
                    <motion.div className="config-window" initial={{ scale: 0.9, y: 20 }} animate={{ scale: 1, y: 0 }} onClick={(e) => e.stopPropagation()}>
                        <div className="window-header retro-text" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span>AI SYSTEM CONFIGURATION</span>
                            <button 
                                className={`lang-toggle-btn retro-text ${language === 'en-US' ? 'active-en' : 'active-jp'}`}
                                onClick={() => setLanguage(language === 'ja-JP' ? 'en-US' : 'ja-JP')}
                                style={{ position: 'relative', top: 0, right: 0, padding: '4px 12px', fontSize: '12px' }}
                            >
                                {language === 'ja-JP' ? 'JP' : 'EN'}
                            </button>
                        </div>
                        <div className="window-body">
                            <div className="config-group" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '15px' }}>
                                <label className="retro-text label-small" style={{color: '#00ff88', marginBottom: 0, whiteSpace: 'nowrap', width: '150px'}}>MICROPHONE:</label>
                                <select 
                                    className="config-input retro-text" 
                                    style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', cursor: 'pointer' }}
                                    value={micDeviceId}
                                    onChange={(e) => setMicDeviceId(e.target.value)}
                                >
                                    <option value="default">Default System Mic</option>
                                    {availableMics.map(mic => (
                                        <option key={mic.deviceId} value={mic.deviceId}>{mic.label || `Mic ${mic.deviceId.slice(0,5)}`}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#ffaa00'}}>LOCAL AI BACKEND:</label>
                                <div className="model-grid">
                                    <div className={`model-card ${localAiProvider === 'ollama' ? 'active' : ''}`} onClick={() => handleProviderChange('ollama')}>OLLAMA</div>
                                    <div className={`model-card ${localAiProvider === 'lm-studio' ? 'active' : ''}`} onClick={() => handleProviderChange('lm-studio')}>LM STUDIO</div>
                                    <div className={`model-card ${localAiProvider === 'custom' ? 'active' : ''}`} onClick={() => handleProviderChange('custom')}>CUSTOM</div>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '10px' }}>
                                    <label className="retro-text label-small" style={{marginBottom: 0, width: '120px', color: '#888'}}>BASE URL:</label>
                                    <input 
                                        type="text" 
                                        value={localAiBaseUrl} 
                                        onChange={(e) => setLocalAiBaseUrl(e.target.value)} 
                                        className="config-input retro-text" 
                                        placeholder="http://localhost:..."
                                    />
                                </div>
                            </div>
                            
                            <div className="config-group" style={{ display: 'flex', alignItems: 'center', gap: '10px', marginTop: '10px', marginBottom: '15px' }}>
                                <label className="retro-text label-small" style={{color: '#ff8800', marginBottom: 0, whiteSpace: 'nowrap', width: '150px'}}>MODEL NAME:</label>
                                <select 
                                    className="config-input retro-text" 
                                    style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.5)', cursor: 'pointer' }}
                                    value={ollamaModel}
                                    onChange={(e) => setOllamaModel(e.target.value)}
                                >
                                    <option value={ollamaModel}>{ollamaModel} (Current)</option>
                                    {availableModels.filter(m => m !== ollamaModel).map(model => (
                                        <option key={model} value={model}>{model}</option>
                                    ))}
                                </select>
                            </div>

                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#ff00ff'}}>VOICE COMMAND AI:</label>
                                <div className="model-grid">
                                    <div className={`model-card ${voiceEngine === 'local_ollama' ? 'active' : ''}`} onClick={() => setVoiceEngine('local_ollama')}>LOCAL (AI-ENGINE)</div>
                                    <div className={`model-card ${voiceEngine === 'cloud_gemini' ? 'active' : ''}`} onClick={() => setVoiceEngine('cloud_gemini')}>CLOUD (GEMINI 3)</div>
                                    <div className={`model-card ${voiceEngine === 'cloud_openai' ? 'active' : ''}`} onClick={() => setVoiceEngine('cloud_openai')}>CLOUD (GPT-4O)</div>
                                    <div className={`model-card ${voiceEngine === 'cloud_claude' ? 'active' : ''}`} onClick={() => setVoiceEngine('cloud_claude')}>CLOUD (CLAUDE 3.5)</div>
                                </div>
                            </div>
                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#00ffff'}}>SAMPLE GENERATOR AI:</label>
                                <div className="model-grid">
                                    <div className={`model-card ${sampleEngine === 'local_mlx' ? 'active' : ''}`} onClick={() => setSampleEngine('local_mlx')}>LOCAL</div>
                                    <div className={`model-card ${sampleEngine === 'cloud_lyria' ? 'active' : ''}`} onClick={() => setSampleEngine('cloud_lyria')}>CLOUD (GEMINI 3 LYRIA)</div>
                                </div>
                            </div>
                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#ffff00'}}>MIDI GENERATOR AI:</label>
                                <div className="model-grid">
                                    <div className={`model-card ${midiEngine === 'local_ollama' ? 'active' : ''}`} onClick={() => setMidiEngine('local_ollama')}>LOCAL</div>
                                    <div className={`model-card ${midiEngine === 'cloud_gemini' ? 'active' : ''}`} onClick={() => setMidiEngine('cloud_gemini')}>CLOUD (GEMINI 3)</div>
                                    <div className={`model-card ${midiEngine === 'cloud_openai' ? 'active' : ''}`} onClick={() => setMidiEngine('cloud_openai')}>CLOUD (GPT-4O)</div>
                                    <div className={`model-card ${midiEngine === 'cloud_claude' ? 'active' : ''}`} onClick={() => setMidiEngine('cloud_claude')}>CLOUD (CLAUDE 3.5)</div>
                                </div>
                            </div>
                            <div className="config-group">
                                <label className="retro-text label-small" style={{color: '#00ff00'}}>AUDIO-TO-MIDI ENGINE (LOCAL):</label>
                                <div className="model-grid">
                                    <div 
                                        className={`model-card ${transcriptionEngine === 'mt3' ? 'active' : ''} ${!availableTranscribers['mt3'] ? 'disabled' : ''}`} 
                                        onClick={() => availableTranscribers['mt3'] && setTranscriptionEngine('mt3')}
                                    >
                                        MT3 {availableTranscribers['mt3'] ? '(MULTITRACK)' : '(N/A)'}
                                    </div>
                                    <div 
                                        className={`model-card ${transcriptionEngine === 'giantmidi-piano' ? 'active' : ''} ${!availableTranscribers['giantmidi-piano'] ? 'disabled' : ''}`} 
                                        onClick={() => availableTranscribers['giantmidi-piano'] && setTranscriptionEngine('giantmidi-piano')}
                                    >
                                        GIANTMIDI {availableTranscribers['giantmidi-piano'] ? '(PIANO)' : '(N/A)'}
                                    </div>
                                    <div 
                                        className={`model-card ${transcriptionEngine === 'muscriptor' ? 'active' : ''} ${!availableTranscribers['muscriptor'] ? 'disabled' : ''}`} 
                                        onClick={() => availableTranscribers['muscriptor'] && setTranscriptionEngine('muscriptor')}
                                    >
                                        MUSCRIPTOR {availableTranscribers['muscriptor'] ? '(MULTI-INST)' : '(N/A)'}
                                    </div>
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
                            <div className="config-group" style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                                <label className="retro-text label-small" style={{marginBottom: 0, whiteSpace: 'nowrap', width: '120px'}}>CLAUDE KEY:</label>
                                <input type="password" value={claudeApiKey} onChange={(e) => setClaudeApiKey(e.target.value)} className="config-input retro-text" placeholder="SK-ANT-..." />
                            </div>
                            <div className="config-group" style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
                                <label className="retro-text label-small" style={{marginBottom: 0, whiteSpace: 'nowrap', width: '120px'}}>HF TOKEN:</label>
                                <input type="password" value={hfToken} onChange={(e) => setHfToken(e.target.value)} className="config-input retro-text" placeholder="hf_..." />
                            </div>
                            <button className="confirm-btn retro-text" onClick={onClose} style={{marginTop: '15px'}}>CONFIRM & APPLY</button>

                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

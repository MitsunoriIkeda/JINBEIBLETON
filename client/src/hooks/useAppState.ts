import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppState {
    // Global Context
    currentBpm: number;
    currentKey: string;
    currentTime: string;
    
    // UI State
    isMicActive: boolean;
    isBgmPlaying: boolean;
    isFullscreen: boolean;
    statusMessage: string;
    
    // AI Configuration
    geminiApiKey: string;
    openaiApiKey: string;
    claudeApiKey: string;
    hfToken: string;
    voiceEngine: 'local_ollama' | 'cloud_gemini' | 'cloud_openai' | 'cloud_claude';
    sampleEngine: 'local_mlx' | 'cloud_lyria';
    transcriptionEngine: 'mt3' | 'giantmidi-piano' | 'muscriptor';
    midiEngine: 'local_ollama' | 'cloud_gemini' | 'cloud_openai' | 'cloud_claude';
    ollamaModel: string;
    localAiProvider: 'ollama' | 'lm-studio' | 'custom';
    localAiBaseUrl: string;
    currentMode: 'control' | 'sampler' | 'midi' | 'advisor' | 'learning';
    
    // Sample Search Config
    sampleSearchEngineType: 'freesound' | 'local' | 'splice_mcp';
    freesoundApiKey: string;
    localSamplePath: string;
    
    language: 'ja-JP' | 'en-US';
    micDeviceId: string;
    
    // Actions
    setLanguage: (lang: 'ja-JP' | 'en-US') => void;
    setBpm: (bpm: number) => void;
    setKey: (key: string) => void;
    setTime: (time: string) => void;
    setMicActive: (active: boolean) => void;
    setBgmPlaying: (playing: boolean) => void;
    setFullscreen: (fullscreen: boolean) => void;
    setStatusMessage: (msg: string) => void;
    setGeminiApiKey: (key: string) => void;
    setOpenaiApiKey: (key: string) => void;
    setClaudeApiKey: (key: string) => void;
    setHfToken: (token: string) => void;
    setVoiceEngine: (engine: 'local_ollama' | 'cloud_gemini' | 'cloud_openai' | 'cloud_claude') => void;
    setSampleEngine: (engine: 'local_mlx' | 'cloud_lyria') => void;
    setTranscriptionEngine: (engine: 'mt3' | 'giantmidi-piano' | 'muscriptor') => void;
    setMidiEngine: (engine: 'local_ollama' | 'cloud_gemini' | 'cloud_openai' | 'cloud_claude') => void;
    setOllamaModel: (model: string) => void;
    setLocalAiProvider: (provider: 'ollama' | 'lm-studio' | 'custom') => void;
    setLocalAiBaseUrl: (url: string) => void;
    setCurrentMode: (mode: 'control' | 'sampler' | 'midi' | 'advisor' | 'learning') => void;

    setSampleSearchEngineType: (type: 'freesound' | 'local' | 'splice_mcp') => void;
    setFreesoundApiKey: (key: string) => void;
    setLocalSamplePath: (path: string) => void;
    setMicDeviceId: (id: string) => void;
    
    // MIDI Mappings
    midiMappings: Record<string, number>;
    midiLearningModule: string | null;
    setMidiMapping: (moduleId: string, note: number) => void;
    setMidiLearningModule: (moduleId: string | null) => void;
}

export const useAppState = create<AppState>()(
    persist(
        (set) => ({
            currentBpm: 120,
            currentKey: 'C Major',
            currentTime: '0:00',
            isMicActive: false,
            isBgmPlaying: false,
            isFullscreen: false,
            statusMessage: 'SYSTEM READY',
            geminiApiKey: '',
            openaiApiKey: '',
            claudeApiKey: '',
            hfToken: '',
            voiceEngine: 'local_ollama',

            sampleEngine: 'cloud_lyria',
            transcriptionEngine: 'mt3',
            midiEngine: 'cloud_gemini',
            ollamaModel: 'gemma4:latest',
            localAiProvider: 'ollama',
            localAiBaseUrl: 'http://localhost:11434',
            currentMode: 'control',
            
            sampleSearchEngineType: 'freesound',
            freesoundApiKey: '',
            localSamplePath: '',
            
            midiMappings: {},
            midiLearningModule: null,
            language: 'ja-JP',
            micDeviceId: 'default',
            
            setLanguage: (lang) => set({ language: lang }),
            setBpm: (bpm) => set({ currentBpm: bpm }),
            setKey: (key) => set({ currentKey: key }),
            setTime: (time) => set({ currentTime: time }),
            setMicActive: (active) => set({ isMicActive: active }),
            setBgmPlaying: (playing) => set({ isBgmPlaying: playing }),
            setFullscreen: (fullscreen) => set({ isFullscreen: fullscreen }),
            setStatusMessage: (msg) => set({ statusMessage: msg }),
            setGeminiApiKey: (key) => set({ geminiApiKey: key }),
            setOpenaiApiKey: (key) => set({ openaiApiKey: key }),
            setClaudeApiKey: (key) => set({ claudeApiKey: key }),
            setHfToken: (token) => set({ hfToken: token }),
            setVoiceEngine: (engine) => set({ voiceEngine: engine }),

            setSampleEngine: (engine) => set({ sampleEngine: engine }),
            setTranscriptionEngine: (engine) => set({ transcriptionEngine: engine }),
            setMidiEngine: (engine) => set({ midiEngine: engine }),
            setOllamaModel: (model) => set({ ollamaModel: model }),
            setLocalAiProvider: (provider) => set({ localAiProvider: provider }),
            setLocalAiBaseUrl: (url) => set({ localAiBaseUrl: url }),
            setCurrentMode: (mode) => set({ currentMode: mode }),
            setSampleSearchEngineType: (type) => set({ sampleSearchEngineType: type }),
            setFreesoundApiKey: (key) => set({ freesoundApiKey: key }),
            setLocalSamplePath: (path) => set({ localSamplePath: path }),
            setMicDeviceId: (id) => set({ micDeviceId: id }),
            
            setMidiMapping: (moduleId, note) => set((state) => {
                const newMappings = { ...state.midiMappings };
                
                // Clear this note from any other modules first (ensure uniqueness)
                Object.keys(newMappings).forEach(key => {
                    if (newMappings[key] === note) {
                        delete newMappings[key];
                    }
                });
                
                // Set the new mapping
                newMappings[moduleId] = note;
                
                return { midiMappings: newMappings };
            }),
            setMidiLearningModule: (moduleId) => set({ midiLearningModule: moduleId })
        }),
        {
            name: 'cockpit-storage',
            partialize: (state) => ({ 
                language: state.language,
                geminiApiKey: state.geminiApiKey,
                openaiApiKey: state.openaiApiKey,
                claudeApiKey: state.claudeApiKey,
                hfToken: state.hfToken,
                voiceEngine: state.voiceEngine,
                localAiProvider: state.localAiProvider,
                localAiBaseUrl: state.localAiBaseUrl,

                sampleEngine: state.sampleEngine,
                transcriptionEngine: state.transcriptionEngine,
                midiEngine: state.midiEngine,
                ollamaModel: state.ollamaModel,
                sampleSearchEngineType: state.sampleSearchEngineType,
                freesoundApiKey: state.freesoundApiKey,
                localSamplePath: state.localSamplePath,
                midiMappings: state.midiMappings,
                micDeviceId: state.micDeviceId,
            }), // Only save API keys and Engine preferences
        }
    )
);

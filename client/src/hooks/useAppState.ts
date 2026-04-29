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
    voiceEngine: 'local_ollama' | 'cloud_gemini' | 'cloud_openai';
    sampleEngine: 'local_mlx' | 'cloud_lyria';
    transcriptionEngine: 'basic-pitch' | 'mt3' | 'giantmidi-piano';
    midiEngine: 'local_ollama' | 'cloud_gemini' | 'cloud_openai';
    
    // Actions
    setBpm: (bpm: number) => void;
    setKey: (key: string) => void;
    setTime: (time: string) => void;
    setMicActive: (active: boolean) => void;
    setBgmPlaying: (playing: boolean) => void;
    setFullscreen: (fullscreen: boolean) => void;
    setStatusMessage: (msg: string) => void;
    setGeminiApiKey: (key: string) => void;
    setOpenaiApiKey: (key: string) => void;
    setVoiceEngine: (engine: 'local_ollama' | 'cloud_gemini' | 'cloud_openai') => void;
    setSampleEngine: (engine: 'local_mlx' | 'cloud_lyria') => void;
    setTranscriptionEngine: (engine: 'basic-pitch' | 'mt3' | 'giantmidi-piano') => void;
    setMidiEngine: (engine: 'local_ollama' | 'cloud_gemini' | 'cloud_openai') => void;
}

export const useAppState = create<AppState>()(
    persist(
        (set) => ({
            currentBpm: 120,
            currentKey: 'C Major',
            currentTime: '1.1.1',
            isMicActive: false,
            isBgmPlaying: false,
            isFullscreen: false,
            
            statusMessage: 'SYSTEM READY',
            
            // Default configs
            geminiApiKey: '',
            openaiApiKey: '',
            voiceEngine: 'local_ollama',
            sampleEngine: 'local_mlx',
            transcriptionEngine: 'basic-pitch',
            midiEngine: 'cloud_gemini',
            
            setBpm: (bpm) => set({ currentBpm: bpm }),
            setKey: (key) => set({ currentKey: key }),
            setTime: (time) => set({ currentTime: time }),
            setMicActive: (active) => set({ isMicActive: active }),
            setBgmPlaying: (playing) => set({ isBgmPlaying: playing }),
            setFullscreen: (fullscreen) => set({ isFullscreen: fullscreen }),
            setStatusMessage: (msg) => set({ statusMessage: msg }),
            setGeminiApiKey: (key) => set({ geminiApiKey: key }),
            setOpenaiApiKey: (key) => set({ openaiApiKey: key }),
            setVoiceEngine: (engine) => set({ voiceEngine: engine }),
            setSampleEngine: (engine) => set({ sampleEngine: engine }),
            setTranscriptionEngine: (engine) => set({ transcriptionEngine: engine }),
            setMidiEngine: (engine) => set({ midiEngine: engine }),
        }),
        {
            name: 'ai-cockpit-settings', // saved to local storage under this key
            partialize: (state) => ({ 
                geminiApiKey: state.geminiApiKey,
                openaiApiKey: state.openaiApiKey,
                voiceEngine: state.voiceEngine,
                sampleEngine: state.sampleEngine,
                transcriptionEngine: state.transcriptionEngine,
                midiEngine: state.midiEngine
            }), // Only save API keys and Engine preferences
        }
    )
);

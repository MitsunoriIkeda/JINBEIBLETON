import { useState } from 'react';
import { useAppState } from './useAppState';

export const useAudioTranscription = (setIsGenerating: (val: boolean) => void) => {
    const [isDragging, setIsDragging] = useState(false);
    const { transcriptionEngine, midiEngine, geminiApiKey, currentBpm, setStatusMessage } = useAppState();

    const uploadAudioForTranscription = async (file: File) => {
        setIsGenerating(true);
        let statusText = ">>> ANALYZING AUDIO CONTENT...";
        if (transcriptionEngine === 'mt3') statusText = ">>> MT3 PRECISION ANALYZING...";
        if (transcriptionEngine === 'giantmidi-piano') statusText = ">>> GIANTMIDI-PIANO CONVERTING...";
        setStatusMessage(statusText);
        
        const formData = new FormData();
        formData.append('file', file);
        localStorage.setItem('transcriptionEngine', transcriptionEngine);
        localStorage.setItem('midiEngine', midiEngine);
        localStorage.setItem('geminiApiKey', geminiApiKey);
        formData.append('engine', transcriptionEngine);
        formData.append('bpm', currentBpm.toString());
        
        try {
            const resp = await fetch('http://localhost:8002/api/v1/transcribe', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (data.status === 'success') {
                // Handled via WebSocket in EventSubscriptions
            } else {
                setIsGenerating(false);
                setStatusMessage(`❌ FAILED: ${data.msg}`);
            }
        } catch (err) {
            setIsGenerating(false);
            setStatusMessage("❌ NETWORK ERROR");
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file && (file.type.includes("audio") || file.name.endsWith(".wav") || file.name.endsWith(".mp3"))) {
            uploadAudioForTranscription(file);
        } else {
            setStatusMessage("⚠️ INVALID FILE. PLEASE DROP AUDIO.");
        }
    };

    return {
        isDragging,
        handleDragOver,
        handleDragLeave,
        handleDrop
    };
};

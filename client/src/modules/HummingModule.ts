import { eventBus, EVENTS } from '../utils/EventBus';
import { useAppState } from '../hooks/useAppState';

export class HummingModule {
    private mediaRecorder: MediaRecorder | null = null;
    private audioChunks: Blob[] = [];
    private isRecording = false;

    constructor() {
        eventBus.on(EVENTS.TRIGGER_HUMMING, () => this.toggle());
    }

    async toggle() {
        if (this.isRecording) {
            this.stopRecording();
        } else {
            await this.startRecording();
        }
    }

    async startRecording() {
        try {
            eventBus.emit(EVENTS.STATUS_UPDATE, "🎤 INITIALIZING MIC...");
            
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];

            this.mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    this.audioChunks.push(event.data);
                }
            };

            this.mediaRecorder.onstop = () => {
                this.processAudio();
                // Clean up the stream
                stream.getTracks().forEach(track => track.stop());
            };

            this.mediaRecorder.start();
            this.isRecording = true;
            eventBus.emit(EVENTS.STATUS_UPDATE, "🐶 RECORDING HUMMING...");
            eventBus.emit(EVENTS.HUMMING_STARTED);
            
        } catch (err) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ ERROR: MIC ACCESS DENIED");
            console.error(err);
        }
    }

    stopRecording() {
        if (this.mediaRecorder && this.isRecording) {
            this.mediaRecorder.stop();
            this.isRecording = false;
            eventBus.emit(EVENTS.HUMMING_STOPPED);
        }
    }

    async processAudio() {
        eventBus.emit(EVENTS.STATUS_UPDATE, ">>> ANALYZING HUMMING...");
        
        // Ensure UI stays in generating mode
        eventBus.emit(EVENTS.TRIGGER_SAMPLE_GEN);

        try {
            // 1. Create WebM blob from chunks
            const webmBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
            
            // 2. Decode WebM to AudioBuffer using AudioContext
            const arrayBuffer = await webmBlob.arrayBuffer();
            const audioCtx = new AudioContext();
            const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
            
            // 3. Convert AudioBuffer to WAV Blob
            const wavBlob = this.audioBufferToWav(audioBuffer);
            const file = new File([wavBlob], `humming_${Date.now()}.wav`, { type: 'audio/wav' });

            const state = useAppState.getState();
            const formData = new FormData();
            formData.append('file', file);
            formData.append('engine', state.transcriptionEngine);
            formData.append('bpm', state.currentBpm.toString());
            formData.append('is_humming', 'true');

            const resp = await fetch('http://localhost:8002/api/v1/transcribe', {
                method: 'POST',
                body: formData
            });
            const data = await resp.json();
            if (data.status === 'success') {
                // Success is handled by WebSocket 'TRANSCRIPTION_FINISHED'
            } else {
                eventBus.emit(EVENTS.STATUS_UPDATE, `❌ FAILED: ${data.msg}`);
            }
        } catch (err) {
            eventBus.emit(EVENTS.STATUS_UPDATE, "❌ CONVERSION OR NETWORK ERROR");
            console.error(err);
        }
    }

    // Helper: Converts AudioBuffer to a valid WAV Blob
    private audioBufferToWav(buffer: AudioBuffer): Blob {
        const numOfChan = buffer.numberOfChannels;
        const length = buffer.length * numOfChan * 2 + 44;
        const bufferData = new ArrayBuffer(length);
        const view = new DataView(bufferData);
        let offset = 0;

        const writeString = (s: string) => {
            for (let i = 0; i < s.length; i++) {
                view.setUint8(offset + i, s.charCodeAt(i));
            }
            offset += s.length;
        };

        writeString('RIFF');
        view.setUint32(offset, 36 + buffer.length * numOfChan * 2, true); offset += 4;
        writeString('WAVE');
        writeString('fmt ');
        view.setUint32(offset, 16, true); offset += 4; // Subchunk1Size
        view.setUint16(offset, 1, true); offset += 2; // AudioFormat (PCM)
        view.setUint16(offset, numOfChan, true); offset += 2;
        view.setUint32(offset, buffer.sampleRate, true); offset += 4;
        view.setUint32(offset, buffer.sampleRate * 2 * numOfChan, true); offset += 4; // ByteRate
        view.setUint16(offset, numOfChan * 2, true); offset += 2; // BlockAlign
        view.setUint16(offset, 16, true); offset += 2; // BitsPerSample
        writeString('data');
        view.setUint32(offset, buffer.length * numOfChan * 2, true); offset += 4;

        for (let i = 0; i < buffer.numberOfChannels; i++) {
            const channel = buffer.getChannelData(i);
            let sampleOffset = offset + i * 2;
            for (let j = 0; j < buffer.length; j++) {
                let sample = Math.max(-1, Math.min(1, channel[j]));
                sample = (0.5 + sample < 0 ? sample * 32768 : sample * 32767) | 0;
                view.setInt16(sampleOffset, sample, true);
                sampleOffset += numOfChan * 2;
            }
        }

        return new Blob([view], { type: 'audio/wav' });
    }
}

export const hummingModule = new HummingModule();

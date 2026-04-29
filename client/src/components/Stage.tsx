import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { eventBus, EVENTS } from '../utils/EventBus';

interface StageProps {
    voiceText: string | null;
    setVoiceText: (val: string | null) => void;
    setIsSuccess: (val: boolean) => void;
    activeModule: string | null;
    isListening: boolean;
    activeVoiceMode: string | null;
    latestSample: any;
    latestMidi: any;
    isPoofing: boolean;
    isPreviewPlaying: boolean;
    setIsPreviewPlaying: (val: boolean) => void;
    previewAudioRef: React.RefObject<HTMLAudioElement | null>;
    activateModule: (id: string) => void;
    triggerShortVibration: (id: string, durationMs?: number) => void;
    isBgmPlaying: boolean;
    toggleBgm: () => void;
    currentBpm: number;
}

export const Stage: React.FC<StageProps> = ({
    voiceText, setVoiceText, setIsSuccess,
    activeModule, isListening, activeVoiceMode,
    latestSample, latestMidi, isPoofing,
    isPreviewPlaying, setIsPreviewPlaying, previewAudioRef,
    activateModule, triggerShortVibration,
    isBgmPlaying, toggleBgm, currentBpm
}) => {
    const [hoveredModule, setHoveredModule] = useState<string | null>(null);

    const beatDuration = 60 / currentBpm;

    const glitterProps = {
        opacity: [1, 0.4, 1, 0.2, 0.9, 1],
        scale: [1, 1.03, 0.98, 1.02, 1]
    };
    const blinkProps = { opacity: [1, 0.4, 1] };

    const getModuleStyle = (id: string, baseZ: number) => {
        const isHovered = hoveredModule === id;
        return {
            zIndex: isHovered ? 85 : baseZ,
            transform: isHovered ? 'scale(1.03)' : 'scale(1)',
            filter: isHovered ? 'brightness(1.5)' : 'brightness(1)',
            willChange: 'transform'
        };
    };

    return (
        <>
            <img src="/assets/bg-2.png" className="full-layer no-click" alt="Background" />

            <AnimatePresence>
                {voiceText && (
                    <motion.div 
                        className="speech-bubble-container"
                        initial={{ opacity: 0, scale: 0.8, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                    >
                        <div className="speech-bubble">
                            {voiceText}
                        </div>
                        <div className="dismiss-bubble-btn" onClick={() => { setVoiceText(null); setIsSuccess(false); }}>
                            🦴
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* --- VISUALS --- */}
            <motion.img src="/assets/car-yellow.png" className={`full-layer no-click hover-expand ${activeModule === 'yellow' ? 'vibrate-engine' : ''} ${isListening && activeModule === 'yellow' ? 'generating-glow' : ''}`} style={getModuleStyle('yellow', 21)} />
            
            {/* --- USER-PROVIDED CASSETTE (FULL LAYER) --- */}
            <AnimatePresence>
                {latestSample && (
                    <motion.div 
                        className={`sample-slot ${isPoofing ? 'poof-dismissing' : ''}`}
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                    >
                        <motion.img 
                            src="/assets/cassette.png" 
                            className={`cassette-hero ${isPreviewPlaying ? 'shiver-active' : ''} ${hoveredModule === 'cassette' ? 'cassette-hovered' : ''}`}
                            alt="Cassette Tape"
                        />
                        <div 
                            className="cassette-hitbox"
                            onMouseEnter={() => setHoveredModule('cassette')}
                            onMouseLeave={() => setHoveredModule(null)}
                            onClick={() => {
                                if (previewAudioRef.current) {
                                    if (isPreviewPlaying) {
                                        previewAudioRef.current.pause();
                                        setIsPreviewPlaying(false);
                                    } else {
                                        previewAudioRef.current.currentTime = 0;
                                        previewAudioRef.current.play();
                                        setIsPreviewPlaying(true);
                                    }
                                }
                            }}
                        />
                        <audio ref={previewAudioRef} src={latestSample.file} onEnded={() => setIsPreviewPlaying(false)} />
                        <AnimatePresence>
                            {isPreviewPlaying && (
                                <motion.div 
                                    className="download-row"
                                    initial={{ opacity: 0, y: -10 }}
                                    animate={{ opacity: 1, y: 0 }}
                                    exit={{ opacity: 0, y: -10 }}
                                >
                                    <a href={latestSample.file} download={`ai_loop_${Date.now()}.wav`} className="download-btn" style={{ textDecoration: 'none' }}>
                                        <span>📁 DOWNLOAD</span>
                                    </a>
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* --- MIDI TRANSCRIPTION RESULT ICON --- */}
            <AnimatePresence>
                {latestMidi && (
                    <motion.div 
                        className="midi-slot"
                        initial={{ scale: 0, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        exit={{ scale: 0, opacity: 0 }}
                    >
                        <div className="midi-download-row">
                            <a href={latestMidi.file} download={`transcribed_${Date.now()}.mid`} className="download-btn" style={{ textDecoration: 'none', borderColor: '#00ffff' }}>
                                <span>🎹 DOWNLOAD MIDI</span>
                            </a>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.img src="/assets/car-red.png" className={`full-layer no-click hover-expand ${activeModule === 'red' ? 'vibrate-engine' : ''} ${isListening && activeVoiceMode === 'midi' ? 'mic-active generating-glow' : ''}`} style={getModuleStyle('red', 22)} />
            <motion.img src="/assets/car-blue.png" className={`full-layer no-click hover-expand ${activeModule === 'blue' ? 'vibrate-engine' : ''} ${isListening && activeVoiceMode === 'humming' ? 'mic-active generating-glow' : ''}`} style={getModuleStyle('blue', 23)} />
            <motion.img src="/assets/car-green.png" className={`full-layer no-click hover-expand ${activeModule === 'green' ? 'vibrate-engine' : ''}`} style={getModuleStyle('green', 24)} />
            <motion.img src="/assets/tractor.png" className={`full-layer no-click hover-expand ${activeModule === 'tractor' ? 'vibrate-engine' : ''}`} style={getModuleStyle('tractor', 25)} />
            <motion.img src="/assets/signboard-yellow.png" className={`full-layer no-click hover-expand ${activeModule === 'sign' ? 'vibrate-engine' : ''}`} style={getModuleStyle('sign', 26)} />
            <motion.img src="/assets/title.png" className={`full-layer no-click hover-expand ${activeModule === 'title' ? 'vibrate-engine' : ''} ${(isListening && activeVoiceMode === 'control') ? 'mic-active generating-glow' : ''}`} alt="Title" style={getModuleStyle('title', 20)} />
            <motion.img src="/assets/plane-pink.png" className={`full-layer no-click hover-expand ${activeModule === 'pink' ? 'vibrate-engine' : ''}`} style={getModuleStyle('pink', 30)} animate={{ y: [0, -10, 0] }} transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }} />
            <motion.img src="/assets/plane-green.png" className={`full-layer no-click hover-expand ${activeModule === 'p-green' ? 'vibrate-engine' : ''}`} style={getModuleStyle('p-green', 31)} animate={{ y: [0, -5, 0] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }} />
            
            <motion.img 
                src="/assets/dog.png" 
                className={`full-layer no-click ${activeModule === 'dog' ? 'vibrate-engine' : ''}`} 
                style={{ ...getModuleStyle('dog', 85), transformOrigin: 'calc(76.5% - 20px) 67.5%' }} 
                animate={isBgmPlaying ? { 
                    rotate: [-8, 8, -8],
                    scaleY: [1, 1.03, 1],
                    y: [0, -6, 0]
                } : { rotate: 0, scaleY: 1, y: 0 }}
                transition={isBgmPlaying ? { 
                    duration: beatDuration * 2, 
                    repeat: Infinity, 
                    ease: "easeInOut" 
                } : { duration: 0.5 }} 
            />
            <motion.img src="/assets/start.png.png" className="full-layer no-click" style={getModuleStyle('start', 60)} animate={isBgmPlaying ? glitterProps : blinkProps} transition={{ duration: isBgmPlaying ? 0.2 : 1.5, repeat: Infinity, ease: "linear" }} />

            {/* --- PRECISION HITBOXES --- */}
            <div className="hitbox hitbox-yellow" onMouseEnter={() => setHoveredModule('yellow')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { activateModule('yellow'); eventBus.emit(EVENTS.TRIGGER_VOICE, 'sampler'); }}></div>
            <div className="hitbox hitbox-red" onMouseEnter={() => setHoveredModule('red')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { activateModule('red'); eventBus.emit(EVENTS.TRIGGER_VOICE, 'midi'); }}></div>
            <div className="hitbox hitbox-blue" onMouseEnter={() => setHoveredModule('blue')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { activateModule('blue'); eventBus.emit(EVENTS.TRIGGER_HUMMING); }}></div>
            <div className="hitbox hitbox-green" onMouseEnter={() => setHoveredModule('green')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { activateModule('green'); eventBus.emit(EVENTS.TRIGGER_SOUND_PALETTE); }}></div>
            <div className="hitbox hitbox-tractor" onMouseEnter={() => setHoveredModule('tractor')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { activateModule('tractor'); eventBus.emit(EVENTS.TRIGGER_STRUCTURE_ANALYZE); }}></div>
            <div className="hitbox hitbox-plane-pink" onMouseEnter={() => setHoveredModule('pink')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { activateModule('pink'); eventBus.emit(EVENTS.TRIGGER_READ_MIDI); }}></div>
            <div className="hitbox hitbox-plane-green" onMouseEnter={() => setHoveredModule('p-green')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { triggerShortVibration('p-green'); eventBus.emit(EVENTS.TRIGGER_SYNC); }}></div>
            <div className="hitbox hitbox-dog" onMouseEnter={() => setHoveredModule('dog')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { 
                activateModule('dog'); 
                eventBus.emit(EVENTS.TRIGGER_VOICE, 'advisor'); 
            }}></div>
            <div className="hitbox hitbox-title" onMouseEnter={() => setHoveredModule('title')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { activateModule('title'); eventBus.emit(EVENTS.TRIGGER_VOICE, 'control'); }}></div>
            <div className="hitbox hitbox-sign-yellow" onMouseEnter={() => setHoveredModule('sign')} onMouseLeave={() => setHoveredModule(null)} onClick={() => { 
                triggerShortVibration('sign'); 
                if (!document.fullscreenElement) {
                    document.documentElement.requestFullscreen().catch(e => console.error(e));
                } else {
                    if (document.exitFullscreen) document.exitFullscreen();
                }
            }}></div>
            <div className="start-hitbox" onMouseEnter={() => setHoveredModule('start')} onMouseLeave={() => setHoveredModule(null)} onClick={toggleBgm}></div>
        </>
    );
};

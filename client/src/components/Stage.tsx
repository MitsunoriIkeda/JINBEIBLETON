declare const require: any;
import React, { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { eventBus, EVENTS } from '../utils/EventBus';
import { useAppState } from '../hooks/useAppState';


interface StageProps {
    voiceText: string | null;
    setVoiceText: (val: string | null) => void;
    setIsSuccess: (val: boolean) => void;
    activeModule: string | null;
    isListening: boolean;
    isGenerating: boolean;
    isMixing: boolean;
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
    handleCancelAll: () => void;
    onOpenConfig: () => void;
}

export const Stage: React.FC<StageProps> = ({
    activeModule, isListening, isGenerating, isMixing, activeVoiceMode,
    latestSample, latestMidi, isPoofing,
    isPreviewPlaying, setIsPreviewPlaying, previewAudioRef,
    activateModule, triggerShortVibration,
    isBgmPlaying, toggleBgm, currentBpm,
    handleCancelAll, onOpenConfig
}) => {
    const { statusMessage, setCurrentMode, midiLearningModule, setMidiLearningModule, setStatusMessage } = useAppState();
    const [hoveredModule, setHoveredModule] = useState<string | null>(null);
    const [pressingModule, setPressingModule] = useState<string | null>(null);

    const MODULE_LABELS: Record<string, string> = {
        'yellow': 'SAMPLE GENERATE',
        'red': 'MIDI GENERATE',
        'blue': 'HUMMING',
        'green': 'CONFIG',
        'fast': 'CHORD-TO-MELODY',
        'tractor': 'LEARNING',
        'pink': 'CANCEL',
        'p-green': 'SYNC',
        'dog': 'JINBEI ADVISOR',
        'sign': 'FULLSCREEN',
        'cassette': 'PREVIEW',
        'midi-key': 'DOWNLOAD',
        'title': ''
    };

    const MODULE_POSITIONS: Record<string, { top: string, left: string }> = {
        'yellow': { top: '56%', left: '22.5%' },
        'red': { top: '56%', left: '73%' }, /* Shifted left to prevent clipping */
        'blue': { top: '56%', left: '47%' },
        'green': { top: '44%', left: '31.2%' },
        'fast': { top: '50%', left: '75%' }, /* Further left from 82% */
        'tractor': { top: '41%', left: '9%' },
        'pink': { top: '18%', left: '80%' }, /* Shifted left */
        'p-green': { top: '17%', left: '14%' },
        'dog': { top: '56%', left: '73%' }, /* Shifted left */
        'sign': { top: '42%', left: '72%' },
        'cassette': { top: '48%', left: '33%' },
        'midi-key': { top: '48%', left: '48%' }
    };

    const pressTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
    const longPressFired = useRef(false);

    const handlePointerDown = (moduleId: string) => {
        longPressFired.current = false;
        setPressingModule(moduleId);
        if (pressTimerRef.current) clearTimeout(pressTimerRef.current);
        pressTimerRef.current = setTimeout(() => {
            longPressFired.current = true;
            setMidiLearningModule(moduleId);
            setPressingModule(null);
            if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
        }, 2000);
    };

    const handlePointerUp = (moduleId: string, onClick: () => void) => {
        if (pressTimerRef.current) {
            clearTimeout(pressTimerRef.current);
            pressTimerRef.current = null;
        }
        setPressingModule(null);
        if (!longPressFired.current && midiLearningModule !== moduleId) {
            onClick();
        }
    };

    const handlePointerLeave = () => {
        if (pressTimerRef.current) {
            clearTimeout(pressTimerRef.current);
            pressTimerRef.current = null;
        }
        setPressingModule(null);
        setHoveredModule(null);
    };

    const bgmBeatDuration = 60 / 160; 
    const mixBeatDuration = 60 / currentBpm;
    const currentDuration = isMixing ? (mixBeatDuration * 2) : (bgmBeatDuration * 2);

    // Helper for module classes
    const getModuleClass = (id: string, baseClass: string = '') => {
        let cls = `full-layer no-click hover-expand ${baseClass}`;
        if (activeModule === id) cls += ' vibrate-engine';
        if (pressingModule === id) cls += ' midi-learning-press';
        if (midiLearningModule === id) cls += ' midi-learning-active';
        return cls;
    };

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

    const shouldVibrateAll = isGenerating && (
        (statusMessage.toUpperCase().includes("ANALYZING") && !statusMessage.toUpperCase().includes("COMMAND")) || 
        statusMessage.toUpperCase().includes("COMPOSING") || 
        statusMessage.toUpperCase().includes("MIDI") || 
        statusMessage.toUpperCase().includes("SCANNING") ||
        statusMessage.toUpperCase().includes("AUDIT") ||
        statusMessage.toUpperCase().includes("WORKING") ||
        isMixing
    );
    
    // --- MIX METER COMPONENT REMOVED FROM STAGE (NOW IN CONSOLE) ---

    const handleDragStart = (e: React.DragEvent, filePath: string) => {
        e.preventDefault();
        if ((window as any).require) {
            try {
                const { ipcRenderer } = (window as any).require('electron');
                ipcRenderer.send('ondragstart', filePath);
            } catch (err) {
                console.error("Native drag start failed:", err);
            }
        }
    };

    return (
        <>
            {/* --- FLOATING LABELS (FIXED PER BUTTON) --- */}
            <AnimatePresence>
                {hoveredModule && MODULE_LABELS[hoveredModule] && MODULE_POSITIONS[hoveredModule] && (
                    <motion.div 
                        className="floating-label"
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        style={{ 
                            top: MODULE_POSITIONS[hoveredModule].top, 
                            left: MODULE_POSITIONS[hoveredModule].left 
                        }}
                    >
                        {MODULE_LABELS[hoveredModule]}
                    </motion.div>
                )}
            </AnimatePresence>

            <img 
                src="./assets/bg-2.png" 
                className="full-layer" 
                style={{ zIndex: 1, pointerEvents: (midiLearningModule || activeModule === 'tractor') ? 'auto' : 'none' }} 
                alt="Background" 
                onClick={() => {
                    if (midiLearningModule) {
                        setMidiLearningModule(null);
                        setCurrentMode('control');
                        setStatusMessage("LEARNING CANCELLED");
                    }
                }}
            />

            {/* Speech bubble moved to App.tsx for top-level rendering */}

            {/* --- VISUALS --- */}
            <motion.img src="./assets/car-yellow.png" className={`full-layer no-click hover-expand ${activeModule === 'yellow' ? 'vibrate-engine' : ''} ${isListening && activeModule === 'yellow' ? 'generating-glow' : ''}`} style={getModuleStyle('yellow', 21)} />
            
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
                            src="./assets/cassette.png" 
                            className={`cassette-hero ${isPreviewPlaying ? 'shiver-active' : ''} ${hoveredModule === 'cassette' ? 'cassette-hovered' : ''}`}
                            alt="Cassette Tape"
                        />
                        <div 
                            className="cassette-hitbox"
                            draggable="true"
                            onDragStart={(e) => handleDragStart(e, latestSample.file)}
                            onMouseEnter={(e) => {
                                e.stopPropagation();
                                setHoveredModule('cassette');
                            }}
                            onMouseLeave={() => setHoveredModule(null)}
                            onClick={(e) => {
                                e.stopPropagation();
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
                            <div 
                                className="midi-hitbox"
                                draggable="true"
                                onDragStart={(e) => handleDragStart(e, latestMidi.file)}
                                onClick={() => {
                                    const link = document.createElement('a');
                                    link.href = latestMidi.file;
                                    link.download = `transcribed_${Date.now()}.mid`;
                                    link.click();
                                }}
                                onMouseEnter={() => setHoveredModule('midi-key')}
                                onMouseLeave={() => setHoveredModule(null)}
                            />
                            <img 
                                src="./assets/midi-key.png" 
                                className={`midi-icon-hero ${hoveredModule === 'midi-key' ? 'midi-hero-hovered' : ''}`} 
                                alt="MIDI Key"
                            />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            <motion.img src="./assets/car-yellow.png" className={getModuleClass('yellow', `${isListening && activeVoiceMode === 'sampler' ? 'mic-active generating-glow' : ''} ${shouldVibrateAll ? 'vibrate-engine' : ''}`)} style={getModuleStyle('yellow', 21)} />
            <motion.img src="./assets/car-red.png" className={getModuleClass('red', `${isListening && activeVoiceMode === 'midi' ? 'mic-active generating-glow' : ''} ${shouldVibrateAll ? 'vibrate-engine' : ''}`)} style={getModuleStyle('red', 22)} />
            <motion.img src="./assets/car-blue.png" className={getModuleClass('blue', `${isListening && activeVoiceMode === 'humming' ? 'mic-active generating-glow' : ''} ${shouldVibrateAll ? 'vibrate-engine' : ''}`)} style={getModuleStyle('blue', 23)} />
            <motion.img src="./assets/car-green.png" className={getModuleClass('green', `${shouldVibrateAll ? 'vibrate-engine' : ''}`)} style={getModuleStyle('green', 24)} />

            <motion.img src="./assets/tractor.png" className={getModuleClass('tractor', `${shouldVibrateAll ? 'vibrate-engine' : ''}`)} style={getModuleStyle('tractor', 25)} />
            <motion.img src="./assets/signboard-yellow.png" className={getModuleClass('sign')} style={getModuleStyle('sign', 26)} />
            <motion.img src="./assets/title.png" className={getModuleClass('title', `${(isListening && activeVoiceMode === 'control') ? 'mic-active generating-glow' : ''}`)} alt="Title" style={getModuleStyle('title', 20)} />
            <motion.img src="./assets/plane-pink.png" className={getModuleClass('pink')} style={getModuleStyle('pink', 30)} animate={{ y: [0, -10, 0] }} transition={{ duration: 4.5, repeat: Infinity, ease: "easeInOut" }} />
            <motion.img src="./assets/plane-green.png" className={getModuleClass('p-green')} style={getModuleStyle('p-green', 31)} animate={{ y: [0, -5, 0] }} transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }} />
            
            <motion.img 
                key={isMixing ? `dog-mix-${currentBpm}` : `dog-bgm`}
                src="./assets/dog.png" 
                className={getModuleClass('dog')} 
                style={{ ...getModuleStyle('dog', 85), transformOrigin: 'calc(76.5% - 20px) 67.5%' }} 
                animate={isBgmPlaying ? { 
                    rotate: isMixing ? [-12, 12, -12] : [-8, 8, -8],
                    scaleY: [1, 1.05, 1],
                    y: [0, -8, -0]
                } : { rotate: 0, scaleY: 1, y: 0 }}
                transition={isBgmPlaying ? { 
                    duration: currentDuration, 
                    repeat: Infinity, 
                    ease: "easeInOut" 
                } : { duration: 0.5 }} 
            />
            <motion.img 
                key={isMixing ? `start-mix-${currentBpm}` : `start-bgm`}
                src="./assets/start.png" 
                className="full-layer no-click" 
                style={getModuleStyle('start', 60)} 
                animate={isBgmPlaying ? glitterProps : blinkProps} 
                transition={{ 
                    duration: isBgmPlaying ? (isMixing ? mixBeatDuration / 2 : bgmBeatDuration / 2) : 1.5, 
                    repeat: Infinity, 
                    ease: isBgmPlaying ? "linear" : "easeInOut" 
                }} 
            />
            <motion.img src="./assets/car-fast.png" className={`full-layer no-click hover-expand ${shouldVibrateAll ? 'vibrate-engine' : ''}`} style={getModuleStyle('fast', 80)} />

            {/* --- PRECISION HITBOXES --- */}
            <div className="hitbox hitbox-yellow" 
                onMouseEnter={() => setHoveredModule('yellow')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('yellow')}
                onPointerUp={() => handlePointerUp('yellow', () => { setCurrentMode('sampler'); activateModule('yellow'); eventBus.emit(EVENTS.TRIGGER_VOICE, 'sampler'); })}></div>
            
            <div className="hitbox hitbox-red" 
                onMouseEnter={() => setHoveredModule('red')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('red')}
                onPointerUp={() => handlePointerUp('red', () => { setCurrentMode('midi'); activateModule('red'); eventBus.emit(EVENTS.TRIGGER_VOICE, 'midi'); })}></div>
            
            <div className="hitbox hitbox-blue" 
                onMouseEnter={() => setHoveredModule('blue')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('blue')}
                onPointerUp={() => handlePointerUp('blue', () => { activateModule('blue'); eventBus.emit(EVENTS.TRIGGER_HUMMING); })}></div>

            <div className="hitbox hitbox-green" 
                onMouseEnter={() => setHoveredModule('green')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('green')}
                onPointerUp={() => handlePointerUp('green', () => { 
                    triggerShortVibration('green', 200);
                    onOpenConfig(); 
                })}></div>

            <div className="hitbox hitbox-fast" 
                onMouseEnter={() => setHoveredModule('fast')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('fast')}
                onPointerUp={() => handlePointerUp('fast', () => { activateModule('fast'); eventBus.emit(EVENTS.TRIGGER_CHORD_MELODY); })}></div>

            
            <div className="hitbox hitbox-tractor" 
                onMouseEnter={() => setHoveredModule('tractor')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('tractor')}
                onPointerUp={() => handlePointerUp('tractor', () => { 
                    activateModule('tractor'); 
                    setCurrentMode('learning');
                    eventBus.emit(EVENTS.TRIGGER_VOICE, 'learning'); 
                })}></div>
            
            <div className="hitbox hitbox-plane-pink" 
                onMouseEnter={() => setHoveredModule('pink')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('pink')}
                onPointerUp={() => handlePointerUp('pink', () => { 
                    triggerShortVibration('pink', 200);
                    handleCancelAll(); 
                })}></div>
            
            <div className="hitbox hitbox-plane-green" 
                onMouseEnter={() => setHoveredModule('p-green')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('p-green')}
                onPointerUp={() => handlePointerUp('p-green', () => { triggerShortVibration('p-green'); eventBus.emit(EVENTS.TRIGGER_SYNC); })}></div>
            
            <div className="hitbox hitbox-dog" 
                onMouseEnter={() => setHoveredModule('dog')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('dog')}
                onPointerUp={() => handlePointerUp('dog', () => { 
                    setCurrentMode('advisor');
                    activateModule('dog'); 
                    eventBus.emit(EVENTS.TRIGGER_VOICE, 'advisor'); 
                })}></div>
            
            <div className="hitbox hitbox-title" 
                onMouseEnter={() => setHoveredModule('title')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('title')}
                onPointerUp={() => handlePointerUp('title', () => { setCurrentMode('control'); activateModule('title'); eventBus.emit(EVENTS.TRIGGER_VOICE, 'control'); })}></div>
            
            <div className="hitbox hitbox-sign-yellow" 
                onMouseEnter={() => setHoveredModule('sign')} 
                onPointerLeave={handlePointerLeave} 
                onPointerDown={() => handlePointerDown('sign')}
                onPointerUp={() => handlePointerUp('sign', () => { 
                    triggerShortVibration('sign'); 
                    if ((window as any).require) {
                        try {
                            const { ipcRenderer } = (window as any).require('electron');
                            ipcRenderer.send('toggle-fullscreen');
                        } catch (err) {
                            console.error("Native fullscreen toggle failed:", err);
                        }
                    } else {
                        if (!document.fullscreenElement) {
                            document.documentElement.requestFullscreen().catch(() => {});
                        } else {
                            document.exitFullscreen().catch(() => {});
                        }
                    }
                })}></div>

            <div className="start-hitbox" onMouseEnter={() => setHoveredModule('start')} onMouseLeave={() => setHoveredModule(null)} onClick={toggleBgm}></div>
        </>
    );
};

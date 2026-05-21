import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAppState } from '../hooks/useAppState';

interface DropZoneOverlayProps {
    isDragging: boolean;
}

export const DropZoneOverlay: React.FC<DropZoneOverlayProps> = ({ isDragging }) => {
    const { transcriptionEngine } = useAppState();

    return (
        <AnimatePresence>
            {isDragging && (
                <motion.div 
                    className="drop-zone-overlay"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                >
                    <img src="./assets/dog.png" style={{ width: '15vw', filter: transcriptionEngine === 'mt3' ? 'hue-rotate(280deg) brightness(1.5)' : 'hue-rotate(180deg)' }} className="floating" alt="Drag Dog" />
                    <h2 className="retro-text">DROP AUDIO FOR {transcriptionEngine.toUpperCase()} TRANSCRIPTION</h2>
                    {transcriptionEngine === 'mt3' && <p className="retro-text label-small" style={{ color: '#ff00ff', marginTop: '10px' }}>{">>>"} PRECISION MODE ACTIVE (MT3)</p>}
                    {transcriptionEngine === 'giantmidi-piano' && <p className="retro-text label-small" style={{ color: '#ffff00', marginTop: '10px' }}>{">>>"} PIANO SPECIALIZED MODE (GIANTMIDI)</p>}
                </motion.div>
            )}
        </AnimatePresence>
    );
};

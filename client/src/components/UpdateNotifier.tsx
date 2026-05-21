import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface UpdateMetadata {
    version: string;
    download_url: string;
    release_notes?: string;
}

const CURRENT_VERSION = "1.0.0"; // Hardcoded current app version
const UPDATE_CHECK_URL = "https://raw.githubusercontent.com/MitsunoriIkeda/for-ableton-AI-controller/main/version.json";

export const UpdateNotifier: React.FC = () => {
    const [updateInfo, setUpdateInfo] = useState<UpdateMetadata | null>(null);
    const [isVisible, setIsVisible] = useState(false);

    useEffect(() => {
        // Run after 3 seconds delay to avoid cluttering splash screen / launch flow
        const timer = setTimeout(() => {
            checkUpdates();
        }, 3000);
        return () => clearTimeout(timer);
    }, []);

    const parseVersion = (v: string): number[] => {
        return v.replace(/[^0-9.]/g, '').split('.').map(Number);
    };

    const isNewerVersion = (latest: string, current: string): boolean => {
        const lParts = parseVersion(latest);
        const cParts = parseVersion(current);
        
        for (let i = 0; i < Math.max(lParts.length, cParts.length); i++) {
            const lVal = lParts[i] || 0;
            const cVal = cParts[i] || 0;
            if (lVal > cVal) return true;
            if (lVal < cVal) return false;
        }
        return false;
    };

    const checkUpdates = async () => {
        try {
            const response = await fetch(UPDATE_CHECK_URL, { cache: 'no-store' });
            if (response.ok) {
                const data: UpdateMetadata = await response.json();
                if (data && data.version && isNewerVersion(data.version, CURRENT_VERSION)) {
                    console.log(`✨ [UPDATE] New version v${data.version} available! Current: v${CURRENT_VERSION}`);
                    setUpdateInfo(data);
                    setIsVisible(true);
                }
            }
        } catch (error) {
            // Silently ignore network failures (offline mode)
            console.log("ℹ️ [UPDATE CHECK] Offline or raw.githubusercontent.com unreachable.");
        }
    };

    const handleDownload = () => {
        if (!updateInfo) return;
        window.open(updateInfo.download_url, '_blank');
        setIsVisible(false);
    };

    return (
        <AnimatePresence>
            {isVisible && updateInfo && (
                <motion.div 
                    className="update-toast"
                    initial={{ opacity: 0, y: -50, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -20, scale: 0.9 }}
                    transition={{ type: "spring", stiffness: 300, damping: 25 }}
                >
                    <div className="update-icon-glow">✨</div>
                    <div className="update-content">
                        <div className="update-header retro-text">NEW VERSION AVAILABLE</div>
                        <div className="update-version retro-text">v{updateInfo.version} <span className="current-ver-tag">({CURRENT_VERSION}➔)</span></div>
                        {updateInfo.release_notes && (
                            <div className="update-notes font-pnm">{updateInfo.release_notes}</div>
                        )}
                        <div className="update-actions">
                            <button className="update-btn download-btn retro-text" onClick={handleDownload}>
                                DOWNLOAD NOW
                            </button>
                            <button className="update-btn dismiss-btn retro-text" onClick={() => setIsVisible(false)}>
                                LATER
                            </button>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
};

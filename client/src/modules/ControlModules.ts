import { eventBus } from '../utils/EventBus';

/**
 * B. Sound Palette Module (car-green.png)
 * Handles preset selection and parameter transmission to Ableton VSTs.
 */
export const SoundPaletteModule = {
    sendPreset: async (presetName: string) => {
        console.log(`[SoundPalette] Applying preset: ${presetName}`);
        
        // Pseudo-logic for OSC transmission via server
        const response = await fetch('http://localhost:8000/send_osc', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                address: '/palette/load',
                args: [presetName]
            })
        });

        if (response.ok) {
            console.log(`[SoundPalette] Preset ${presetName} loaded successfully`);
            eventBus.emit('OSC_MESSAGE' as any, { status: 'success', module: 'palette' });
        }
    }
};

/**
 * C. ControllerModule (title.png)
 * Handles voice-driven parameter control.
 */
export const ControllerModule = {
    handleVoiceIntent: (intent: { param: string, value: number }) => {
        console.log(`[Controller] Voice command: Set ${intent.param} to ${intent.value}`);
        
        // Send OSC to Ableton
        fetch('http://localhost:8000/send_osc', {
            method: 'POST',
            body: JSON.stringify({
                address: `/live/device/param/${intent.param}`,
                args: [intent.value]
            })
        });
    }
};

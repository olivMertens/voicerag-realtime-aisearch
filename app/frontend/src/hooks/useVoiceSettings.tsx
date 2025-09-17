import { useState, useEffect, useCallback } from 'react';

const TEXT_VOICE_STORAGE_KEY = 'voicerag-text-voice-preference';
const REALTIME_VOICE_STORAGE_KEY = 'voicerag-realtime-voice-preference';
const DEFAULT_VOICE = 'alloy';

export function useVoiceSettings() {
    const [selectedTextVoice, setSelectedTextVoice] = useState<string>(DEFAULT_VOICE);
    const [selectedRealtimeVoice, setSelectedRealtimeVoice] = useState<string>(DEFAULT_VOICE);

    // Load voice preferences from localStorage
    useEffect(() => {
        try {
            const savedTextVoice = localStorage.getItem(TEXT_VOICE_STORAGE_KEY);
            if (savedTextVoice) {
                setSelectedTextVoice(savedTextVoice);
            }

            const savedRealtimeVoice = localStorage.getItem(REALTIME_VOICE_STORAGE_KEY);
            if (savedRealtimeVoice) {
                setSelectedRealtimeVoice(savedRealtimeVoice);
            }
        } catch (error) {
            console.warn('Failed to load voice preferences:', error);
        }
    }, []);

    // Update text chat voice preference
    const updateTextVoice = useCallback(async (voice: string) => {
        try {
            setSelectedTextVoice(voice);
            localStorage.setItem(TEXT_VOICE_STORAGE_KEY, voice);
            
            // Notify backend of text chat voice change
            await fetch('/api/voice-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    voice, 
                    mode: 'text' 
                })
            });
            
            console.log(`🎵 Text chat voice updated to: ${voice}`);
        } catch (error) {
            console.warn('Failed to update text chat voice preference:', error);
        }
    }, []);

    // Update realtime voice preference
    const updateRealtimeVoice = useCallback(async (voice: string) => {
        try {
            setSelectedRealtimeVoice(voice);
            localStorage.setItem(REALTIME_VOICE_STORAGE_KEY, voice);
            
            // Notify backend of realtime voice change
            await fetch('/api/voice-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    voice, 
                    mode: 'realtime' 
                })
            });
            
            console.log(`🎵 Realtime voice updated to: ${voice}`);
        } catch (error) {
            console.warn('Failed to update realtime voice preference:', error);
        }
    }, []);

    return {
        selectedTextVoice,
        selectedRealtimeVoice,
        updateTextVoice,
        updateRealtimeVoice
    };
}
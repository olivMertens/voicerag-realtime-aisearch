import { useState } from 'react';
import { Volume2, Mic } from 'lucide-react';
import { Button } from './button';

interface VoiceSelectorProps {
    selectedVoice: string;
    onVoiceChange: (voice: string) => void;
    disabled?: boolean;
    mode?: 'text' | 'realtime';
    title?: string;
}

const AVAILABLE_VOICES = [
    { id: 'alloy', name: 'Alloy', description: 'Neutral, balanced voice' },
    { id: 'ash', name: 'Ash', description: 'Warm, friendly voice' },
    { id: 'ballad', name: 'Ballad', description: 'Storytelling, expressive voice' },
    { id: 'cedar', name: 'Cedar', description: 'Calm, steady voice' },
    { id: 'coral', name: 'Coral', description: 'Bright, energetic voice' },
    { id: 'echo', name: 'Echo', description: 'Clear, professional voice' },
    { id: 'marin', name: 'Marin', description: 'Sophisticated, elegant voice' },
    { id: 'sage', name: 'Sage', description: 'Wise, mature voice' },
    { id: 'shimmer', name: 'Shimmer', description: 'Light, pleasant voice' },
    { id: 'verse', name: 'Verse', description: 'Poetic, rhythmic voice' }
] as const;

export function VoiceSelector({ 
    selectedVoice, 
    onVoiceChange, 
    disabled = false,
    mode = 'text',
    title 
}: VoiceSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);
    
    const selectedVoiceData = AVAILABLE_VOICES.find(voice => voice.id === selectedVoice) || AVAILABLE_VOICES[0];
    
    const modeIcon = mode === 'realtime' ? <Mic className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />;
    const modeLabel = mode === 'realtime' ? 'Realtime Voice' : 'Text Chat Voice';
    const displayTitle = title || modeLabel;

    return (
        <div className="relative">
            <div className="mb-2 flex items-center gap-2 text-sm text-white/70">
                {modeIcon}
                <span>{displayTitle}</span>
            </div>
            
            <Button
                onClick={() => setIsOpen(!isOpen)}
                disabled={disabled}
                variant="outline"
                size="sm"
                className="w-full justify-between bg-white/10 border-white/30 text-white hover:bg-white/20 flex items-center gap-2"
            >
                <div className="flex items-center gap-2">
                    {modeIcon}
                    <span className="capitalize">{selectedVoiceData.name}</span>
                </div>
                <span className="text-xs opacity-70">▼</span>
            </Button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div 
                        className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm"
                        onClick={() => setIsOpen(false)}
                    />
                    
                    {/* Voice Selection Panel */}
                    <div className="absolute top-full left-0 mt-2 w-80 bg-white/95 backdrop-blur-md rounded-2xl border border-white/20 shadow-2xl z-50 overflow-hidden">
                        <div className="p-4 bg-gradient-to-r from-blue-600/20 to-purple-600/20">
                            <div className="flex items-center gap-2 text-gray-800">
                                {modeIcon}
                                <h3 className="font-semibold">{displayTitle}</h3>
                            </div>
                            <p className="text-sm text-gray-600 mt-1">
                                Select your preferred AI assistant voice
                            </p>
                        </div>
                        
                        <div className="max-h-64 overflow-y-auto">
                            {AVAILABLE_VOICES.map((voice) => (
                                <button
                                    key={voice.id}
                                    onClick={() => {
                                        onVoiceChange(voice.id);
                                        setIsOpen(false);
                                    }}
                                    disabled={disabled}
                                    className={`w-full text-left p-3 hover:bg-blue-50/80 transition-colors border-b border-gray-100/50 disabled:opacity-50 disabled:cursor-not-allowed ${
                                        selectedVoice === voice.id ? 'bg-blue-100/60 border-l-4 border-l-blue-500' : ''
                                    }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <div>
                                            <div className="font-medium text-gray-800 capitalize">
                                                {voice.name}
                                                {selectedVoice === voice.id && (
                                                    <span className="ml-2 text-xs bg-blue-500 text-white px-2 py-0.5 rounded-full">
                                                        Selected
                                                    </span>
                                                )}
                                            </div>
                                            <div className="text-sm text-gray-600 mt-0.5">
                                                {voice.description}
                                            </div>
                                        </div>
                                        <div className="text-xs text-gray-400 uppercase tracking-wide">
                                            {voice.id}
                                        </div>
                                    </div>
                                </button>
                            ))}
                        </div>
                        
                        <div className="p-3 bg-gray-50/80 text-xs text-gray-500 text-center">
                            Voice changes apply to both Realtime and GPT-Audio modes
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
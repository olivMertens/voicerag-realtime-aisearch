import { useState } from 'react';
import { Volume2, Mic, ChevronDown } from 'lucide-react';
import { Button } from './button';

interface CompactVoiceSelectorProps {
    selectedVoice: string;
    onVoiceChange: (voice: string) => void;
    disabled?: boolean;
    mode?: 'text' | 'realtime';
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
];

export function CompactVoiceSelector({ 
    selectedVoice, 
    onVoiceChange, 
    disabled = false,
    mode = 'text'
}: CompactVoiceSelectorProps) {
    const [isOpen, setIsOpen] = useState(false);
    
    const selectedVoiceData = AVAILABLE_VOICES.find(voice => voice.id === selectedVoice) || AVAILABLE_VOICES[0];
    const modeIcon = mode === 'realtime' ? <Mic className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />;

    return (
        <div className="relative inline-block">
            <Button
                onClick={() => setIsOpen(!isOpen)}
                disabled={disabled}
                className="glass-button text-white font-medium px-4 py-2 rounded-xl transition-all duration-300 flex items-center gap-2 min-w-24"
            >
                {modeIcon}
                <span className="capitalize">{selectedVoiceData.name}</span>
                <ChevronDown className={`h-4 w-4 transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
            </Button>

            {isOpen && (
                <>
                    {/* Backdrop */}
                    <div 
                        className="fixed inset-0 z-40" 
                        onClick={() => setIsOpen(false)}
                    />
                    
                    {/* Voice Selection Dropdown */}
                    <div className="absolute top-full left-0 mt-2 w-64 bg-black/90 backdrop-blur-md rounded-xl border border-white/20 shadow-2xl z-50 overflow-hidden">
                        <div className="p-3 bg-gradient-to-r from-blue-600/30 to-purple-600/30 border-b border-white/10">
                            <div className="flex items-center gap-2 text-white">
                                {modeIcon}
                                <h3 className="font-medium text-sm">
                                    {mode === 'realtime' ? 'Realtime Voice' : 'Text Chat Voice'}
                                </h3>
                            </div>
                        </div>
                        
                        <div className="max-h-48 overflow-y-auto">
                            {AVAILABLE_VOICES.map((voice) => (
                                <button
                                    key={voice.id}
                                    onClick={() => {
                                        onVoiceChange(voice.id);
                                        setIsOpen(false);
                                    }}
                                    disabled={disabled}
                                    className={`w-full px-3 py-2 text-left hover:bg-white/10 transition-colors text-sm ${
                                        voice.id === selectedVoice ? 'bg-blue-600/50 text-white' : 'text-white/80'
                                    }`}
                                >
                                    <div className="flex items-center justify-between">
                                        <div>
                                            <div className="font-medium">{voice.name}</div>
                                            <div className="text-xs text-white/60 mt-0.5">{voice.description}</div>
                                        </div>
                                        {voice.id === selectedVoice && (
                                            <div className="text-blue-400 text-sm">✓</div>
                                        )}
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
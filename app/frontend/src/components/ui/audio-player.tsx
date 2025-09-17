import { useState, useRef, useEffect } from 'react';
import { Play, Pause, Square, Volume2, Loader2 } from 'lucide-react';
import { Button } from './button';

interface AudioPlayerProps {
    audioData?: string; // Base64 encoded MP3 data
    audioFormat?: string; // Format (mp3, wav)
    isLoading?: boolean;
    onPlayStart?: () => void;
    onPlayEnd?: () => void;
    onError?: (error: string) => void;
    autoPlay?: boolean;
    voice?: string;
    transcript?: string;
}

export function AudioPlayer({
    audioData,
    audioFormat = 'mp3',
    isLoading = false,
    onPlayStart,
    onPlayEnd,
    onError,
    autoPlay = false,
    voice = 'alloy',
    transcript
}: AudioPlayerProps) {
    const [isPlaying, setIsPlaying] = useState(false);
    const [duration, setDuration] = useState(0);
    const [currentTime, setCurrentTime] = useState(0);
    const [volume, setVolume] = useState(1.0);
    const [isReady, setIsReady] = useState(false);
    const [error, setError] = useState<string | null>(null);
    
    const audioRef = useRef<HTMLAudioElement>(null);
    const progressInterval = useRef<number | null>(null);

    // Create audio blob URL from base64 data
    useEffect(() => {
        if (!audioData || isLoading) {
            setIsReady(false);
            setError(null);
            return;
        }

        try {
            // Decode base64 audio data - following soundboard.py pattern
            const binaryString = atob(audioData);
            const bytes = new Uint8Array(binaryString.length);
            for (let i = 0; i < binaryString.length; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            
            const audioBlob = new Blob([bytes], { type: `audio/${audioFormat}` });
            const audioUrl = URL.createObjectURL(audioBlob);
            
            if (audioRef.current) {
                audioRef.current.src = audioUrl;
                audioRef.current.load();
            }
            
            // Cleanup URL when component unmounts
            return () => {
                URL.revokeObjectURL(audioUrl);
            };
        } catch (err) {
            const errorMsg = `Failed to decode audio data: ${err instanceof Error ? err.message : 'Unknown error'}`;
            setError(errorMsg);
            onError?.(errorMsg);
        }
    }, [audioData, audioFormat, isLoading, onError]);

    // Auto-play when audio is ready
    useEffect(() => {
        if (isReady && autoPlay && !isPlaying && audioData) {
            handlePlay();
        }
    }, [isReady, autoPlay, audioData]);

    const handlePlay = async () => {
        if (!audioRef.current || isLoading) return;

        try {
            await audioRef.current.play();
            setIsPlaying(true);
            onPlayStart?.();
            
            // Start progress tracking
            progressInterval.current = window.setInterval(() => {
                if (audioRef.current) {
                    setCurrentTime(audioRef.current.currentTime);
                }
            }, 100);
        } catch (err) {
            const errorMsg = `Playback failed: ${err instanceof Error ? err.message : 'Unknown error'}`;
            setError(errorMsg);
            onError?.(errorMsg);
        }
    };

    const handlePause = () => {
        if (!audioRef.current) return;
        
        audioRef.current.pause();
        setIsPlaying(false);
        
        if (progressInterval.current) {
            clearInterval(progressInterval.current);
            progressInterval.current = null;
        }
    };

    const handleStop = () => {
        if (!audioRef.current) return;
        
        audioRef.current.pause();
        audioRef.current.currentTime = 0;
        setIsPlaying(false);
        setCurrentTime(0);
        
        if (progressInterval.current) {
            clearInterval(progressInterval.current);
            progressInterval.current = null;
        }
        
        onPlayEnd?.();
    };

    const handleVolumeChange = (newVolume: number) => {
        setVolume(newVolume);
        if (audioRef.current) {
            audioRef.current.volume = newVolume;
        }
    };

    const handleSeek = (seekTime: number) => {
        if (!audioRef.current) return;
        
        audioRef.current.currentTime = seekTime;
        setCurrentTime(seekTime);
    };

    const formatTime = (time: number): string => {
        const minutes = Math.floor(time / 60);
        const seconds = Math.floor(time % 60);
        return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    };

    return (
        <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-4 border border-white/20">
            {/* Hidden HTML5 Audio Element */}
            <audio
                ref={audioRef}
                onLoadedMetadata={() => {
                    if (audioRef.current) {
                        setDuration(audioRef.current.duration);
                        setIsReady(true);
                        setError(null);
                    }
                }}
                onEnded={() => {
                    setIsPlaying(false);
                    setCurrentTime(0);
                    if (progressInterval.current) {
                        clearInterval(progressInterval.current);
                        progressInterval.current = null;
                    }
                    onPlayEnd?.();
                }}
                onError={() => {
                    const errorMsg = 'Audio playback error occurred';
                    setError(errorMsg);
                    onError?.(errorMsg);
                }}
            />

            {/* Audio Player Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    <Volume2 className="w-5 h-5 text-blue-400" />
                    <div>
                        <h3 className="text-white font-semibold text-sm">
                            AI Audio Response
                        </h3>
                        <p className="text-white/70 text-xs capitalize">
                            Voice: {voice}
                        </p>
                    </div>
                </div>
                
                {/* Loading Indicator */}
                {isLoading && (
                    <div className="flex items-center gap-2 text-blue-400">
                        <Loader2 className="w-4 h-4 animate-spin" />
                        <span className="text-xs">Generating...</span>
                    </div>
                )}
            </div>

            {/* Error Display */}
            {error && (
                <div className="mb-3 p-2 bg-red-500/20 border border-red-500/30 rounded-lg">
                    <p className="text-red-200 text-xs">{error}</p>
                </div>
            )}

            {/* Progress Bar */}
            {isReady && duration > 0 && (
                <div className="mb-4">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-white/70">
                            {formatTime(currentTime)}
                        </span>
                        <span className="text-xs text-white/70">
                            {formatTime(duration)}
                        </span>
                    </div>
                    <div className="w-full bg-white/20 rounded-full h-2">
                        <div
                            className="bg-blue-500 h-2 rounded-full transition-all duration-100"
                            style={{ width: `${(currentTime / duration) * 100}%` }}
                        />
                    </div>
                    <input
                        type="range"
                        min="0"
                        max={duration}
                        value={currentTime}
                        onChange={(e) => handleSeek(Number(e.target.value))}
                        className="w-full mt-1 opacity-0 cursor-pointer absolute"
                        style={{ height: '8px', marginTop: '-8px' }}
                    />
                </div>
            )}

            {/* Control Buttons */}
            <div className="flex items-center justify-center gap-2 mb-3">
                <Button
                    onClick={isPlaying ? handlePause : handlePlay}
                    disabled={!isReady || isLoading}
                    size="sm"
                    className="bg-blue-500 hover:bg-blue-600 text-white"
                >
                    {isLoading ? (
                        <Loader2 className="w-4 h-4 animate-spin" />
                    ) : isPlaying ? (
                        <Pause className="w-4 h-4" />
                    ) : (
                        <Play className="w-4 h-4" />
                    )}
                </Button>
                
                <Button
                    onClick={handleStop}
                    disabled={!isReady || isLoading}
                    size="sm"
                    variant="outline"
                    className="border-white/30 text-white hover:bg-white/10"
                >
                    <Square className="w-4 h-4" />
                </Button>
            </div>

            {/* Volume Control */}
            {isReady && (
                <div className="flex items-center gap-2">
                    <Volume2 className="w-3 h-3 text-white/70" />
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.1"
                        value={volume}
                        onChange={(e) => handleVolumeChange(Number(e.target.value))}
                        className="flex-1 h-1 bg-white/20 rounded-full appearance-none slider"
                        style={{
                            background: `linear-gradient(to right, #3b82f6 0%, #3b82f6 ${volume * 100}%, rgba(255,255,255,0.2) ${volume * 100}%, rgba(255,255,255,0.2) 100%)`
                        }}
                    />
                    <span className="text-xs text-white/70 w-8">
                        {Math.round(volume * 100)}%
                    </span>
                </div>
            )}

            {/* Transcript */}
            {transcript && (
                <div className="mt-3 pt-3 border-t border-white/20">
                    <p className="text-xs text-white/80 italic">
                        "{transcript}"
                    </p>
                </div>
            )}

            {/* Audio Status */}
            <div className="mt-2 text-center">
                <p className="text-xs text-white/50">
                    {isLoading ? 'Generating audio...' : 
                     !audioData ? 'No audio available' :
                     !isReady ? 'Loading audio...' :
                     isPlaying ? 'Playing' : 'Ready to play'}
                </p>
            </div>
        </div>
    );
}
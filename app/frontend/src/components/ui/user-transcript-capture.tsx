import React, { useState, useEffect } from 'react';
import { Mic, MicOff, User } from 'lucide-react';
import { useSpeechToText } from '../../hooks/useSpeechToText';

interface UserTranscriptCaptureProps {
  onUserTranscript?: (transcript: string) => void;
}

export const UserTranscriptCapture: React.FC<UserTranscriptCaptureProps> = ({
  onUserTranscript
}) => {
  const [isCapturing, setIsCapturing] = useState(false);
  const [capturedQuestions, setCapturedQuestions] = useState<Array<{
    id: string;
    transcript: string;
    timestamp: number;
  }>>([]);

  const {
    isListening,
    transcript,
    interimTranscript,
    isSupported,
    startListening,
    stopListening,
    resetTranscript
  } = useSpeechToText({
    continuous: false, // Stop after user finishes speaking
    interimResults: true,
    language: 'fr-FR',
    onTranscript: (transcriptText: string, isFinal: boolean) => {
      if (isFinal && transcriptText.trim()) {
        // Save the user's question to our log
        const newQuestion = {
          id: Date.now().toString(),
          transcript: transcriptText.trim(),
          timestamp: Date.now()
        };
        
        setCapturedQuestions(prev => [...prev, newQuestion]);
        
        // Send to conversation log API
        logUserTranscript(newQuestion);
        
        // Callback for parent component
        if (onUserTranscript) {
          onUserTranscript(transcriptText.trim());
        }

        // Reset for next capture
        resetTranscript();
        setIsCapturing(false);
      }
    },
    onError: (error: string) => {
      console.error('Speech recognition error:', error);
      setIsCapturing(false);
    }
  });

  const logUserTranscript = async (question: { id: string; transcript: string; timestamp: number }) => {
    try {
      await fetch('/api/user-transcript', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          type: 'user_question',
          transcript: question.transcript,
          timestamp: question.timestamp,
          session_id: Date.now().toString() // Simple session ID
        })
      });
    } catch (error) {
      console.error('Failed to log user transcript:', error);
    }
  };

  const handleToggleCapture = () => {
    if (isCapturing && isListening) {
      stopListening();
      setIsCapturing(false);
    } else if (!isCapturing) {
      setIsCapturing(true);
      startListening();
    }
  };

  useEffect(() => {
    // Auto-stop after 30 seconds of listening
    let timeout: NodeJS.Timeout;
    if (isListening) {
      timeout = setTimeout(() => {
        stopListening();
        setIsCapturing(false);
      }, 30000);
    }
    return () => clearTimeout(timeout);
  }, [isListening, stopListening]);

  if (!isSupported) {
    return (
      <div className="text-xs text-white/60 p-2">
        Speech recognition not supported in this browser
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {/* Capture Control */}
      <div className="flex items-center justify-between">
        <button
          onClick={handleToggleCapture}
          disabled={!isSupported}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
            isCapturing
              ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
              : 'bg-blue-500/20 text-blue-400 hover:bg-blue-500/30'
          } disabled:opacity-50 disabled:cursor-not-allowed`}
        >
          {isCapturing ? (
            <>
              <MicOff className="h-4 w-4" />
              Arrêter la capture
            </>
          ) : (
            <>
              <Mic className="h-4 w-4" />
              Capturer la question
            </>
          )}
        </button>

        <div className="text-xs text-white/60">
          {capturedQuestions.length} question{capturedQuestions.length !== 1 ? 's' : ''} capturée{capturedQuestions.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Live Transcript Display */}
      {isCapturing && (
        <div className="glass-dark rounded-lg p-3">
          <div className="flex items-center gap-2 mb-2">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
              <span className="text-xs text-white/80">En écoute...</span>
            </div>
          </div>
          
          <div className="text-sm text-white/90 min-h-[2em]">
            {transcript && (
              <span className="text-green-400">{transcript}</span>
            )}
            {interimTranscript && (
              <span className="text-white/60 italic">{interimTranscript}</span>
            )}
            {!transcript && !interimTranscript && (
              <span className="text-white/40">Parlez maintenant...</span>
            )}
          </div>
        </div>
      )}

      {/* Recent Captured Questions */}
      {capturedQuestions.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-xs font-semibold text-white/80 uppercase tracking-wide">
            Questions récentes
          </h4>
          <div className="space-y-1 max-h-32 overflow-y-auto">
            {capturedQuestions.slice(-5).reverse().map((question) => (
              <div key={question.id} className="glass-dark rounded-lg p-2 text-xs">
                <div className="flex items-start gap-2">
                  <User className="h-3 w-3 text-blue-400 flex-shrink-0 mt-0.5" />
                  <div className="flex-1 min-w-0">
                    <div className="text-white/90 break-words">
                      utilisateur : "{question.transcript}"
                    </div>
                    <div className="text-white/40 text-[10px] mt-1">
                      {new Date(question.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default UserTranscriptCapture;
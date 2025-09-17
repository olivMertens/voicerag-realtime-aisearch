import React, { useState, useEffect, useRef } from 'react';
import { MessageSquare, User, Bot, Mic, MicOff, Download } from 'lucide-react';
import UserTranscriptCapture from './user-transcript-capture';

interface TranscriptMessage {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: number;
  isComplete: boolean;
}

interface TranscriptPanelProps {
  isRecording: boolean;
  currentUserInput?: string;
  currentAssistantResponse?: string;
  userMessages: string[];
  assistantMessages: string[];
  isVisible: boolean;
  onToggle: () => void;
}

export const TranscriptPanel: React.FC<TranscriptPanelProps> = ({ 
  isRecording, 
  currentUserInput = '', 
  currentAssistantResponse = '',
  userMessages = [],
  assistantMessages = [],
  isVisible,
  onToggle
}) => {
  const [messages, setMessages] = useState<TranscriptMessage[]>([]);
  const [activeTab, setActiveTab] = useState<'realtime' | 'capture'>('realtime');
  const scrollRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages are added
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, currentUserInput, currentAssistantResponse]);

  // Update messages when props change
  useEffect(() => {
    const allMessages: TranscriptMessage[] = [];
    
    // Interleave user and assistant messages chronologically
    const maxLength = Math.max(userMessages.length, assistantMessages.length);
    
    for (let i = 0; i < maxLength; i++) {
      if (i < userMessages.length && userMessages[i]) {
        allMessages.push({
          id: `user-${i}`,
          type: 'user',
          content: userMessages[i],
          timestamp: Date.now() - ((maxLength - i) * 1000),
          isComplete: true
        });
      }
      
      if (i < assistantMessages.length && assistantMessages[i]) {
        allMessages.push({
          id: `assistant-${i}`,
          type: 'assistant',
          content: assistantMessages[i],
          timestamp: Date.now() - ((maxLength - i) * 1000) + 500,
          isComplete: true
        });
      }
    }
    
    // Sort by timestamp
    allMessages.sort((a, b) => a.timestamp - b.timestamp);
    setMessages(allMessages);
  }, [userMessages, assistantMessages]);

  const downloadTranscript = () => {
    // Combine all messages including current ones
    const allTranscriptMessages = [...messages];
    
    // Add current user input if exists
    if (currentUserInput) {
      allTranscriptMessages.push({
        id: 'current-user',
        type: 'user' as const,
        content: `utilisateur : "${currentUserInput}"`,
        timestamp: Date.now(),
        isComplete: false
      });
    }
    
    // Add current assistant response if exists
    if (currentAssistantResponse) {
      allTranscriptMessages.push({
        id: 'current-assistant',
        type: 'assistant' as const,
        content: currentAssistantResponse,
        timestamp: Date.now(),
        isComplete: false
      });
    }

    console.log('📝 Downloading transcript with messages:', allTranscriptMessages.length);

    if (allTranscriptMessages.length === 0) {
      alert('Aucun transcript à télécharger');
      return;
    }

    const transcriptText = allTranscriptMessages
      .map(message => {
        const timestamp = new Date(message.timestamp).toLocaleString();
        const role = message.type === 'user' ? 'Utilisateur' : 'Assistant IA';
        return `[${timestamp}] ${role}: ${message.content}`;
      })
      .join('\n\n');

    const blob = new Blob([transcriptText], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `transcript-${new Date().toISOString().split('T')[0]}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('✅ Transcript downloaded successfully');
  };

  const handleUserTranscript = (transcript: string) => {
    // Add to messages list with formatted display
    const newMessage: TranscriptMessage = {
      id: `captured-${Date.now()}`,
      type: 'user',
      content: `"${transcript}"`, // Format as requested by user
      timestamp: Date.now(),
      isComplete: true
    };
    setMessages(prev => [...prev, newMessage]);
  };

  return (
    <>
      {/* Transcript panel */}
      <div className={`fixed left-6 bottom-20 w-96 h-[70vh] glass border-white/20 rounded-xl transition-all duration-300 flex flex-col z-40 ${
        isVisible ? 'opacity-100 translate-x-0 pointer-events-auto' : 'opacity-0 -translate-x-full pointer-events-none'
      }`}>
        {/* Header */}
        <div className="p-4 border-b border-white/10">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-white font-semibold flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Transcriptions
              {isRecording && <Mic className="h-4 w-4 text-red-400 animate-pulse" />}
              {!isRecording && <MicOff className="h-4 w-4 text-gray-400" />}
            </h3>
            <div className="flex items-center gap-2">
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  console.log('📥 Download button clicked');
                  downloadTranscript();
                }}
                className="interactive-button p-2 hover:bg-white/20 rounded-full transition-all duration-200 z-50 relative"
                title="Télécharger les transcriptions"
                type="button"
              >
                <Download className="h-4 w-4 text-white/80 hover:text-white" />
              </button>
              <button
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  console.log('🗙 Closing transcript panel');
                  onToggle();
                }}
                className="interactive-button p-2 hover:bg-white/20 rounded-full transition-all duration-200 z-50 relative text-white/80 hover:text-white text-lg font-bold leading-none"
                title="Fermer le panneau"
                type="button"
              >
                ×
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-white/10">
            <button
              onClick={() => setActiveTab('realtime')}
              className={`flex-1 px-3 py-1 text-sm font-medium transition-colors ${
                activeTab === 'realtime'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              Temps réel
            </button>
            <button
              onClick={() => setActiveTab('capture')}
              className={`flex-1 px-3 py-1 text-sm font-medium transition-colors ${
                activeTab === 'capture'
                  ? 'text-blue-400 border-b-2 border-blue-400'
                  : 'text-white/60 hover:text-white'
              }`}
            >
              Capture vocale
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-hidden">
          {/* Real-time Tab */}
          {activeTab === 'realtime' && (
            <div 
              ref={scrollRef}
              className="h-full overflow-y-auto p-4 space-y-3"
            >
              {messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex gap-3 ${
                    message.type === 'assistant' ? 'justify-start' : 'justify-end'
                  }`}
                >
                  {message.type === 'assistant' && (
                    <div className="flex-shrink-0 w-8 h-8 glass-card rounded-full flex items-center justify-center">
                      <Bot className="h-4 w-4 text-blue-400" />
                    </div>
                  )}
                  
                  <div className={`max-w-[80%] ${
                    message.type === 'assistant' 
                      ? 'bg-blue-500/20 text-white' 
                      : 'bg-white/20 text-white'
                  } rounded-2xl px-4 py-2 glass-card`}>
                    <p className="text-sm leading-relaxed">{message.content}</p>
                    <div className="text-xs text-white/60 mt-1">
                      {new Date(message.timestamp).toLocaleTimeString()}
                    </div>
                  </div>
                  
                  {message.type === 'user' && (
                    <div className="flex-shrink-0 w-8 h-8 glass-card rounded-full flex items-center justify-center">
                      <User className="h-4 w-4 text-green-400" />
                    </div>
                  )}
                </div>
              ))}
              
              {/* Current user input (live) */}
              {currentUserInput && (
                <div className="flex gap-3 justify-end">
                  <div className="max-w-[80%] bg-white/10 text-white/80 rounded-2xl px-4 py-2 glass-card border-2 border-green-400/30">
                    <p className="text-sm leading-relaxed">utilisateur : "{currentUserInput}"</p>
                    <div className="text-xs text-green-400 mt-1 flex items-center gap-1">
                      <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
                      En cours...
                    </div>
                  </div>
                  <div className="flex-shrink-0 w-8 h-8 glass-card rounded-full flex items-center justify-center border-2 border-green-400/30">
                    <User className="h-4 w-4 text-green-400" />
                  </div>
                </div>
              )}
              
              {/* Current assistant response (live) */}
              {currentAssistantResponse && (
                <div className="flex gap-3 justify-start">
                  <div className="flex-shrink-0 w-8 h-8 glass-card rounded-full flex items-center justify-center border-2 border-blue-400/30">
                    <Bot className="h-4 w-4 text-blue-400" />
                  </div>
                  <div className="max-w-[80%] bg-blue-500/10 text-white/80 rounded-2xl px-4 py-2 glass-card border-2 border-blue-400/30">
                    <p className="text-sm leading-relaxed">{currentAssistantResponse}</p>
                    <div className="text-xs text-blue-400 mt-1 flex items-center gap-1">
                      <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                      En cours de génération...
                    </div>
                  </div>
                </div>
              )}

              {messages.length === 0 && !currentUserInput && !currentAssistantResponse && (
                <div className="p-8 text-center text-white/60">
                  <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">
                    Commencez à parler pour voir le transcript des conversations
                  </p>
                </div>
              )}
            </div>
          )}

          {/* Speech Capture Tab */}
          {activeTab === 'capture' && (
            <div className="h-full overflow-y-auto p-4">
              <UserTranscriptCapture onUserTranscript={handleUserTranscript} />
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default TranscriptPanel;
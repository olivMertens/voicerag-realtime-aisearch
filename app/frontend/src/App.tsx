import { useState } from "react";
import { Mic, MicOff, Shield, Send, MessageSquare, RotateCcw, Plus, Volume2 } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { GroundingFiles } from "@/components/ui/grounding-files";
import GroundingFileView from "@/components/ui/grounding-file-view";
import StatusMessage from "@/components/ui/status-message";
import { TelemetryPanel } from "@/components/ui/telemetry-panel";
import TranscriptPanel from "@/components/ui/transcript-panel";
import FloatingIconsBar from "@/components/ui/floating-icons-bar";
import RagSourceDisplay from "@/components/ui/rag-source-display";
import { EnhancedGroundingDisplay } from "@/components/ui/enhanced-grounding-display";
import { CallHistoryPopup } from "@/components/ui/call-history-popup";
import { AudioPlayer } from "@/components/ui/audio-player";
import { CompactVoiceSelector } from "@/components/ui/compact-voice-selector";
import FloatingThemeButton from "@/components/ui/floating-theme-button";

import { ThemeProvider } from "@/contexts/ThemeContext";
import useRealTime from "@/hooks/useRealtime";
import useAudioRecorder from "@/hooks/useAudioRecorder";
import useAudioPlayer from "@/hooks/useAudioPlayer";
import useChat from "@/hooks/useChat";
import { useChatWithAudio } from "@/hooks/useChatWithAudio";
import { useVoiceSettings } from "@/hooks/useVoiceSettings";

import { GroundingFile, ToolResult, EnhancedToolResult, CallHistoryMetadata } from "./types";

interface RagSource {
    id: string;
    content: string;
    title: string;
    category: string;
    excerpt: string;
}

// Common French first names to detect in transcriptions
const FRENCH_NAMES = [
    'pierre', 'jean', 'marie', 'paul', 'michel', 'anne', 'françois', 'christian', 'philippe', 'jacques',
    'alain', 'bernard', 'claude', 'daniel', 'didier', 'eric', 'fabrice', 'gérard', 'henri', 'julien',
    'laurent', 'marc', 'olivier', 'patrick', 'robert', 'stéphane', 'thierry', 'vincent', 'yves',
    'sophie', 'nathalie', 'isabelle', 'catherine', 'françoise', 'monique', 'sylvie', 'patricia',
    'martine', 'nicole', 'véronique', 'chantal', 'dominique', 'brigitte', 'christine', 'corinne',
    'céline', 'sandrine', 'valérie', 'karine', 'laure', 'caroline', 'aurélie', 'ludovic', 'frédéric'
];

// Function to detect if text contains name introduction patterns
const detectNameMentions = (text: string): { hasNameMention: boolean; detectedNames: string[] } => {
    const lowerText = text.toLowerCase();
    const detectedNames: string[] = [];
    
    // Patterns that indicate someone is introducing themselves
    const introPatterns = [
        /je suis ([a-z]+)/g,
        /je m['']appelle ([a-z]+)/g,
        /mon nom est ([a-z]+)/g,
        /c['']est ([a-z]+)/g,
        /moi c['']est ([a-z]+)/g,
        /je me présente[,]? ([a-z]+)/g
    ];
    
    // Check for name introduction patterns
    for (const pattern of introPatterns) {
        const matches = Array.from(lowerText.matchAll(pattern));
        for (const match of matches) {
            const name = match[1];
            if (FRENCH_NAMES.includes(name)) {
                detectedNames.push(name);
            }
        }
    }
    
    // Also check for direct name mentions in common contexts
    const words = lowerText.split(/\s+/);
    for (const word of words) {
        if (FRENCH_NAMES.includes(word.replace(/[.,!?;:]/g, ''))) {
            detectedNames.push(word.replace(/[.,!?;:]/g, ''));
        }
    }
    
    return {
        hasNameMention: detectedNames.length > 0,
        detectedNames: [...new Set(detectedNames)] // Remove duplicates
    };
};

function App() {
    return (
        <ThemeProvider>
            <AppContent />
        </ThemeProvider>
    );
}

function AppContent() {
    const [isRecording, setIsRecording] = useState(false);
    const [groundingFiles, setGroundingFiles] = useState<GroundingFile[]>([]);
    const [selectedFile, setSelectedFile] = useState<GroundingFile | null>(null);
    const [currentUserTranscript, setCurrentUserTranscript] = useState("");
    const [currentAssistantTranscript, setCurrentAssistantTranscript] = useState("");
    const [completedUserMessages, setCompletedUserMessages] = useState<string[]>([]);
    const [completedAssistantMessages, setCompletedAssistantMessages] = useState<string[]>([]);
    const [isTelemetryVisible, setIsTelemetryVisible] = useState(false);
    const [isTranscriptVisible, setIsTranscriptVisible] = useState(false);
    const [ragSources, setRagSources] = useState<RagSource[]>([]);
    const [enhancedGrounding, setEnhancedGrounding] = useState<EnhancedToolResult | null>(null);
    const [isGroundingVisible, setIsGroundingVisible] = useState(false);
    const [textMessage, setTextMessage] = useState("");
    const [showTextChat, setShowTextChat] = useState(false);
    const [callHistoryMetadata, setCallHistoryMetadata] = useState<CallHistoryMetadata | null>(null);
    const [isCallHistoryVisible, setIsCallHistoryVisible] = useState(false);

    // Audio and voice settings hooks
    const { selectedTextVoice, selectedRealtimeVoice, updateTextVoice, updateRealtimeVoice } = useVoiceSettings();
    const { 
        sendMessage: sendMessageWithAudio, 
        isGeneratingAudio, 
        lastAudioData,
        lastAudioFormat,
        lastVoice,
        lastAudioTranscript,
        clearMessages: clearChatMessages,
        messages: chatMessages
    } = useChatWithAudio();

    const { startSession, addUserAudio, inputAudioBufferClear } = useRealTime({
        onWebSocketOpen: () => console.log("WebSocket connection opened"),
        onWebSocketClose: () => console.log("WebSocket connection closed"),
        onWebSocketError: event => console.error("WebSocket error:", event),
        onReceivedError: message => console.error("error", message),
        onReceivedResponseAudioDelta: message => {
            playAudio(message.delta);
        },
        onReceivedResponseAudioTranscriptDelta: message => {
            // Update assistant transcript in real-time
            setCurrentAssistantTranscript(prev => prev + (message.delta || ''));
        },
        onReceivedInputAudioTranscriptionCompleted: message => {
            // User speech completed - add to completed messages
            if (message.transcript) {
                setCompletedUserMessages(prev => [...prev, message.transcript]);
                setCurrentUserTranscript('');
                
                // Detect name mentions in user transcript
                const nameDetection = detectNameMentions(message.transcript);
                if (nameDetection.hasNameMention) {
                    console.log('👤 Name mentioned in transcript:', nameDetection.detectedNames);
                    // The AI model will automatically use the appropriate tools based on the conversation context
                    // The call history popup will show when tool responses include call history metadata
                }
            }
        },
        onReceivedInputAudioBufferSpeechStarted: () => {
            // Clear current user transcript when starting new speech and stop audio player
            setCurrentUserTranscript('');
            stopAudioPlayer();
        },
        onReceivedResponseDone: () => {
            // Assistant response completed - add to completed messages
            setCompletedAssistantMessages(prev => {
                // Only add if currentAssistantTranscript is not empty and not already in the array
                if (currentAssistantTranscript && !prev.includes(currentAssistantTranscript)) {
                    return [...prev, currentAssistantTranscript];
                }
                return prev;
            });
            // Reset current assistant transcript after adding to completed messages
            setCurrentAssistantTranscript('');
        },
        onReceivedExtensionMiddleTierToolResponse: message => {
            console.log("🔧 Tool Response Received:", message.tool_name, message.tool_result);
            
            try {
                const result: ToolResult = JSON.parse(message.tool_result);
                console.log("📋 Parsed Tool Result:", result);

                // Handle enhanced grounding format
                if ('grounding_info' in result && result.grounding_info) {
                    console.log("✅ Enhanced grounding detected:", result);
                    setEnhancedGrounding(result as EnhancedToolResult);
                    setIsGroundingVisible(true);
                    
                    // Convert enhanced sources to legacy format for backward compatibility
                    if (result.sources) {
                        const files: GroundingFile[] = result.sources.map(x => ({
                            id: x.chunk_id, 
                            name: x.title || 'Document sans titre', 
                            content: x.chunk
                        }));
                        setGroundingFiles(prev => [...prev, ...files]);
                    }
                }
                // Handle legacy grounding format
                else if (result.sources && Array.isArray(result.sources)) {
                    console.log("📄 Legacy grounding format:", result.sources.length, "sources");
                    const files: GroundingFile[] = result.sources.map(x => {
                        return { id: x.chunk_id, name: x.title, content: x.chunk };
                    });
                    setGroundingFiles(prev => [...prev, ...files]);
                }

                // Extract RAG sources from tool response if available
                try {
                    // Check if tool response contains call history metadata
                    if ('__CALL_HISTORY_METADATA__' in result && result.__CALL_HISTORY_METADATA__) {
                        const callHistoryData = result.__CALL_HISTORY_METADATA__ as CallHistoryMetadata[];
                        console.log('📞 Call history metadata detected:', callHistoryData);
                        
                        // Show the first customer's call history in popup
                        if (callHistoryData.length > 0) {
                            setCallHistoryMetadata(callHistoryData[0]);
                            setIsCallHistoryVisible(true);
                            console.log('📋 Displaying call history for:', callHistoryData[0].customer);
                        }
                    }
                    
                    // Check if tool response contains metadata for RAG sources
                    const toolResponseText = message.tool_result;
                    const metadataMatch = toolResponseText.match(/__METADATA__: (.+)$/);
                    
                    if (metadataMatch) {
                        const metadata = JSON.parse(metadataMatch[1]);
                        if (Array.isArray(metadata)) {
                            setRagSources(metadata);
                            console.log('📚 Extracted RAG sources:', metadata);
                        }
                    }
                } catch (error) {
                    console.warn('Failed to extract RAG metadata:', error);
                }
            } catch (parseError) {
                console.error("❌ Failed to parse tool result:", parseError);
            }
        },
        enableInputAudioTranscription: true  // Enable transcription
    });

    const { reset: resetAudioPlayer, play: playAudio, stop: stopAudioPlayer } = useAudioPlayer();
    const { start: startAudioRecording, stop: stopAudioRecording } = useAudioRecorder({ onAudioRecorded: addUserAudio });

    // GPT-Audio chat hook
    useChat({
        onNewMessage: (message) => {
            console.log('New chat message:', message);
        },
        onAudioReceived: (audioBase64) => {
            console.log('Audio received, playing...');
            // Convert base64 to audio and play it
            try {
                const audioBlob = new Blob(
                    [Uint8Array.from(atob(audioBase64), c => c.charCodeAt(0))], 
                    { type: 'audio/wav' }
                );
                const audioUrl = URL.createObjectURL(audioBlob);
                const audio = new Audio(audioUrl);
                audio.play().catch(e => console.error('Error playing audio:', e));
                
                // Cleanup URL after playing
                audio.onended = () => URL.revokeObjectURL(audioUrl);
            } catch (error) {
                console.error('Error playing audio:', error);
            }
        }
    });

    const onToggleListening = async () => {
        if (!isRecording) {
            startSession();
            await startAudioRecording();
            resetAudioPlayer();

            setIsRecording(true);
        } else {
            await stopAudioRecording();
            stopAudioPlayer();
            inputAudioBufferClear();

            setIsRecording(false);
        }
    };

    // Function to restart/refresh conversation
    const handleRestartConversation = () => {
        // Add confirmation dialog
        if (chatMessages.length > 0 || completedUserMessages.length > 0 || completedAssistantMessages.length > 0) {
            if (!confirm('Êtes-vous sûr de vouloir redémarrer la conversation ? Tous les messages seront effacés.')) {
                return;
            }
        }
        
        // Clear chat messages from text mode
        clearChatMessages();
        
        // Clear realtime conversation transcripts
        setCompletedUserMessages([]);
        setCompletedAssistantMessages([]);
        setCurrentUserTranscript('');
        setCurrentAssistantTranscript('');
        
        // Clear text input
        setTextMessage('');
        
        // Clear grounding and metadata
        setGroundingFiles([]);
        setSelectedFile(null);
        setRagSources([]);
        setEnhancedGrounding(null);
        setCallHistoryMetadata(null);
        setIsCallHistoryVisible(false);
        
        // Stop current recording if active
        if (isRecording) {
            onToggleListening();
        }
        
        console.log('🔄 Conversation restarted');
    };

    const { t } = useTranslation();

    return (
        <div className="min-h-screen relative overflow-hidden">
            {/* Floating background elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-20 left-10 w-64 h-64 bg-white/10 rounded-full blur-3xl floating-element pointer-events-none"></div>
                <div className="absolute top-40 right-16 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl floating-element pointer-events-none" style={{ animationDelay: '2s' }}></div>
                <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-purple-400/10 rounded-full blur-3xl floating-element pointer-events-none" style={{ animationDelay: '4s' }}></div>
            </div>

            {/* Header with logo */}
            <header className="relative z-10 pointer-events-none">
                <div className="absolute top-6 left-6 glass-card rounded-2xl p-4 floating-element pointer-events-auto">
                    <Shield className="h-16 w-16 text-white drop-shadow-lg" />
                </div>
                
                {/* Action Buttons */}
                <div className="absolute top-6 right-6 pointer-events-auto z-50 flex gap-3">
                    {/* New Session Button */}
                    <Button
                        onClick={() => {
                            // Clear all conversations and start fresh
                            clearChatMessages();
                            setCompletedUserMessages([]);
                            setCompletedAssistantMessages([]);
                            setCurrentUserTranscript('');
                            setCurrentAssistantTranscript('');
                            setTextMessage('');
                            setGroundingFiles([]);
                            setSelectedFile(null);
                            setRagSources([]);
                            setEnhancedGrounding(null);
                            setCallHistoryMetadata(null);
                            setIsCallHistoryVisible(false);
                            
                            // Stop recording if active
                            if (isRecording) {
                                onToggleListening();
                            }
                            
                            console.log('🆕 New session started');
                        }}
                        className="glass-card hover:bg-white/20 text-white p-4 rounded-2xl transition-all duration-200 floating-element group cursor-pointer"
                        title="Nouvelle session"
                        style={{ pointerEvents: 'auto' }}
                    >
                        <Plus className="h-6 w-6 transition-transform duration-200 group-hover:scale-110" />
                    </Button>
                    
                    {/* Restart Conversation Button */}
                    <Button
                        onClick={handleRestartConversation}
                        className="glass-card hover:bg-white/20 text-white p-4 rounded-2xl transition-all duration-200 floating-element group cursor-pointer"
                        title="Redémarrer la conversation"
                        style={{ pointerEvents: 'auto' }}
                    >
                        <RotateCcw className="h-6 w-6 transition-transform duration-200 group-hover:rotate-180" />
                    </Button>
                </div>
            </header>

            <main className="flex flex-col items-center justify-center min-h-screen relative z-10 px-6 pb-20">
                {/* Main title with glass effect */}
                <div className="glass rounded-3xl p-8 mb-12 text-center max-w-4xl">
                    <h1 className="text-4xl md:text-6xl lg:text-7xl font-bold text-white text-glow mb-4">
                        {t("app.title")}
                    </h1>
                    <p className="text-lg md:text-xl text-white/80 font-medium">
                        Assistant vocal intelligent pour vos assurances
                    </p>
                </div>

                {/* Voice control section */}
                <div className="glass-card rounded-3xl p-8 mb-8 text-center min-w-[400px]">
                    {/* Mode Toggle */}
                    <div className="mb-6 flex justify-center gap-4">
                        <Button
                            onClick={() => setShowTextChat(false)}
                            className={`glass-button px-6 py-2 rounded-2xl transition-all duration-300 ${
                                !showTextChat 
                                    ? "bg-blue-600/80 text-white" 
                                    : "bg-white/20 text-white/70 hover:bg-white/30"
                            }`}
                        >
                            <Mic className="mr-2 h-4 w-4" />
                            Vocal
                        </Button>
                        <Button
                            onClick={() => setShowTextChat(true)}
                            className={`glass-button px-6 py-2 rounded-2xl transition-all duration-300 ${
                                showTextChat 
                                    ? "bg-blue-600/80 text-white" 
                                    : "bg-white/20 text-white/70 hover:bg-white/30"
                            }`}
                        >
                            <MessageSquare className="mr-2 h-4 w-4" />
                            Texte
                        </Button>
                    </div>

                    {/* Voice Mode */}
                    {!showTextChat && (
                        <>
                            {/* Voice Selector - positioned like in Text mode */}
                            <div className="mb-6 flex justify-center">
                                <CompactVoiceSelector 
                                    selectedVoice={selectedRealtimeVoice}
                                    onVoiceChange={updateRealtimeVoice}
                                    mode="realtime"
                                />
                            </div>
                            
                            <div className="mb-6">
                                <Button
                                    onClick={onToggleListening}
                                    className={`h-20 w-20 rounded-full text-white font-semibold transition-all duration-300 transform hover:scale-105 ${
                                        isRecording 
                                            ? "bg-red-500/80 hover:bg-red-600/80 recording-pulse" 
                                            : "bg-blue-600/80 hover:bg-blue-700/80 pulse-glow glass-button"
                                    }`}
                                    aria-label={isRecording ? t("app.stopRecording") : t("app.startRecording")}
                                >
                                    {isRecording ? (
                                        <MicOff className="h-8 w-8" />
                                    ) : (
                                        <Mic className="h-8 w-8" />
                                    )}
                                </Button>
                            </div>
                            
                            <div className="mb-4">
                                {!isRecording ? (
                                    <Button
                                        onClick={onToggleListening}
                                        className="glass-button text-white font-semibold py-3 px-8 rounded-2xl transition-all duration-300"
                                    >
                                        <Mic className="mr-2 h-5 w-5" />
                                        Commencer la conversation
                                    </Button>
                                ) : (
                                    <Button
                                        onClick={onToggleListening}
                                        className="bg-red-500/80 hover:bg-red-600/80 text-white font-semibold py-3 px-8 rounded-2xl transition-all duration-300"
                                    >
                                        <MicOff className="mr-2 h-5 w-5" />
                                        Arrêter l'enregistrement
                                    </Button>
                                )}
                            </div>
                            
                            <StatusMessage isRecording={isRecording} />
                        </>
                    )}

                    {/* Text Mode */}
                    {showTextChat && (
                        <div className="space-y-4">
                            {/* Voice Selection */}
                            <div className="flex justify-center mb-4">
                                <CompactVoiceSelector 
                                    selectedVoice={selectedTextVoice}
                                    onVoiceChange={updateTextVoice}
                                    mode="text"
                                />
                            </div>
                            
                            <div className="flex gap-2">
                                <input
                                    type="text"
                                    value={textMessage}
                                    onChange={(e) => setTextMessage(e.target.value)}
                                    onKeyPress={(e) => {
                                        if (e.key === 'Enter' && !e.shiftKey && textMessage.trim() && !isGeneratingAudio) {
                                            e.preventDefault();
                                            sendMessageWithAudio(textMessage, true, selectedTextVoice);
                                            setTextMessage("");
                                        }
                                    }}
                                    placeholder="Tapez votre message ici..."
                                    disabled={isGeneratingAudio}
                                    className="flex-1 px-4 py-3 rounded-2xl bg-white/20 text-white placeholder-white/60 border border-white/30 focus:outline-none focus:ring-2 focus:ring-blue-400 focus:border-transparent"
                                />
                                <Button
                                    onClick={() => {
                                        if (textMessage.trim() && !isGeneratingAudio) {
                                            sendMessageWithAudio(textMessage, true, selectedTextVoice);
                                            setTextMessage("");
                                        }
                                    }}
                                    disabled={!textMessage.trim() || isGeneratingAudio}
                                    className="glass-button text-white px-4 py-3 rounded-2xl transition-all duration-300 disabled:opacity-50"
                                >
                                    {isGeneratingAudio ? (
                                        <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                                    ) : (
                                        <Send className="h-5 w-5" />
                                    )}
                                </Button>
                            </div>
                            
                            {/* Chat Messages Display */}
                            {chatMessages.length > 0 && (
                                <div className="max-h-60 overflow-y-auto space-y-2 bg-white/10 rounded-2xl p-4">
                                    {chatMessages.map((message, index) => (
                                        <div
                                            key={index}
                                            className={`p-3 rounded-xl ${
                                                message.role === 'user'
                                                    ? 'bg-blue-600/80 text-white ml-8'
                                                    : 'bg-white/20 text-white mr-8'
                                            }`}
                                        >
                                            <div className="text-sm opacity-70 mb-1 flex items-center gap-2">
                                                <span>{message.role === 'user' ? 'Vous' : 'Assistant'}</span>
                                                {message.role === 'assistant' && message.audio && (
                                                    <div className="flex items-center gap-1 text-xs bg-blue-500/30 px-2 py-1 rounded-full">
                                                        <Volume2 className="w-3 h-3" />
                                                        <span>Audio</span>
                                                    </div>
                                                )}
                                            </div>
                                            <div className="whitespace-pre-wrap">{message.content}</div>
                                            {message.role === 'assistant' && message.audioTranscript && (
                                                <div className="text-xs text-white/60 mt-2 italic border-l-2 border-white/30 pl-2">
                                                    Transcription audio: "{message.audioTranscript}"
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                            
                            {/* Audio Player */}
                            {(lastAudioData || isGeneratingAudio) && (
                                <AudioPlayer 
                                    audioData={lastAudioData || undefined}
                                    audioFormat={lastAudioFormat || 'mp3'}
                                    voice={lastVoice || selectedTextVoice}
                                    transcript={lastAudioTranscript || undefined}
                                    isLoading={isGeneratingAudio && !lastAudioData}
                                />
                            )}
                            
                            <p className="text-white/70 text-sm">
                                💡 Tapez votre question et recevez une réponse audio générée par GPT-Audio
                            </p>
                        </div>
                    )}
                </div>

                {/* Grounding files section */}
                <div className="w-full max-w-4xl">
                    <GroundingFiles files={groundingFiles} onSelected={setSelectedFile} />
                </div>

                {/* RAG Sources Display */}
                {ragSources.length > 0 && (
                    <div className="w-full max-w-4xl">
                        <RagSourceDisplay 
                            sources={ragSources} 
                            className="glass-card rounded-2xl p-4"
                        />
                    </div>
                )}
            </main>

            {/* Footer */}
            <footer className="absolute bottom-0 left-0 right-0 z-10 pb-4">
                <div className="text-center">
                    <div className="glass-card rounded-2xl inline-block px-6 py-3">
                        <p className="text-white/90 font-medium">{t("app.footer")}</p>
                    </div>
                </div>
            </footer>

            {/* File viewer */}
            <GroundingFileView groundingFile={selectedFile} onClosed={() => setSelectedFile(null)} />

            {/* Floating Icons Bar */}
            <FloatingIconsBar 
                onTelemetryClick={() => setIsTelemetryVisible(!isTelemetryVisible)}
                onTranscriptClick={() => setIsTranscriptVisible(!isTranscriptVisible)}
                isTelemetryActive={isTelemetryVisible}
                isTranscriptActive={isTranscriptVisible}
            />

            {/* Telemetry Panel */}
            <TelemetryPanel 
                isVisible={isTelemetryVisible}
                onToggle={() => setIsTelemetryVisible(false)}
            />
            
            {/* Transcript Panel */}
            <TranscriptPanel 
                isRecording={isRecording}
                currentUserInput={currentUserTranscript}
                currentAssistantResponse={currentAssistantTranscript}
                userMessages={completedUserMessages}
                assistantMessages={completedAssistantMessages}
                isVisible={isTranscriptVisible}
                onToggle={() => setIsTranscriptVisible(false)}
            />

            {/* Enhanced Grounding Display */}
            {enhancedGrounding && (
                <EnhancedGroundingDisplay
                    sources={enhancedGrounding.sources}
                    grounding_info={enhancedGrounding.grounding_info}
                    isVisible={isGroundingVisible}
                    onToggle={() => setIsGroundingVisible(false)}
                />
            )}

            {/* Call History Popup */}
            {callHistoryMetadata && (
                <CallHistoryPopup
                    isVisible={isCallHistoryVisible}
                    onClose={() => setIsCallHistoryVisible(false)}
                    customer={callHistoryMetadata.customer}
                    callHistory={callHistoryMetadata.call_history}
                    title="Historique des appels client"
                />
            )}

            {/* Floating Theme Selector */}
            <FloatingThemeButton />
        </div>
    );
}

export default App;

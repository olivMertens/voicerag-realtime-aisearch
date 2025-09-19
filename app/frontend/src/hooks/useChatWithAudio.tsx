import { useState, useCallback } from "react";

interface ChatMessage {
    role: "user" | "assistant";
    content: string;
    timestamp: Date;
    audio?: string; // base64 encoded audio data
    audioFormat?: string; // mp3, wav
    audioTranscript?: string;
    audioId?: string;
    voice?: string;
}

interface UseChatWithAudioParams {
    onNewMessage?: (message: ChatMessage) => void;
    onAudioReceived?: (audioData: string, format: string, transcript?: string) => void;
    onError?: (error: string) => void;
    onContentSafetyError?: (errorDetails: { message: string; reason?: string; action?: string; documentation?: string }) => void;
}

interface ChatApiResponse {
    message: string;
    audio?: string; // base64 encoded audio
    audio_format?: string; // mp3, wav
    audio_transcript?: string;
    audio_id?: string;
    role: string;
    tokens_used?: number;
    model: string;
    error?: string;
    error_type?: string;
    details?: {
        reason?: string;
        action?: string;
        documentation?: string;
    };
}

interface UseChatWithAudioReturn {
    messages: ChatMessage[];
    isLoading: boolean;
    isGeneratingAudio: boolean;
    sendMessage: (message: string, generateAudio?: boolean, voice?: string) => Promise<ChatMessage | null>;
    clearMessages: () => void;
    lastAudioData: string | null;
    lastAudioFormat: string | null;
    lastAudioTranscript: string | null;
    lastVoice: string | null;
}

export function useChatWithAudio({ onNewMessage, onAudioReceived, onError, onContentSafetyError }: UseChatWithAudioParams = {}): UseChatWithAudioReturn {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isGeneratingAudio, setIsGeneratingAudio] = useState(false);
    const [lastAudioData, setLastAudioData] = useState<string | null>(null);
    const [lastAudioFormat, setLastAudioFormat] = useState<string | null>(null);
    const [lastAudioTranscript, setLastAudioTranscript] = useState<string | null>(null);
    const [lastVoice, setLastVoice] = useState<string | null>(null);

    const sendMessage = useCallback(
        async (message: string, generateAudio: boolean = true, voice: string = "alloy"): Promise<ChatMessage | null> => {
            if (!message.trim() || isLoading) return null;

            const userMessage: ChatMessage = {
                role: "user",
                content: message.trim(),
                timestamp: new Date()
            };

            // Add user message to state
            setMessages(prev => [...prev, userMessage]);
            onNewMessage?.(userMessage);

            setIsLoading(true);
            if (generateAudio) {
                setIsGeneratingAudio(true);
            }

            try {
                // Prepare conversation history for API
                const conversationHistory = messages.map(msg => ({
                    role: msg.role,
                    content: msg.content
                }));

                // Call the chat API with audio generation support
                const response = await fetch("/api/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        message: message.trim(),
                        history: conversationHistory,
                        generate_audio: generateAudio,
                        voice: voice
                    })
                });

                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }

                const data: ChatApiResponse = await response.json();

                // Check for content safety violations first
                if (data.error === "content_safety_violation" || data.error_type === "content_filter") {
                    onContentSafetyError?.({
                        message: data.message || "Contenu non autorisé détecté",
                        reason: data.details?.reason,
                        action: data.details?.action,
                        documentation: data.details?.documentation
                    });
                    return null;
                }

                if (data.error) {
                    throw new Error(data.error);
                }

                const assistantMessage: ChatMessage = {
                    role: "assistant",
                    content: data.message || (data.audio ? data.audio_transcript || "Réponse audio générée" : "No response received"),
                    timestamp: new Date(),
                    audio: data.audio,
                    audioFormat: data.audio_format || "mp3",
                    audioTranscript: data.audio_transcript,
                    audioId: data.audio_id,
                    voice: voice
                };

                // Add assistant response to state
                setMessages(prev => [...prev, assistantMessage]);
                onNewMessage?.(assistantMessage);

                // Handle audio data if available
                if (data.audio && generateAudio) {
                    setLastAudioData(data.audio);
                    setLastAudioFormat(data.audio_format || "mp3");
                    setLastAudioTranscript(data.audio_transcript || null);
                    setLastVoice(voice);

                    onAudioReceived?.(data.audio, data.audio_format || "mp3", data.audio_transcript);

                    console.log("🎵 Audio received:", {
                        format: data.audio_format || "mp3",
                        voice: voice,
                        transcript: data.audio_transcript,
                        size: data.audio.length
                    });
                }

                return assistantMessage;
            } catch (error) {
                console.error("Chat error:", error);

                const errorMessage = error instanceof Error ? error.message : "Unknown error";
                onError?.(errorMessage);

                const errorResponse: ChatMessage = {
                    role: "assistant",
                    content: `Sorry, I encountered an error: ${errorMessage}`,
                    timestamp: new Date()
                };

                setMessages(prev => [...prev, errorResponse]);
                onNewMessage?.(errorResponse);

                return null;
            } finally {
                setIsLoading(false);
                setIsGeneratingAudio(false);
            }
        },
        [messages, isLoading, onNewMessage, onAudioReceived, onError]
    );

    const clearMessages = useCallback(() => {
        setMessages([]);
        setLastAudioData(null);
        setLastAudioFormat(null);
        setLastAudioTranscript(null);
        setLastVoice(null);
    }, []);

    return {
        messages,
        isLoading,
        isGeneratingAudio,
        sendMessage,
        clearMessages,
        lastAudioData,
        lastAudioFormat,
        lastAudioTranscript,
        lastVoice
    };
}

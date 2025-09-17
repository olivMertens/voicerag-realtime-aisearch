import { useState, useCallback } from 'react';

interface ChatMessage {
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    audio?: string; // base64 encoded audio data
}

interface UseChatParams {
    onNewMessage?: (message: ChatMessage) => void;
    onAudioReceived?: (audioBase64: string) => void;
}

interface ChatApiResponse {
    message: string;
    audio?: string; // base64 encoded audio
    audio_format?: string; // mp3, wav format
    audio_transcript?: string;
    audio_id?: string;
    sources?: any[];
    error?: string;
}

interface UseChatReturn {
    messages: ChatMessage[];
    isLoading: boolean;
    sendMessage: (message: string) => Promise<void>;
    clearMessages: () => void;
}

export default function useChat({ onNewMessage, onAudioReceived }: UseChatParams = {}): UseChatReturn {
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const sendMessage = useCallback(async (message: string) => {
        if (!message.trim() || isLoading) return;

        const userMessage: ChatMessage = {
            role: 'user',
            content: message.trim(),
            timestamp: new Date()
        };

        // Add user message to state
        setMessages(prev => [...prev, userMessage]);
        onNewMessage?.(userMessage);

        setIsLoading(true);

        try {
            // Prepare conversation history for API
            const conversationHistory = messages.map(msg => ({
                role: msg.role,
                content: msg.content
            }));

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message.trim(),
                    history: conversationHistory,
                    generate_audio: true, // Always request audio generation for text mode
                    voice: 'alloy' // Default voice, will be overridden by voice selector
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data: ChatApiResponse = await response.json();

            if (data.error) {
                throw new Error(data.error);
            }

            const assistantMessage: ChatMessage = {
                role: 'assistant',
                content: data.message || 'No response received',
                timestamp: new Date(),
                audio: data.audio
            };

            // Add assistant response to state
            setMessages(prev => [...prev, userMessage, assistantMessage]);
            onNewMessage?.(assistantMessage);

            // Play audio if available
            if (data.audio && onAudioReceived) {
                onAudioReceived(data.audio);
            }

        } catch (error) {
            console.error('Chat error:', error);
            
            const errorMessage: ChatMessage = {
                role: 'assistant',
                content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}`,
                timestamp: new Date()
            };

            setMessages(prev => [...prev, userMessage, errorMessage]);
            onNewMessage?.(errorMessage);
        } finally {
            setIsLoading(false);
        }
    }, [messages, isLoading, onNewMessage]);

    const clearMessages = useCallback(() => {
        setMessages([]);
    }, []);

    return {
        messages,
        isLoading,
        sendMessage,
        clearMessages,
    };
}
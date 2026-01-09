import React, { useState, useEffect, useRef } from "react";
import { MessageSquare, User, Bot, Mic, MicOff, Download } from "lucide-react";
import UserTranscriptCapture from "./user-transcript-capture";
import { useTranslation } from "react-i18next";

interface TranscriptMessage {
    id: string;
    type: "user" | "assistant";
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
    currentUserInput = "",
    currentAssistantResponse = "",
    userMessages = [],
    assistantMessages = [],
    isVisible,
    onToggle
}) => {
    const { t } = useTranslation();
    const [messages, setMessages] = useState<TranscriptMessage[]>([]);
    const [activeTab, setActiveTab] = useState<"realtime" | "capture">("realtime");
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
                    type: "user",
                    content: userMessages[i],
                    timestamp: Date.now() - (maxLength - i) * 1000,
                    isComplete: true
                });
            }

            if (i < assistantMessages.length && assistantMessages[i]) {
                allMessages.push({
                    id: `assistant-${i}`,
                    type: "assistant",
                    content: assistantMessages[i],
                    timestamp: Date.now() - (maxLength - i) * 1000 + 500,
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
                id: "current-user",
                type: "user" as const,
                content: `utilisateur : "${currentUserInput}"`,
                timestamp: Date.now(),
                isComplete: false
            });
        }

        // Add current assistant response if exists
        if (currentAssistantResponse) {
            allTranscriptMessages.push({
                id: "current-assistant",
                type: "assistant" as const,
                content: currentAssistantResponse,
                timestamp: Date.now(),
                isComplete: false
            });
        }

        console.log("📝 Downloading transcript with messages:", allTranscriptMessages.length);

        if (allTranscriptMessages.length === 0) {
            alert(t("transcript.noTranscriptToDownload"));
            return;
        }

        const transcriptText = allTranscriptMessages
            .map(message => {
                const timestamp = new Date(message.timestamp).toLocaleString();
                const role = message.type === "user" ? t("transcript.roleUser") : t("transcript.roleAssistant");
                return `[${timestamp}] ${role}: ${message.content}`;
            })
            .join("\n\n");

        const blob = new Blob([transcriptText], { type: "text/plain" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `transcript-${new Date().toISOString().split("T")[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        console.log("✅ Transcript downloaded successfully");
    };

    const handleUserTranscript = (transcript: string) => {
        // Add to messages list with formatted display
        const newMessage: TranscriptMessage = {
            id: `captured-${Date.now()}`,
            type: "user",
            content: `"${transcript}"`, // Format as requested by user
            timestamp: Date.now(),
            isComplete: true
        };
        setMessages(prev => [...prev, newMessage]);
    };

    return (
        <>
            {/* Transcript panel */}
            <div
                className={`glass fixed bottom-20 left-6 z-40 flex h-[70vh] w-96 flex-col rounded-xl border-white/20 transition-all duration-300 ${
                    isVisible ? "pointer-events-auto translate-x-0 opacity-100" : "pointer-events-none -translate-x-full opacity-0"
                }`}
            >
                {/* Header */}
                <div className="border-b border-white/10 p-4">
                    <div className="mb-3 flex items-center justify-between">
                        <h3 className="flex items-center gap-2 font-semibold text-white">
                            <MessageSquare className="h-4 w-4" />
                            {t("transcript.title")}
                            {isRecording && <Mic className="h-4 w-4 animate-pulse text-red-400" />}
                            {!isRecording && <MicOff className="h-4 w-4 text-gray-400" />}
                        </h3>
                        <div className="flex items-center gap-2">
                            <button
                                onClick={e => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    console.log("📥 Download button clicked");
                                    downloadTranscript();
                                }}
                                className="interactive-button relative z-50 rounded-full p-2 transition-all duration-200 hover:bg-white/20"
                                title={t("transcript.download")}
                                type="button"
                            >
                                <Download className="h-4 w-4 text-white/80 hover:text-white" />
                            </button>
                            <button
                                onClick={e => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    console.log("🗙 Closing transcript panel");
                                    onToggle();
                                }}
                                className="interactive-button relative z-50 rounded-full p-2 text-lg font-bold leading-none text-white/80 transition-all duration-200 hover:bg-white/20 hover:text-white"
                                title={t("transcript.close")}
                                type="button"
                            >
                                ×
                            </button>
                        </div>
                    </div>

                    {/* Tabs */}
                    <div className="flex border-b border-white/10">
                        <button
                            onClick={() => setActiveTab("realtime")}
                            className={`flex-1 px-3 py-1 text-sm font-medium transition-colors ${
                                activeTab === "realtime" ? "border-b-2 border-blue-400 text-blue-400" : "text-white/60 hover:text-white"
                            }`}
                        >
                            {t("transcript.tabRealtime")}
                        </button>
                        <button
                            onClick={() => setActiveTab("capture")}
                            className={`flex-1 px-3 py-1 text-sm font-medium transition-colors ${
                                activeTab === "capture" ? "border-b-2 border-blue-400 text-blue-400" : "text-white/60 hover:text-white"
                            }`}
                        >
                            {t("transcript.tabCapture")}
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden">
                    {/* Real-time Tab */}
                    {activeTab === "realtime" && (
                        <div ref={scrollRef} className="h-full space-y-3 overflow-y-auto p-4">
                            {messages.map(message => (
                                <div key={message.id} className={`flex gap-3 ${message.type === "assistant" ? "justify-start" : "justify-end"}`}>
                                    {message.type === "assistant" && (
                                        <div className="glass-card flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full">
                                            <Bot className="h-4 w-4 text-blue-400" />
                                        </div>
                                    )}

                                    <div
                                        className={`max-w-[80%] ${
                                            message.type === "assistant" ? "bg-blue-500/20 text-white" : "bg-white/20 text-white"
                                        } glass-card rounded-2xl px-4 py-2`}
                                    >
                                        <p className="text-sm leading-relaxed">{message.content}</p>
                                        <div className="mt-1 text-xs text-white/60">{new Date(message.timestamp).toLocaleTimeString()}</div>
                                    </div>

                                    {message.type === "user" && (
                                        <div className="glass-card flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full">
                                            <User className="h-4 w-4 text-green-400" />
                                        </div>
                                    )}
                                </div>
                            ))}

                            {/* Current user input (live) */}
                            {currentUserInput && (
                                <div className="flex justify-end gap-3">
                                    <div className="glass-card max-w-[80%] rounded-2xl border-2 border-green-400/30 bg-white/10 px-4 py-2 text-white/80">
                                        <p className="text-sm leading-relaxed">
                                            {t("transcript.userLivePrefix")}: "{currentUserInput}"
                                        </p>
                                        <div className="mt-1 flex items-center gap-1 text-xs text-green-400">
                                            <div className="h-2 w-2 animate-pulse rounded-full bg-green-400" />
                                            {t("transcript.inProgress")}
                                        </div>
                                    </div>
                                    <div className="glass-card flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 border-green-400/30">
                                        <User className="h-4 w-4 text-green-400" />
                                    </div>
                                </div>
                            )}

                            {/* Current assistant response (live) */}
                            {currentAssistantResponse && (
                                <div className="flex justify-start gap-3">
                                    <div className="glass-card flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full border-2 border-blue-400/30">
                                        <Bot className="h-4 w-4 text-blue-400" />
                                    </div>
                                    <div className="glass-card max-w-[80%] rounded-2xl border-2 border-blue-400/30 bg-blue-500/10 px-4 py-2 text-white/80">
                                        <p className="text-sm leading-relaxed">{currentAssistantResponse}</p>
                                        <div className="mt-1 flex items-center gap-1 text-xs text-blue-400">
                                            <div className="h-2 w-2 animate-pulse rounded-full bg-blue-400" />
                                            {t("transcript.generating")}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {messages.length === 0 && !currentUserInput && !currentAssistantResponse && (
                                <div className="p-8 text-center text-white/60">
                                    <MessageSquare className="mx-auto mb-2 h-8 w-8 opacity-50" />
                                    <p className="text-sm">{t("transcript.empty")}</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Speech Capture Tab */}
                    {activeTab === "capture" && (
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

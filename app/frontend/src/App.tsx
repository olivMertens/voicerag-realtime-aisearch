import { useState } from "react";
import { Mic, MicOff, Shield, Sparkles, Zap } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Button } from "@/components/ui/button";
import { GroundingFiles } from "@/components/ui/grounding-files";
import GroundingFileView from "@/components/ui/grounding-file-view";
import StatusMessage from "@/components/ui/status-message";
import { TelemetryPanel } from "@/components/ui/telemetry-panel";

import useRealTime from "@/hooks/useRealtime";
import useAudioRecorder from "@/hooks/useAudioRecorder";
import useAudioPlayer from "@/hooks/useAudioPlayer";

import { GroundingFile, ToolResult } from "./types";

function App() {
    const [isRecording, setIsRecording] = useState(false);
    const [groundingFiles, setGroundingFiles] = useState<GroundingFile[]>([]);
    const [selectedFile, setSelectedFile] = useState<GroundingFile | null>(null);

    const { startSession, addUserAudio, inputAudioBufferClear } = useRealTime({
        onWebSocketOpen: () => console.log("WebSocket connection opened"),
        onWebSocketClose: () => console.log("WebSocket connection closed"),
        onWebSocketError: event => console.error("WebSocket error:", event),
        onReceivedError: message => console.error("error", message),
        onReceivedResponseAudioDelta: message => {
            isRecording && playAudio(message.delta);
        },
        onReceivedInputAudioBufferSpeechStarted: () => {
            stopAudioPlayer();
        },
        onReceivedExtensionMiddleTierToolResponse: message => {
            const result: ToolResult = JSON.parse(message.tool_result);

            const files: GroundingFile[] = result.sources.map(x => {
                return { id: x.chunk_id, name: x.title, content: x.chunk };
            });

            setGroundingFiles(prev => [...prev, ...files]);
        }
    });

    const { reset: resetAudioPlayer, play: playAudio, stop: stopAudioPlayer } = useAudioPlayer();
    const { start: startAudioRecording, stop: stopAudioRecording } = useAudioRecorder({ onAudioRecorded: addUserAudio });

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

    const { t } = useTranslation();

    return (
        <div className="min-h-screen relative overflow-hidden">
            {/* Floating background elements */}
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
                <div className="absolute top-20 left-10 w-64 h-64 bg-white/10 rounded-full blur-3xl floating-element"></div>
                <div className="absolute top-40 right-16 w-96 h-96 bg-blue-400/10 rounded-full blur-3xl floating-element" style={{ animationDelay: '2s' }}></div>
                <div className="absolute bottom-20 left-1/3 w-80 h-80 bg-purple-400/10 rounded-full blur-3xl floating-element" style={{ animationDelay: '4s' }}></div>
            </div>

            {/* Header with logo */}
            <header className="relative z-10">
                <div className="absolute top-6 left-6 glass-card rounded-2xl p-4 floating-element">
                    <Shield className="h-16 w-16 text-white drop-shadow-lg" />
                </div>
                
                {/* Top right decorative elements */}
                <div className="absolute top-8 right-8 flex gap-4">
                    <div className="glass-card rounded-full p-3 floating-element">
                        <Sparkles className="h-6 w-6 text-white/80" />
                    </div>
                    <div className="glass-card rounded-full p-3 floating-element" style={{ animationDelay: '1s' }}>
                        <Zap className="h-6 w-6 text-white/80" />
                    </div>
                </div>
            </header>

            <main className="flex flex-col items-center justify-center min-h-screen relative z-10 px-6">
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
                </div>

                {/* Grounding files section */}
                <div className="w-full max-w-4xl">
                    <GroundingFiles files={groundingFiles} onSelected={setSelectedFile} />
                </div>
            </main>

            {/* Footer */}
            <footer className="relative z-10 pb-6">
                <div className="text-center">
                    <div className="glass-card rounded-2xl inline-block px-6 py-3">
                        <p className="text-white/90 font-medium">{t("app.footer")}</p>
                    </div>
                </div>
            </footer>

            {/* File viewer */}
            <GroundingFileView groundingFile={selectedFile} onClosed={() => setSelectedFile(null)} />

            {/* Telemetry Panel */}
            <TelemetryPanel />
        </div>
    );
}

export default App;

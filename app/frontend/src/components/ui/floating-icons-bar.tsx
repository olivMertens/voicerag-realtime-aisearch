import React, { useState } from "react";
import { Activity, MessageSquare, Palette, Plus, RotateCcw } from "lucide-react";
import { useTheme } from "../../contexts/ThemeContext";
import ThemeSelector from "./theme-selector";
import { Button } from "./button";

interface FloatingIconsBarProps {
    onTelemetryClick: () => void;
    onTranscriptClick: () => void;
    onNewSessionClick: () => void;
    onRestartClick: () => void;
    isTelemetryActive: boolean;
    isTranscriptActive: boolean;
}

export const FloatingIconsBar: React.FC<FloatingIconsBarProps> = ({
    onTelemetryClick,
    onTranscriptClick,
    onNewSessionClick,
    onRestartClick,
    isTelemetryActive,
    isTranscriptActive
}) => {
    const [showThemeSelector, setShowThemeSelector] = useState(false);
    const { theme } = useTheme();

    const getThemeButtonStyle = () => {
        switch (theme) {
            case "white":
                return "bg-white/90 text-slate-700 border-slate-200 hover:bg-white";
            case "black":
                return "bg-slate-900/90 text-slate-100 border-slate-700 hover:bg-slate-800/90";
            default:
                return "glass-card text-white hover:bg-white/20";
        }
    };

    return (
        <div className="fixed bottom-6 left-6 z-30">
            {/* Theme Selector Panel */}
            {showThemeSelector && (
                <div className="mb-4 transform transition-all duration-300 ease-out">
                    <ThemeSelector />
                </div>
            )}

            {/* All Icons Row */}
            <div className="glass-card flex items-center gap-3 rounded-2xl p-3">
                {/* New Session Button */}
                <Button
                    onClick={onNewSessionClick}
                    className="glass-button floating-element group cursor-pointer rounded-full p-3 transition-all duration-300 hover:bg-white/10"
                    title="Nouvelle session"
                    style={{ pointerEvents: "auto" }}
                >
                    <Plus className="h-6 w-6 text-white transition-transform duration-200 group-hover:scale-110" />
                </Button>

                {/* Restart Conversation Button */}
                <Button
                    onClick={onRestartClick}
                    className="glass-button floating-element group cursor-pointer rounded-full p-3 transition-all duration-300 hover:bg-white/10"
                    title="Redémarrer la conversation"
                    style={{ pointerEvents: "auto" }}
                >
                    <RotateCcw className="h-6 w-6 text-white transition-transform duration-200 group-hover:rotate-180" />
                </Button>

                {/* Separator */}
                <div className="h-8 w-px bg-white/20"></div>

                {/* Transcript Button */}
                <button
                    onClick={onTranscriptClick}
                    className={`glass-button rounded-full p-3 transition-all duration-300 hover:bg-white/10 ${
                        isTranscriptActive ? "bg-blue-500/20 ring-2 ring-blue-400/30" : ""
                    }`}
                    title="Toggle transcript"
                >
                    <MessageSquare className="h-6 w-6 text-white" />
                </button>

                {/* Telemetry Button */}
                <button
                    onClick={onTelemetryClick}
                    className={`glass-button rounded-full p-3 transition-all duration-300 hover:bg-white/10 ${
                        isTelemetryActive ? "bg-green-500/20 ring-2 ring-green-400/30" : ""
                    }`}
                    title="Ouvrir le panneau de télémétrie"
                >
                    <Activity className="h-6 w-6 text-white" />
                </button>

                {/* Theme Selector Button */}
                <button
                    onClick={() => setShowThemeSelector(!showThemeSelector)}
                    className={`transform rounded-full border p-3 backdrop-blur-md transition-all duration-300 hover:scale-105 ${getThemeButtonStyle()} `}
                    title="Changer le thème"
                >
                    <Palette className={`h-6 w-6 transition-transform duration-300 ${showThemeSelector ? "rotate-180" : "hover:rotate-12"} `} />
                </button>
            </div>

            {/* Backdrop to close theme selector */}
            {showThemeSelector && <div className="fixed inset-0 -z-10" onClick={() => setShowThemeSelector(false)} />}
        </div>
    );
};

export default FloatingIconsBar;

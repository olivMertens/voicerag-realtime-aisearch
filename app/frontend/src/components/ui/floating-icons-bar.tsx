import React from 'react';
import { Activity, MessageSquare } from 'lucide-react';

interface FloatingIconsBarProps {
  onTelemetryClick: () => void;
  onTranscriptClick: () => void;
  isTelemetryActive: boolean;
  isTranscriptActive: boolean;
}

export const FloatingIconsBar: React.FC<FloatingIconsBarProps> = ({
  onTelemetryClick,
  onTranscriptClick,
  isTelemetryActive,
  isTranscriptActive
}) => {
  return (
    <div className="fixed bottom-6 left-6 z-30 flex items-center gap-3">
      {/* Transcript Button */}
      <button
        onClick={onTranscriptClick}
        className={`glass-card rounded-full p-4 hover:bg-white/10 transition-all duration-300 ${
          isTranscriptActive ? 'bg-blue-500/20 ring-2 ring-blue-400/30' : ''
        }`}
        title="Toggle transcript"
      >
        <MessageSquare className="h-6 w-6 text-white" />
      </button>

      {/* Telemetry Button */}
      <button
        onClick={onTelemetryClick}
        className={`glass-card rounded-full p-4 hover:bg-white/10 transition-all duration-300 ${
          isTelemetryActive ? 'bg-green-500/20 ring-2 ring-green-400/30' : ''
        }`}
        title="Ouvrir le panneau de télémétrie"
      >
        <Activity className="h-6 w-6 text-white" />
      </button>
    </div>
  );
};

export default FloatingIconsBar;
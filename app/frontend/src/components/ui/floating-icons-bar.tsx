import React, { useState } from 'react';
import { Activity, MessageSquare, Palette } from 'lucide-react';
import { useTheme } from '../../contexts/ThemeContext';
import ThemeSelector from './theme-selector';

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
  const [showThemeSelector, setShowThemeSelector] = useState(false);
  const { theme } = useTheme();

  const getThemeButtonStyle = () => {
    switch (theme) {
      case 'white':
        return 'bg-white/90 text-slate-700 border-slate-200 hover:bg-white';
      case 'black':
        return 'bg-slate-900/90 text-slate-100 border-slate-700 hover:bg-slate-800/90';
      default:
        return 'glass-card text-white hover:bg-white/20';
    }
  };

  return (
    <div className="fixed bottom-6 left-72 z-30">
      {/* Theme Selector Panel */}
      {showThemeSelector && (
        <div className="mb-4 transform transition-all duration-300 ease-out">
          <ThemeSelector />
        </div>
      )}
      
      {/* Icons Row */}
      <div className="flex items-center gap-3">
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

        {/* Theme Selector Button */}
        <button
          onClick={() => setShowThemeSelector(!showThemeSelector)}
          className={`
            p-4 rounded-full transition-all duration-300 
            transform hover:scale-105 border backdrop-blur-md
            ${getThemeButtonStyle()}
          `}
          title="Changer le thème"
        >
          <Palette className={`
            h-6 w-6 transition-transform duration-300 
            ${showThemeSelector ? 'rotate-180' : 'hover:rotate-12'}
          `} />
        </button>
      </div>
      
      {/* Backdrop to close theme selector */}
      {showThemeSelector && (
        <div 
          className="fixed inset-0 -z-10"
          onClick={() => setShowThemeSelector(false)}
        />
      )}
    </div>
  );
};

export default FloatingIconsBar;
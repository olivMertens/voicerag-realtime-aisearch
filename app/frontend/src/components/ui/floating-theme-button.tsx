import React, { useState } from 'react';
import { Palette } from 'lucide-react';
import ThemeSelector from './theme-selector';
import { useTheme } from '../../contexts/ThemeContext';

const FloatingThemeButton: React.FC = () => {
    const [showSelector, setShowSelector] = useState(false);
    const { theme } = useTheme();

    const getButtonStyle = () => {
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
        <div className="fixed bottom-6 left-6 z-50">
            {/* Theme Selector Panel */}
            {showSelector && (
                <div className="mb-4 transform transition-all duration-300 ease-out">
                    <ThemeSelector />
                </div>
            )}
            
            {/* Floating Theme Button */}
            <button
                onClick={() => setShowSelector(!showSelector)}
                className={`
                    p-4 rounded-2xl transition-all duration-300 
                    transform hover:scale-105 floating-element group
                    border backdrop-blur-md
                    ${getButtonStyle()}
                `}
                title="Changer le thème"
            >
                <Palette className={`
                    h-6 w-6 transition-transform duration-300 
                    ${showSelector ? 'rotate-180' : 'group-hover:rotate-12'}
                `} />
            </button>
            
            {/* Backdrop to close selector */}
            {showSelector && (
                <div 
                    className="fixed inset-0 -z-10"
                    onClick={() => setShowSelector(false)}
                />
            )}
        </div>
    );
};

export default FloatingThemeButton;
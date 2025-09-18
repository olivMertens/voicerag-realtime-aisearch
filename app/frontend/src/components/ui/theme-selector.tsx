import React from 'react';
import { Palette, Check } from 'lucide-react';
import { useTheme, Theme } from '../../contexts/ThemeContext';

const ThemeSelector: React.FC = () => {
    const { theme, setTheme } = useTheme();

    const themes: { key: Theme; name: string; preview: string; description: string }[] = [
        {
            key: 'glass',
            name: 'Verre',
            preview: 'linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.05) 100%)',
            description: 'Effet glassmorphisme moderne'
        },
        {
            key: 'white',
            name: 'Blanc',
            preview: 'linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%)',
            description: 'Thème clair et minimaliste'
        },
        {
            key: 'black',
            name: 'Noir',
            preview: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)',
            description: 'Thème sombre élégant'
        }
    ];

    return (
        <div className="glass-card rounded-2xl p-4 w-80">
            <div className="flex items-center gap-2 mb-4">
                <Palette className="h-5 w-5 text-blue-400" />
                <h3 className="font-semibold text-white">Thème de l'interface</h3>
            </div>
            
            <div className="space-y-3">
                {themes.map((themeOption) => (
                    <button
                        key={themeOption.key}
                        onClick={() => setTheme(themeOption.key)}
                        className={`w-full p-3 rounded-xl transition-all duration-200 border-2 ${
                            theme === themeOption.key
                                ? 'border-blue-400 bg-white/10'
                                : 'border-white/10 hover:border-white/20 hover:bg-white/5'
                        }`}
                    >
                        <div className="flex items-center gap-3">
                            {/* Theme preview circle */}
                            <div 
                                className="w-8 h-8 rounded-full border-2 border-white/20 flex items-center justify-center"
                                style={{ 
                                    background: themeOption.preview,
                                    backdropFilter: themeOption.key === 'glass' ? 'blur(10px)' : 'none'
                                }}
                            >
                                {theme === themeOption.key && (
                                    <Check className="h-4 w-4 text-white font-bold" />
                                )}
                            </div>
                            
                            <div className="flex-1 text-left">
                                <div className="font-medium text-white">{themeOption.name}</div>
                                <div className="text-sm text-white/60">{themeOption.description}</div>
                            </div>
                        </div>
                    </button>
                ))}
            </div>
            
            <div className="mt-4 pt-3 border-t border-white/10">
                <p className="text-xs text-white/50 text-center">
                    Le thème est automatiquement sauvegardé
                </p>
            </div>
        </div>
    );
};

export default ThemeSelector;
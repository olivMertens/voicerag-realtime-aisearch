import React, { createContext, useContext, useEffect, useState } from 'react';

export type Theme = 'glass' | 'white' | 'black';

interface ThemeContextType {
    theme: Theme;
    setTheme: (theme: Theme) => void;
    toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (context === undefined) {
        throw new Error('useTheme must be used within a ThemeProvider');
    }
    return context;
};

interface ThemeProviderProps {
    children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
    const [theme, setThemeState] = useState<Theme>(() => {
        // Try to get theme from localStorage
        const savedTheme = localStorage.getItem('app-theme') as Theme;
        return savedTheme && ['glass', 'white', 'black'].includes(savedTheme) ? savedTheme : 'glass';
    });

    const setTheme = (newTheme: Theme) => {
        setThemeState(newTheme);
        localStorage.setItem('app-theme', newTheme);
        
        // Apply theme class to document body
        document.body.className = document.body.className
            .replace(/theme-\w+/g, '') // Remove existing theme classes
            .concat(` theme-${newTheme}`)
            .trim();
    };

    const toggleTheme = () => {
        const themes: Theme[] = ['glass', 'white', 'black'];
        const currentIndex = themes.indexOf(theme);
        const nextIndex = (currentIndex + 1) % themes.length;
        setTheme(themes[nextIndex]);
    };

    useEffect(() => {
        // Apply initial theme class to body
        document.body.className = document.body.className
            .replace(/theme-\w+/g, '') // Remove existing theme classes
            .concat(` theme-${theme}`)
            .trim();
    }, [theme]);

    const value = {
        theme,
        setTheme,
        toggleTheme
    };

    return (
        <ThemeContext.Provider value={value}>
            {children}
        </ThemeContext.Provider>
    );
};
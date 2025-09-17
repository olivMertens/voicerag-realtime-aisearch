import React from 'react';
import { Card } from './card';

interface RagSource {
  id: string;
  content: string;
  title: string;
  category: string;
  excerpt: string;
}

interface RagSourceDisplayProps {
  sources: RagSource[];
  className?: string;
}

export const RagSourceDisplay: React.FC<RagSourceDisplayProps> = ({ sources, className = "" }) => {
  if (!sources || sources.length === 0) {
    return null;
  }

  return (
    <div className={`space-y-3 ${className}`}>
      <h4 className="text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
        📚 Sources consultées
      </h4>
      {sources.map((source, index) => (
        <Card key={`${source.id}-${index}`} className="p-3 bg-blue-50/80 dark:bg-blue-950/20 border-blue-200/50 dark:border-blue-800/50">
          <div className="space-y-2">
            {/* Category and Title */}
            <div className="flex items-start justify-between gap-2">
              <div>
                {source.category && (
                  <span className="inline-block px-2 py-1 text-xs font-medium bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 rounded-full mb-1">
                    {source.category}
                  </span>
                )}
                {source.title && (
                  <h5 className="font-medium text-sm text-slate-800 dark:text-slate-200 leading-tight">
                    {source.title}
                  </h5>
                )}
              </div>
              <span className="text-xs text-slate-500 dark:text-slate-400 flex-shrink-0">
                #{source.id}
              </span>
            </div>

            {/* Excerpt */}
            <div className="text-sm text-slate-600 dark:text-slate-300 leading-relaxed">
              {source.excerpt}
            </div>

            {/* Expand button for full content if needed */}
            {source.content.length > 200 && (
              <button 
                className="text-xs text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-200 font-medium"
                onClick={() => {
                  // Toggle full content display (could be implemented with state)
                  console.log('Full content:', source.content);
                }}
              >
                Voir le contenu complet →
              </button>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
};

export default RagSourceDisplay;
import React, { useState } from 'react';
import { ChevronDown, ChevronRight, Copy, Eye, EyeOff } from 'lucide-react';

interface ToolCallDetailProps {
  call: {
    id: string;
    tool_name: string;
    args: Record<string, any>;
    response_preview?: string;
    timestamp: number;
    duration?: number;
    status: string;
  };
}

export const ToolCallDetail: React.FC<ToolCallDetailProps> = ({ call }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [showResponse, setShowResponse] = useState(false);

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  const formatArgs = (args: Record<string, any>) => {
    return JSON.stringify(args, null, 2);
  };

  return (
    <div className="glass-dark rounded-lg p-3 border-l-4 border-blue-500/50">
      {/* Header */}
      <div className="flex items-center justify-between mb-2">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2 text-sm font-medium text-white hover:text-blue-400 transition-colors"
        >
          {isExpanded ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          <span className="font-mono bg-blue-500/20 px-2 py-1 rounded text-xs">
            {call.tool_name}
          </span>
        </button>
        
        <div className="flex items-center gap-2 text-xs text-white/60">
          <span>{formatTimestamp(call.timestamp)}</span>
          {call.duration && (
            <span className="bg-green-500/20 px-2 py-1 rounded">
              {(call.duration * 1000).toFixed(0)}ms
            </span>
          )}
          <span className={`px-2 py-1 rounded ${
            call.status === 'completed' ? 'bg-green-500/20 text-green-400' : 
            call.status === 'running' ? 'bg-yellow-500/20 text-yellow-400' :
            'bg-red-500/20 text-red-400'
          }`}>
            {call.status}
          </span>
        </div>
      </div>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="space-y-3 mt-3 border-t border-white/10 pt-3">
          {/* Input Arguments */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-xs font-semibold text-white/80 uppercase tracking-wide">
                Input Arguments
              </h5>
              <button
                onClick={() => copyToClipboard(formatArgs(call.args))}
                className="p-1 hover:bg-white/10 rounded"
                title="Copy arguments"
              >
                <Copy className="h-3 w-3 text-white/60" />
              </button>
            </div>
            <div className="bg-black/30 rounded p-2 text-xs font-mono text-green-400 overflow-auto max-h-32">
              <pre>{formatArgs(call.args)}</pre>
            </div>
          </div>

          {/* Response */}
          {call.response_preview && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h5 className="text-xs font-semibold text-white/80 uppercase tracking-wide">
                  Response
                </h5>
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setShowResponse(!showResponse)}
                    className="p-1 hover:bg-white/10 rounded"
                    title={showResponse ? "Hide response" : "Show response"}
                  >
                    {showResponse ? <EyeOff className="h-3 w-3 text-white/60" /> : <Eye className="h-3 w-3 text-white/60" />}
                  </button>
                  <button
                    onClick={() => copyToClipboard(call.response_preview || '')}
                    className="p-1 hover:bg-white/10 rounded"
                    title="Copy response"
                  >
                    <Copy className="h-3 w-3 text-white/60" />
                  </button>
                </div>
              </div>
              
              {showResponse && (
                <div className="bg-black/30 rounded p-2 text-xs font-mono text-blue-400 overflow-auto max-h-32">
                  <pre>{call.response_preview}</pre>
                </div>
              )}
              
              {!showResponse && (
                <div className="bg-black/30 rounded p-2 text-xs text-white/60 italic">
                  Click the eye icon to view response content
                </div>
              )}
            </div>
          )}

          {/* Trace Info */}
          <div className="flex items-center justify-between text-xs text-white/50">
            <span>Trace ID: {call.id}</span>
            <span>Tool Execution</span>
          </div>
        </div>
      )}
    </div>
  );
};

export default ToolCallDetail;
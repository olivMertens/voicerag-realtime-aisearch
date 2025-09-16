import { useState, useEffect } from 'react';
import { Activity, Database, Search, Phone, Building, Clock, Zap, CheckCircle, AlertCircle } from 'lucide-react';

interface ToolCall {
    id: string;
    tool_name: string;
    args: Record<string, any>;
    timestamp: number;
    duration?: number;
    status: string;
}

interface ModelCall {
    id: string;
    model_name: string;
    operation: string;
    tokens_used?: number;
    latency?: number;
    cost?: number;
    timestamp: number;
    status: string;
}

interface TelemetryStats {
    total_tool_calls: number;
    total_model_calls: number;
    avg_tool_duration: number;
    avg_model_latency: number;
}

interface TelemetryData {
    tool_calls: ToolCall[];
    model_calls: ModelCall[];
    stats: TelemetryStats;
}

const getToolIcon = (toolName: string) => {
    switch (toolName) {
        case 'search': return <Search className="h-4 w-4" />;
        case 'get_policies': return <Database className="h-4 w-4" />;
        case 'get_claims': return <AlertCircle className="h-4 w-4" />;
        case 'get_agencies': return <Building className="h-4 w-4" />;
        case 'get_contact_info': return <Phone className="h-4 w-4" />;
        default: return <Activity className="h-4 w-4" />;
    }
};

const getStatusColor = (status: string) => {
    switch (status) {
        case 'completed': return 'text-green-400';
        case 'running': return 'text-yellow-400';
        case 'failed': return 'text-red-400';
        default: return 'text-gray-400';
    }
};

const formatDuration = (duration?: number) => {
    if (!duration) return 'N/A';
    if (duration < 1) return `${Math.round(duration * 1000)}ms`;
    return `${duration.toFixed(2)}s`;
};

export function TelemetryPanel() {
    const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
    const [isVisible, setIsVisible] = useState(false);
    const [isLoading, setIsLoading] = useState(false);

    const fetchTelemetryData = async () => {
        setIsLoading(true);
        try {
            const response = await fetch('/api/telemetry');
            if (response.ok) {
                const data = await response.json();
                setTelemetryData(data);
            }
        } catch (error) {
            console.error('Failed to fetch telemetry data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        if (isVisible) {
            fetchTelemetryData();
            const interval = setInterval(fetchTelemetryData, 2000); // Refresh every 2 seconds
            return () => clearInterval(interval);
        }
    }, [isVisible]);

    if (!isVisible) {
        return (
            <button
                onClick={() => setIsVisible(true)}
                className="fixed top-20 right-6 glass-card p-3 rounded-2xl text-white/80 hover:text-white transition-all duration-300 z-50 floating-element"
                title="Ouvrir le panneau de télémétrie"
            >
                <Activity className="h-6 w-6" />
            </button>
        );
    }

    return (
        <div className="fixed top-6 right-6 w-80 max-h-96 glass-card rounded-3xl p-4 text-white z-50 overflow-hidden">
            {/* Header */}
            <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-blue-400" />
                    <h3 className="font-semibold">Télémétrie</h3>
                </div>
                <button
                    onClick={() => setIsVisible(false)}
                    className="text-white/60 hover:text-white transition-colors"
                >
                    ×
                </button>
            </div>

            {isLoading ? (
                <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                </div>
            ) : telemetryData ? (
                <div className="space-y-4 overflow-y-auto max-h-80">
                    {/* Stats */}
                    <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="glass-dark rounded-lg p-2">
                            <div className="text-white/60">Outils</div>
                            <div className="font-semibold">{telemetryData.stats.total_tool_calls}</div>
                        </div>
                        <div className="glass-dark rounded-lg p-2">
                            <div className="text-white/60">Modèles</div>
                            <div className="font-semibold">{telemetryData.stats.total_model_calls}</div>
                        </div>
                    </div>

                    {/* Recent Tool Calls */}
                    {telemetryData.tool_calls.length > 0 && (
                        <div>
                            <h4 className="text-sm font-medium text-white/80 mb-2 flex items-center gap-1">
                                <Zap className="h-4 w-4" />
                                Appels d'outils récents
                            </h4>
                            <div className="space-y-1">
                                {telemetryData.tool_calls.slice(-5).reverse().map((call, index) => (
                                    <div key={call.id || index} className="glass-dark rounded-lg p-2 text-xs">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="flex items-center gap-1">
                                                {getToolIcon(call.tool_name)}
                                                <span className="font-medium">{call.tool_name}</span>
                                            </div>
                                            <div className={`flex items-center gap-1 ${getStatusColor(call.status)}`}>
                                                <CheckCircle className="h-3 w-3" />
                                                <span>{formatDuration(call.duration)}</span>
                                            </div>
                                        </div>
                                        {Object.keys(call.args).length > 0 && (
                                            <div className="text-white/60 truncate">
                                                {JSON.stringify(call.args).substring(0, 50)}...
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Recent Model Calls */}
                    {telemetryData.model_calls.length > 0 && (
                        <div>
                            <h4 className="text-sm font-medium text-white/80 mb-2 flex items-center gap-1">
                                <Database className="h-4 w-4" />
                                Appels de modèles récents
                            </h4>
                            <div className="space-y-1">
                                {telemetryData.model_calls.slice(-5).reverse().map((call, index) => (
                                    <div key={call.id || index} className="glass-dark rounded-lg p-2 text-xs">
                                        <div className="flex items-center justify-between mb-1">
                                            <div className="flex items-center gap-1">
                                                <Activity className="h-3 w-3" />
                                                <span className="font-medium">{call.operation}</span>
                                            </div>
                                            <div className={`flex items-center gap-1 ${getStatusColor(call.status)}`}>
                                                <Clock className="h-3 w-3" />
                                                <span>{formatDuration(call.latency)}</span>
                                            </div>
                                        </div>
                                        <div className="text-white/60">
                                            {call.model_name} • {call.tokens_used ? `${call.tokens_used} tokens` : 'N/A'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {telemetryData.tool_calls.length === 0 && telemetryData.model_calls.length === 0 && (
                        <div className="text-center py-4 text-white/60">
                            Aucune activité récente
                        </div>
                    )}
                </div>
            ) : (
                <div className="text-center py-4 text-white/60">
                    Télémétrie non disponible
                </div>
            )}
        </div>
    );
}
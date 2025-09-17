import { useState, useEffect } from 'react';
import { Activity, Database, Search, Phone, Building, AlertCircle, Wrench, RefreshCw } from 'lucide-react';
import ToolCallDetail from './tool-call-detail';

interface ToolCall {
    id: string;
    tool_name: string;
    args: Record<string, any>;
    timestamp: number;
    duration?: number;
    status: string;
    response_preview?: string;
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
        default: return <Wrench className="h-4 w-4" />;
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

export function TelemetryPanel({ isVisible, onToggle }: { isVisible: boolean, onToggle: () => void }) {
    const [telemetryData, setTelemetryData] = useState<TelemetryData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [activeTab, setActiveTab] = useState<'overview' | 'tools'>('overview');

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
            // Remove automatic refresh - only refresh manually via button
        }
    }, [isVisible]);

    if (!isVisible) {
        return null;
    }

    return (
        <div className="fixed top-6 right-6 w-96 max-h-[80vh] glass-card rounded-3xl text-white z-50 overflow-hidden flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between p-4 border-b border-white/10">
                <div className="flex items-center gap-2">
                    <Activity className="h-5 w-5 text-blue-400" />
                    <h3 className="font-semibold">Télémétrie AI Foundry</h3>
                </div>
                <div className="flex items-center gap-2">
                    <button
                        onClick={fetchTelemetryData}
                        disabled={isLoading}
                        className="p-1.5 hover:bg-white/10 rounded-full transition-colors disabled:opacity-50"
                        title="Rafraîchir les données"
                    >
                        <RefreshCw className={`h-4 w-4 text-white/60 hover:text-white ${isLoading ? 'animate-spin' : ''}`} />
                    </button>
                    <button
                        onClick={onToggle}
                        className="text-white/60 hover:text-white transition-colors"
                    >
                        ×
                    </button>
                </div>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-white/10">
                <button
                    onClick={() => setActiveTab('overview')}
                    className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                        activeTab === 'overview'
                            ? 'text-blue-400 border-b-2 border-blue-400'
                            : 'text-white/60 hover:text-white'
                    }`}
                >
                    Vue d'ensemble
                </button>
                <button
                    onClick={() => setActiveTab('tools')}
                    className={`flex-1 px-4 py-2 text-sm font-medium transition-colors ${
                        activeTab === 'tools'
                            ? 'text-blue-400 border-b-2 border-blue-400'
                            : 'text-white/60 hover:text-white'
                    }`}
                >
                    <Wrench className="h-4 w-4 inline mr-1" />
                    Outils
                </button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-4">
                {isLoading ? (
                    <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-white"></div>
                    </div>
                ) : telemetryData ? (
                    <div className="space-y-4">
                        {/* Overview Tab */}
                        {activeTab === 'overview' && (
                            <>
                                {/* Stats */}
                                <div className="grid grid-cols-2 gap-3 text-sm">
                                    <div className="glass-dark rounded-lg p-3">
                                        <div className="text-white/60 text-xs">Appels d'outils</div>
                                        <div className="font-semibold text-lg">{telemetryData.stats.total_tool_calls}</div>
                                        <div className="text-white/40 text-xs">
                                            {telemetryData.tool_calls.length > 0 ? 'Actifs' : 'Aucun'}
                                        </div>
                                    </div>
                                    <div className="glass-dark rounded-lg p-3">
                                        <div className="text-white/60 text-xs">Recherches</div>
                                        <div className="font-semibold text-lg">
                                            {telemetryData.tool_calls.filter(call => call.tool_name === 'search').length}
                                        </div>
                                        <div className="text-white/40 text-xs">
                                            Base de connaissances
                                        </div>
                                    </div>
                                </div>

                                {/* Recent Activity Summary */}
                                <div className="space-y-2">
                                    <h4 className="text-sm font-medium text-white/80">Outils utilisés récemment</h4>
                                    {telemetryData.tool_calls.length > 0 ? (
                                        telemetryData.tool_calls.slice(-3).reverse().map((call, index) => (
                                            <div key={call.id || index} className="glass-dark rounded-lg p-2 text-xs">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center gap-2">
                                                        {getToolIcon(call.tool_name)}
                                                        <span className="font-medium">{call.tool_name}</span>
                                                    </div>
                                                    <div className={`${getStatusColor(call.status)}`}>
                                                        {formatDuration(call.duration)}
                                                    </div>
                                                </div>
                                                {call.args && Object.keys(call.args).length > 0 && (
                                                    <div className="text-white/50 text-[10px] mt-1 truncate">
                                                        {call.tool_name === 'search' && call.args.query ? 
                                                            `Recherche: "${call.args.query}"` :
                                                            JSON.stringify(call.args).substring(0, 40) + '...'
                                                        }
                                                    </div>
                                                )}
                                            </div>
                                        ))
                                    ) : (
                                        <div className="text-center py-4 text-white/60">
                                            <Wrench className="h-8 w-8 mx-auto mb-2 opacity-50" />
                                            <p className="text-xs">Aucun outil utilisé</p>
                                            <p className="text-[10px] mt-1 text-white/40">
                                                Les appels d'outils apparaîtront ici
                                            </p>
                                        </div>
                                    )}
                                </div>
                            </>
                        )}

                        {/* Tools Tab */}
                        {activeTab === 'tools' && (
                            <div className="space-y-3">
                                <h4 className="text-sm font-medium text-white/80">Traces des appels d'outils</h4>
                                {telemetryData.tool_calls.length > 0 ? (
                                    telemetryData.tool_calls.slice().reverse().map((call, index) => (
                                        <ToolCallDetail key={call.id || index} call={call} />
                                    ))
                                ) : (
                                    <div className="text-center py-4 text-white/60">
                                        Aucun appel d'outil
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="text-center py-4 text-white/60">
                        Télémétrie non disponible
                    </div>
                )}
            </div>
        </div>
    );
}
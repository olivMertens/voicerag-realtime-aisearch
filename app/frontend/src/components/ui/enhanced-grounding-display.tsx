import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Clock, FileText, Target, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

interface EnhancedGroundingSource {
    chunk_id: string;
    title: string;
    chunk: string;
    category: string;
    excerpt: string;
    word_count: number;
    relevance: 'high' | 'medium' | 'low';
}

interface GroundingInfo {
    total_sources: number;
    requested_sources: number;
    found_sources: number;
    missing_sources: string[];
    confidence_level: 'high' | 'medium' | 'low';
    summary: string;
    status: 'success' | 'not_found' | 'error' | 'no_sources';
    categories: string[];
    total_words: number;
    timestamp: number;
    error_details?: string;
}

interface EnhancedGroundingDisplayProps {
    sources: EnhancedGroundingSource[];
    grounding_info: GroundingInfo;
    isVisible: boolean;
    onToggle: () => void;
}

const getConfidenceColor = (level: string) => {
    switch (level) {
        case 'high': return 'text-green-600 bg-green-100';
        case 'medium': return 'text-yellow-600 bg-yellow-100';
        case 'low': return 'text-red-600 bg-red-100';
        default: return 'text-gray-600 bg-gray-100';
    }
};

const getRelevanceIcon = (relevance: string) => {
    switch (relevance) {
        case 'high': return <Target className="h-4 w-4 text-green-600" />;
        case 'medium': return <FileText className="h-4 w-4 text-yellow-600" />;
        case 'low': return <Clock className="h-4 w-4 text-gray-600" />;
        default: return <FileText className="h-4 w-4" />;
    }
};

const getStatusIcon = (status: string) => {
    switch (status) {
        case 'success': return <CheckCircle className="h-5 w-5 text-green-600" />;
        case 'error': return <XCircle className="h-5 w-5 text-red-600" />;
        case 'not_found': return <AlertCircle className="h-5 w-5 text-yellow-600" />;
        default: return <FileText className="h-5 w-5 text-gray-600" />;
    }
};

export function EnhancedGroundingDisplay({ 
    sources, 
    grounding_info, 
    isVisible, 
    onToggle 
}: EnhancedGroundingDisplayProps) {
    if (!isVisible) return null;

    const formatTimestamp = (timestamp: number) => {
        return new Date(timestamp * 1000).toLocaleTimeString();
    };

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="fixed bottom-6 right-6 w-96 max-h-[80vh] bg-white rounded-xl shadow-2xl border border-gray-200 overflow-hidden z-50"
            >
                {/* Header */}
                <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-4">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            {getStatusIcon(grounding_info.status)}
                            <h3 className="font-semibold">Sources référencées</h3>
                        </div>
                        <div className="flex items-center gap-2">
                            <Badge className={`${getConfidenceColor(grounding_info.confidence_level)} text-xs`}>
                                {grounding_info.confidence_level} confiance
                            </Badge>
                            <button
                                onClick={onToggle}
                                className="text-white hover:text-gray-200 transition-colors"
                            >
                                ×
                            </button>
                        </div>
                    </div>
                    
                    {/* Summary */}
                    {grounding_info.summary && (
                        <p className="text-sm text-blue-100 mt-2 leading-relaxed">
                            {grounding_info.summary}
                        </p>
                    )}
                </div>

                {/* Stats Overview */}
                <div className="bg-gray-50 p-3 border-b">
                    <div className="grid grid-cols-3 gap-4 text-center">
                        <div>
                            <div className="text-lg font-bold text-blue-600">
                                {grounding_info.found_sources}
                            </div>
                            <div className="text-xs text-gray-600">Sources trouvées</div>
                        </div>
                        <div>
                            <div className="text-lg font-bold text-purple-600">
                                {grounding_info.categories.length}
                            </div>
                            <div className="text-xs text-gray-600">Catégories</div>
                        </div>
                        <div>
                            <div className="text-lg font-bold text-green-600">
                                {grounding_info.total_words}
                            </div>
                            <div className="text-xs text-gray-600">Mots total</div>
                        </div>
                    </div>
                </div>

                {/* Sources List */}
                <div className="flex-1 overflow-y-auto max-h-96">
                    {sources.length > 0 ? (
                        <div className="p-4 space-y-3">
                            {sources.map((source, index) => (
                                <motion.div
                                    key={source.chunk_id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.1 }}
                                    className="bg-white border border-gray-200 rounded-lg p-3 hover:shadow-md transition-shadow"
                                >
                                    {/* Source Header */}
                                    <div className="flex items-center justify-between mb-2">
                                        <div className="flex items-center gap-2">
                                            {getRelevanceIcon(source.relevance)}
                                            <h4 className="font-medium text-sm text-gray-800 truncate">
                                                {source.title || 'Document sans titre'}
                                            </h4>
                                        </div>
                                        <div className="flex gap-1">
                                            <Badge variant="outline" className="text-xs">
                                                {source.category}
                                            </Badge>
                                            <Badge 
                                                variant={source.relevance === 'high' ? 'default' : 'secondary'}
                                                className="text-xs"
                                            >
                                                {source.relevance}
                                            </Badge>
                                        </div>
                                    </div>

                                    {/* Source Content */}
                                    <p className="text-xs text-gray-700 leading-relaxed mb-2">
                                        {source.excerpt}
                                    </p>

                                    {/* Source Metadata */}
                                    <div className="flex items-center justify-between text-xs text-gray-500">
                                        <span>{source.word_count} mots</span>
                                        <span className="font-mono">
                                            ID: {source.chunk_id.substring(0, 8)}...
                                        </span>
                                    </div>
                                </motion.div>
                            ))}
                        </div>
                    ) : (
                        <div className="p-8 text-center text-gray-500">
                            <FileText className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                            <p className="text-sm">Aucune source trouvée</p>
                            {grounding_info.error_details && (
                                <p className="text-xs text-red-600 mt-2">
                                    {grounding_info.error_details}
                                </p>
                            )}
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="bg-gray-50 px-4 py-2 text-xs text-gray-500 text-center border-t">
                    Mis à jour à {formatTimestamp(grounding_info.timestamp)}
                    {grounding_info.missing_sources.length > 0 && (
                        <div className="text-yellow-600 mt-1">
                            ⚠️ {grounding_info.missing_sources.length} source(s) non trouvée(s)
                        </div>
                    )}
                </div>
            </motion.div>
        </AnimatePresence>
    );
}

// Badge component (if not already available)
const Badge: React.FC<{ 
    children: React.ReactNode; 
    variant?: 'default' | 'secondary' | 'outline';
    className?: string;
}> = ({ children, variant = 'default', className = '' }) => {
    const baseClasses = 'inline-flex items-center rounded-full px-2 py-1 text-xs font-medium';
    const variantClasses = {
        default: 'bg-blue-100 text-blue-800',
        secondary: 'bg-gray-100 text-gray-800',
        outline: 'border border-gray-300 text-gray-700'
    };
    
    return (
        <span className={`${baseClasses} ${variantClasses[variant]} ${className}`}>
            {children}
        </span>
    );
};
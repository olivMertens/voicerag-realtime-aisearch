import { motion, AnimatePresence } from 'framer-motion';
import { Phone, Clock, User, MessageCircle, X, Calendar, AlertTriangle } from 'lucide-react';

interface CallHistoryItem {
    date: string;
    type: string;
    reason: string;
    outcome: string;
    agent?: string;
    duration?: string;
    notes?: string;
}

interface CustomerInfo {
    name: string;
    first_name?: string;
    last_name?: string;
    policy_number?: string;
    customer_id?: string;
}

interface CallHistoryPopupProps {
    isVisible: boolean;
    onClose: () => void;
    customer: CustomerInfo;
    callHistory: CallHistoryItem[];
    title?: string;
}

const getCallTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
        case 'réclamation':
        case 'claim':
            return <AlertTriangle className="h-4 w-4 text-red-500" />;
        case 'information':
        case 'info':
            return <MessageCircle className="h-4 w-4 text-blue-500" />;
        case 'urgence':
        case 'emergency':
            return <Phone className="h-4 w-4 text-orange-500" />;
        default:
            return <Phone className="h-4 w-4 text-gray-500" />;
    }
};

const getCallTypeColor = (type: string) => {
    switch (type.toLowerCase()) {
        case 'réclamation':
        case 'claim':
            return 'bg-red-50 border-red-200';
        case 'information':
        case 'info':
            return 'bg-blue-50 border-blue-200';
        case 'urgence':
        case 'emergency':
            return 'bg-orange-50 border-orange-200';
        default:
            return 'bg-gray-50 border-gray-200';
    }
};

export function CallHistoryPopup({ 
    isVisible, 
    onClose, 
    customer, 
    callHistory, 
    title = "Historique des appels" 
}: CallHistoryPopupProps) {
    if (!isVisible) return null;

    const formatDate = (dateString: string) => {
        try {
            const date = new Date(dateString);
            return {
                date: date.toLocaleDateString('fr-FR'),
                time: date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
            };
        } catch {
            return { date: dateString, time: '' };
        }
    };

    const getSummary = () => {
        const totalCalls = callHistory.length;
        const claimCalls = callHistory.filter(call => 
            call.type.toLowerCase().includes('réclamation') || 
            call.type.toLowerCase().includes('claim')
        ).length;
        const recentCall = callHistory.length > 0 ? callHistory[0] : null;
        
        return { totalCalls, claimCalls, recentCall };
    };

    const { totalCalls, claimCalls, recentCall } = getSummary();

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
                onClick={onClose}
            >
                <motion.div
                    initial={{ opacity: 0, scale: 0.9, y: 20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9, y: 20 }}
                    transition={{ type: "spring", damping: 25, stiffness: 300 }}
                    className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden"
                    onClick={(e) => e.stopPropagation()}
                >
                    {/* Header */}
                    <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white p-6">
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <User className="h-6 w-6" />
                                <div>
                                    <h2 className="text-xl font-bold">{title}</h2>
                                    <p className="text-blue-100 text-sm">
                                        {customer.first_name && customer.last_name 
                                            ? `${customer.first_name} ${customer.last_name}`
                                            : customer.name
                                        }
                                        {customer.policy_number && (
                                            <span className="ml-2 opacity-75">• Police: {customer.policy_number}</span>
                                        )}
                                    </p>
                                </div>
                            </div>
                            <button
                                onClick={onClose}
                                className="text-white hover:text-gray-200 transition-colors p-1"
                            >
                                <X className="h-6 w-6" />
                            </button>
                        </div>
                    </div>

                    {/* Summary Stats */}
                    <div className="bg-gray-50 p-4 border-b">
                        <div className="grid grid-cols-3 gap-4 text-center">
                            <div>
                                <div className="text-2xl font-bold text-blue-600">{totalCalls}</div>
                                <div className="text-sm text-gray-600">Appels total</div>
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-red-600">{claimCalls}</div>
                                <div className="text-sm text-gray-600">Réclamations</div>
                            </div>
                            <div>
                                <div className="text-2xl font-bold text-green-600">
                                    {recentCall ? formatDate(recentCall.date).date : 'N/A'}
                                </div>
                                <div className="text-sm text-gray-600">Dernier contact</div>
                            </div>
                        </div>
                    </div>

                    {/* Call History List */}
                    <div className="flex-1 overflow-y-auto max-h-96">
                        {callHistory.length > 0 ? (
                            <div className="p-4 space-y-3">
                                {callHistory.map((call, index) => {
                                    const { date, time } = formatDate(call.date);
                                    return (
                                        <motion.div
                                            key={index}
                                            initial={{ opacity: 0, x: -20 }}
                                            animate={{ opacity: 1, x: 0 }}
                                            transition={{ delay: index * 0.1 }}
                                            className={`border rounded-lg p-4 ${getCallTypeColor(call.type)} hover:shadow-md transition-shadow`}
                                        >
                                            {/* Call Header */}
                                            <div className="flex items-center justify-between mb-3">
                                                <div className="flex items-center gap-2">
                                                    {getCallTypeIcon(call.type)}
                                                    <span className="font-medium text-gray-800">
                                                        {call.type}
                                                    </span>
                                                    {call.duration && (
                                                        <span className="text-sm text-gray-500 flex items-center gap-1">
                                                            <Clock className="h-3 w-3" />
                                                            {call.duration}
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="text-right text-sm text-gray-600">
                                                    <div className="flex items-center gap-1">
                                                        <Calendar className="h-3 w-3" />
                                                        {date}
                                                    </div>
                                                    {time && <div className="text-xs">{time}</div>}
                                                </div>
                                            </div>

                                            {/* Call Details */}
                                            <div className="space-y-2">
                                                <div>
                                                    <span className="text-sm font-medium text-gray-700">Motif: </span>
                                                    <span className="text-sm text-gray-800">{call.reason}</span>
                                                </div>
                                                
                                                <div>
                                                    <span className="text-sm font-medium text-gray-700">Résultat: </span>
                                                    <span className="text-sm text-gray-800">{call.outcome}</span>
                                                </div>

                                                {call.agent && (
                                                    <div>
                                                        <span className="text-sm font-medium text-gray-700">Agent: </span>
                                                        <span className="text-sm text-gray-800">{call.agent}</span>
                                                    </div>
                                                )}

                                                {call.notes && (
                                                    <div className="mt-2 p-2 bg-white bg-opacity-50 rounded border">
                                                        <span className="text-sm font-medium text-gray-700">Notes: </span>
                                                        <p className="text-sm text-gray-800 leading-relaxed">{call.notes}</p>
                                                    </div>
                                                )}
                                            </div>
                                        </motion.div>
                                    );
                                })}
                            </div>
                        ) : (
                            <div className="p-8 text-center text-gray-500">
                                <Phone className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                                <p className="text-sm">Aucun historique d'appel trouvé</p>
                                <p className="text-xs text-gray-400 mt-1">
                                    Premier contact avec ce client
                                </p>
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="bg-gray-50 px-6 py-3 border-t">
                        <div className="flex justify-between items-center text-sm text-gray-600">
                            <span>
                                💡 Cet historique aide à personnaliser votre service
                            </span>
                            <button
                                onClick={onClose}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors text-sm"
                            >
                                Fermer
                            </button>
                        </div>
                    </div>
                </motion.div>
            </motion.div>
        </AnimatePresence>
    );
}
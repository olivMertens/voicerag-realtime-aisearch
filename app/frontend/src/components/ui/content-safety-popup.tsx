import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, X, ExternalLink } from "lucide-react";
import { Button } from "./button";

interface ContentSafetyPopupProps {
    isVisible: boolean;
    onClose: () => void;
    errorDetails?: {
        message?: string;
        reason?: string;
        action?: string;
        documentation?: string;
    };
}

export const ContentSafetyPopup: React.FC<ContentSafetyPopupProps> = ({ isVisible, onClose, errorDetails }) => {
    return (
        <AnimatePresence>
            {isVisible && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm"
                        onClick={onClose}
                    />

                    {/* Popup */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9, y: 20 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.9, y: 20 }}
                        className="fixed inset-0 z-50 flex items-center justify-center p-4"
                        onClick={e => e.stopPropagation()}
                    >
                        <div className="glass-card mx-4 w-full max-w-md rounded-2xl border border-orange-400/30 p-6">
                            {/* Header */}
                            <div className="mb-4 flex items-center justify-between">
                                <div className="flex items-center gap-3">
                                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-500/20">
                                        <AlertTriangle className="h-6 w-6 text-orange-400" />
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-semibold text-white">Contenu non autorisé</h3>
                                        <p className="text-sm text-white/70">Politique de sécurité</p>
                                    </div>
                                </div>
                                <Button onClick={onClose} className="glass-button rounded-full p-2 hover:bg-white/20">
                                    <X className="h-5 w-5 text-white" />
                                </Button>
                            </div>

                            {/* Content */}
                            <div className="mb-6 space-y-4">
                                <div className="rounded-xl border border-orange-400/20 bg-orange-500/10 p-4">
                                    <p className="text-sm leading-relaxed text-white">
                                        {errorDetails?.message ||
                                            "Votre demande a été filtrée par la politique de sécurité du contenu d'Azure OpenAI. Veuillez modifier votre question et réessayer."}
                                    </p>
                                </div>

                                {errorDetails?.reason && (
                                    <div>
                                        <h4 className="mb-2 font-medium text-white">Raison :</h4>
                                        <p className="text-sm text-white/80">{errorDetails.reason}</p>
                                    </div>
                                )}

                                {errorDetails?.action && (
                                    <div>
                                        <h4 className="mb-2 font-medium text-white">Action recommandée :</h4>
                                        <p className="text-sm text-white/80">{errorDetails.action}</p>
                                    </div>
                                )}
                            </div>

                            {/* Actions */}
                            <div className="flex flex-col gap-2">
                                <Button onClick={onClose} className="glass-button w-full rounded-xl py-3 text-white hover:bg-blue-500/20">
                                    Compris, reformuler ma question
                                </Button>

                                {errorDetails?.documentation && (
                                    <Button
                                        onClick={() => window.open(errorDetails.documentation, "_blank")}
                                        className="glass-button flex w-full items-center justify-center gap-2 rounded-xl py-2 text-white/70 hover:bg-white/10"
                                    >
                                        <ExternalLink className="h-4 w-4" />
                                        En savoir plus sur les politiques
                                    </Button>
                                )}
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
};

export default ContentSafetyPopup;

import { useEffect, useMemo, useState } from "react";
import { Check, Copy, X } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./dialog";
import { Button } from "./button";

type HelpDialogProps = {
    open: boolean;
    onOpenChange: (open: boolean) => void;
};

const copyToClipboard = async (text: string) => {
    if (navigator.clipboard?.writeText) {
        await navigator.clipboard.writeText(text);
        return;
    }

    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.left = "-9999px";
    document.body.appendChild(textarea);
    textarea.focus();
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
};

export function HelpDialog({ open, onOpenChange }: HelpDialogProps) {
    const { t } = useTranslation();
    const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

    const examples = useMemo(() => {
        const raw = t("help.examples", { returnObjects: true }) as unknown;
        return Array.isArray(raw) ? (raw as string[]) : [];
    }, [t]);

    useEffect(() => {
        if (copiedIndex == null) return;
        const timer = window.setTimeout(() => setCopiedIndex(null), 1200);
        return () => window.clearTimeout(timer);
    }, [copiedIndex]);

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="glass-card w-[min(820px,94vw)] max-w-none border border-white/20 bg-slate-950/70 p-0 text-white">
                <div className="flex max-h-[85vh] flex-col">
                    <div className="sticky top-0 z-10 border-b border-white/10 bg-slate-950/60 px-6 py-4 backdrop-blur">
                        <div className="flex items-start justify-between gap-4">
                            <DialogHeader className="text-left">
                                <DialogTitle className="text-xl text-white">{t("help.title")}</DialogTitle>
                                <p className="text-sm text-white/70">{t("help.subtitle")}</p>
                            </DialogHeader>
                            <Button
                                onClick={() => onOpenChange(false)}
                                className="glass-button rounded-full p-2 text-white hover:bg-white/10"
                                aria-label={t("help.close")}
                                title={t("help.close")}
                            >
                                <X className="h-5 w-5" />
                            </Button>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto px-6 py-4">
                        <div className="space-y-6">
                            <section className="space-y-2">
                                <h3 className="text-sm font-semibold tracking-wide text-white/90">{t("help.examplesTitle")}</h3>
                                <div className="space-y-2">
                                    {examples.map((example, index) => (
                                        <div
                                            key={index}
                                            className="flex items-start justify-between gap-3 rounded-xl border border-white/10 bg-white/5 p-3"
                                        >
                                            <p className="whitespace-pre-line text-sm text-white/90">{example}</p>
                                            <Button
                                                onClick={async () => {
                                                    await copyToClipboard(example);
                                                    setCopiedIndex(index);
                                                }}
                                                className="glass-button shrink-0 rounded-xl px-3 py-2 text-white hover:bg-white/10"
                                            >
                                                {copiedIndex === index ? (
                                                    <>
                                                        <Check className="mr-2 h-4 w-4" />
                                                        {t("help.copied")}
                                                    </>
                                                ) : (
                                                    <>
                                                        <Copy className="mr-2 h-4 w-4" />
                                                        {t("help.copy")}
                                                    </>
                                                )}
                                            </Button>
                                        </div>
                                    ))}

                                    {examples.length === 0 && <p className="text-sm text-white/70">{t("help.noExamples")}</p>}
                                </div>
                            </section>

                            <section className="space-y-2">
                                <h3 className="text-sm font-semibold tracking-wide text-white/90">{t("help.techTitle")}</h3>
                                <p className="whitespace-pre-line text-sm text-white/80">{t("help.techBody")}</p>
                            </section>
                        </div>
                    </div>

                    <div className="sticky bottom-0 z-10 border-t border-white/10 bg-slate-950/60 px-6 py-4 backdrop-blur">
                        <div className="flex justify-end">
                            <Button
                                onClick={() => onOpenChange(false)}
                                className="rounded-xl bg-blue-600/80 px-4 py-2 text-white hover:bg-blue-700/80"
                            >
                                {t("help.close")}
                            </Button>
                        </div>
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    );
}

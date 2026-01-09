import { useEffect, useMemo, useState } from "react";
import { Check, Copy, LayoutDashboard, ListChecks, Plug, Sparkles, HelpCircle, X } from "lucide-react";
import { useTranslation } from "react-i18next";

import { Dialog, DialogContent, DialogHeader, DialogTitle } from "./dialog";
import { Button } from "./button";

type HelpDialogProps = {
    open: boolean;
    onOpenChange: (open: boolean) => void;
};

type HelpSectionId = "overview" | "questions" | "apis" | "features";

type HelpQuestionGroup = {
    title: string;
    items: string[];
};

type HelpApiItem = {
    name: string;
    description: string;
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
    const [activeSection, setActiveSection] = useState<HelpSectionId>("questions");
    const [copiedKey, setCopiedKey] = useState<string | null>(null);

    const questionGroups = useMemo(() => {
        const rawGroups = t("help.questions.groups", { returnObjects: true }) as unknown;
        if (Array.isArray(rawGroups)) {
            const groups = rawGroups as HelpQuestionGroup[];
            return groups
                .filter(g => typeof g?.title === "string" && Array.isArray(g?.items))
                .map(g => ({
                    title: g.title,
                    items: (g.items ?? []).filter((item): item is string => typeof item === "string")
                }));
        }

        const rawExamples = t("help.examples", { returnObjects: true }) as unknown;
        const examples = Array.isArray(rawExamples) ? (rawExamples as string[]) : [];
        return examples.length ? [{ title: t("help.examplesTitle"), items: examples }] : [];
    }, [t]);

    const apiItems = useMemo(() => {
        const raw = t("help.apis.items", { returnObjects: true }) as unknown;
        if (!Array.isArray(raw)) return [];
        return (raw as HelpApiItem[])
            .filter(item => typeof item?.name === "string" && typeof item?.description === "string")
            .map(item => ({ name: item.name, description: item.description }));
    }, [t]);

    const featureItems = useMemo(() => {
        const raw = t("help.features.items", { returnObjects: true }) as unknown;
        return Array.isArray(raw) ? (raw as string[]).filter((item): item is string => typeof item === "string") : [];
    }, [t]);

    const overviewBullets = useMemo(() => {
        const raw = t("help.overview.bullets", { returnObjects: true }) as unknown;
        return Array.isArray(raw) ? (raw as string[]).filter((item): item is string => typeof item === "string") : [];
    }, [t]);

    useEffect(() => {
        if (copiedKey == null) return;
        const timer = window.setTimeout(() => setCopiedKey(null), 1200);
        return () => window.clearTimeout(timer);
    }, [copiedKey]);

    const navItems = useMemo(
        () => [
            { id: "overview" as const, icon: LayoutDashboard, label: t("help.nav.overview") },
            { id: "questions" as const, icon: ListChecks, label: t("help.nav.questionTypes") },
            { id: "apis" as const, icon: Plug, label: t("help.nav.apis") },
            { id: "features" as const, icon: Sparkles, label: t("help.nav.features") }
        ],
        [t]
    );

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="glass-card w-[min(980px,94vw)] max-w-none p-0 text-white">
                <div className="flex max-h-[85vh] flex-col">
                    <div className="glass-dark sticky top-0 z-10 border-b border-white/10 px-6 py-4 backdrop-blur">
                        <div className="flex items-start justify-between gap-4">
                            <DialogHeader className="text-left">
                                <DialogTitle className="flex items-center gap-2 text-xl text-white">
                                    <HelpCircle className="h-5 w-5 text-white/80" />
                                    {t("help.title")}
                                </DialogTitle>
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

                    <div className="flex-1 overflow-hidden">
                        <div className="flex h-full">
                            <aside className="w-64 shrink-0 border-r border-white/10 bg-white/5 p-3">
                                <nav className="space-y-1">
                                    {navItems.map(item => {
                                        const Icon = item.icon;
                                        const isActive = activeSection === item.id;
                                        return (
                                            <button
                                                key={item.id}
                                                type="button"
                                                onClick={() => setActiveSection(item.id)}
                                                className={
                                                    "flex w-full items-center gap-3 rounded-xl px-3 py-2 text-left text-sm transition-colors " +
                                                    (isActive
                                                        ? "bg-white/10 text-white"
                                                        : "text-white/80 hover:bg-white/5 hover:text-white")
                                                }
                                            >
                                                <Icon className={"h-4 w-4 " + (isActive ? "text-white" : "text-white/60")} />
                                                <span className="truncate">{item.label}</span>
                                            </button>
                                        );
                                    })}
                                </nav>
                            </aside>

                            <main className="flex-1 overflow-y-auto px-6 py-5">
                                {activeSection === "overview" && (
                                    <div className="space-y-5">
                                        <div className="space-y-1">
                                            <h2 className="text-lg font-semibold text-white">{t("help.overview.title")}</h2>
                                            <p className="text-sm text-white/70">{t("help.overview.subtitle")}</p>
                                        </div>

                                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                                            <h3 className="mb-2 text-sm font-semibold text-white/90">{t("help.overview.howToTitle")}</h3>
                                            <ul className="space-y-1 text-sm text-white/80">
                                                {overviewBullets.map((line, idx) => (
                                                    <li key={idx} className="flex gap-2">
                                                        <span className="mt-[6px] h-1.5 w-1.5 shrink-0 rounded-full bg-white/40" />
                                                        <span className="leading-relaxed">{line}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>

                                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                                            <h3 className="mb-2 text-sm font-semibold text-white/90">{t("help.techTitle")}</h3>
                                            <p className="whitespace-pre-line text-sm text-white/80">{t("help.techBody")}</p>
                                        </div>
                                    </div>
                                )}

                                {activeSection === "questions" && (
                                    <div className="space-y-5">
                                        <div className="space-y-1">
                                            <h2 className="text-lg font-semibold text-white">{t("help.questions.title")}</h2>
                                            <p className="text-sm text-white/70">{t("help.questions.subtitle")}</p>
                                        </div>

                                        {questionGroups.length > 0 ? (
                                            <div className="space-y-4">
                                                {questionGroups.map((group, groupIndex) => (
                                                    <section key={groupIndex} className="rounded-2xl border border-white/10 bg-white/5">
                                                        <div className="border-b border-white/10 px-4 py-3">
                                                            <h3 className="text-sm font-semibold text-white/90">{group.title}</h3>
                                                        </div>
                                                        <div className="space-y-2 p-3">
                                                            {group.items.map((question, questionIndex) => {
                                                                const key = `${groupIndex}-${questionIndex}`;
                                                                const copied = copiedKey === key;
                                                                return (
                                                                    <div
                                                                        key={key}
                                                                        className="glass-dark flex items-center justify-between gap-3 rounded-xl px-3 py-2"
                                                                    >
                                                                        <p className="text-sm leading-relaxed text-white/90">{question}</p>
                                                                        <Button
                                                                            type="button"
                                                                            variant="ghost"
                                                                            size="icon"
                                                                            onClick={async () => {
                                                                                await copyToClipboard(question);
                                                                                setCopiedKey(key);
                                                                            }}
                                                                            className="h-9 w-9 shrink-0 rounded-xl text-white/90 hover:bg-white/10 hover:text-white"
                                                                            aria-label={copied ? t("help.copied") : t("help.copy")}
                                                                            title={copied ? t("help.copied") : t("help.copy")}
                                                                        >
                                                                            {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
                                                                        </Button>
                                                                    </div>
                                                                );
                                                            })}
                                                        </div>
                                                    </section>
                                                ))}
                                            </div>
                                        ) : (
                                            <p className="text-sm text-white/70">{t("help.noExamples")}</p>
                                        )}
                                    </div>
                                )}

                                {activeSection === "apis" && (
                                    <div className="space-y-5">
                                        <div className="space-y-1">
                                            <h2 className="text-lg font-semibold text-white">{t("help.apis.title")}</h2>
                                            <p className="text-sm text-white/70">{t("help.apis.subtitle")}</p>
                                        </div>

                                        <div className="space-y-3">
                                            {apiItems.map((api, idx) => (
                                                <div key={idx} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                                                    <p className="font-mono text-sm text-white">{api.name}</p>
                                                    <p className="mt-1 text-sm text-white/75">{api.description}</p>
                                                </div>
                                            ))}

                                            {apiItems.length === 0 && <p className="text-sm text-white/70">{t("help.apis.none")}</p>}
                                        </div>
                                    </div>
                                )}

                                {activeSection === "features" && (
                                    <div className="space-y-5">
                                        <div className="space-y-1">
                                            <h2 className="text-lg font-semibold text-white">{t("help.features.title")}</h2>
                                            <p className="text-sm text-white/70">{t("help.features.subtitle")}</p>
                                        </div>

                                        <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
                                            <ul className="space-y-2 text-sm text-white/85">
                                                {featureItems.map((line, idx) => (
                                                    <li key={idx} className="flex gap-2">
                                                        <span className="mt-[6px] h-1.5 w-1.5 shrink-0 rounded-full bg-white/40" />
                                                        <span className="leading-relaxed">{line}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                    </div>
                                )}
                            </main>
                        </div>
                    </div>

                    <div className="glass-dark sticky bottom-0 z-10 border-t border-white/10 px-6 py-4 backdrop-blur">
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

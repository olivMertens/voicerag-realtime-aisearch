import { AnimatePresence, motion, Variants } from "framer-motion";

import { GroundingFile as GroundingFileType } from "@/types";

import GroundingFile from "./grounding-file";
import { useRef } from "react";
import { useTranslation } from "react-i18next";

type Properties = {
    files: GroundingFileType[];
    onSelected: (file: GroundingFileType) => void;
};

const variants: Variants = {
    hidden: { opacity: 0, scale: 0.8, y: 20 },
    visible: (i: number) => ({
        opacity: 1,
        scale: 1,
        y: 0,
        transition: {
            delay: i * 0.1,
            duration: 0.3,
            type: "spring",
            stiffness: 300,
            damping: 20
        }
    })
};

export function GroundingFiles({ files, onSelected }: Properties) {
    const { t } = useTranslation();
    const isAnimating = useRef(false);

    if (files.length === 0) {
        return null;
    }

    return (
        <div className="glass-card rounded-3xl p-6 m-4 max-w-full md:max-w-2xl lg:min-w-96 lg:max-w-4xl">
            <div className="mb-4">
                <h3 className="text-xl font-semibold text-white text-glow mb-2">{t("groundingFiles.title")}</h3>
                <p className="text-white/80">{t("groundingFiles.description")}</p>
            </div>
            <div>
                <AnimatePresence>
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className={`h-full ${isAnimating ? "overflow-hidden" : "overflow-y-auto"}`}
                        onLayoutAnimationStart={() => (isAnimating.current = true)}
                        onLayoutAnimationComplete={() => (isAnimating.current = false)}
                    >
                        <div className="flex flex-wrap gap-3">
                            {files.map((file, index) => (
                                <motion.div key={index} variants={variants} initial="hidden" animate="visible" custom={index}>
                                    <GroundingFile key={index} value={file} onClick={() => onSelected(file)} />
                                </motion.div>
                            ))}
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>
        </div>
    );
}

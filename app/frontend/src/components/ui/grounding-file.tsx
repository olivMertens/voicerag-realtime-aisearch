import { File } from "lucide-react";

import { GroundingFile as GroundingFileType } from "@/types";

type Properties = {
    value: GroundingFileType;
    onClick: () => void;
};

export default function GroundingFile({ value, onClick }: Properties) {
    return (
        <button 
            className="glass-button text-white/90 hover:text-white py-2 px-4 rounded-2xl transition-all duration-300 flex items-center gap-2 text-sm font-medium"
            onClick={onClick}
        >
            <File className="h-4 w-4" />
            {value.name}
        </button>
    );
}

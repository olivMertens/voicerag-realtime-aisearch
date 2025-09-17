export type EnhancedGroundingSource = {
    chunk_id: string;
    title: string;
    chunk: string;
    category: string;
    excerpt: string;
    word_count: number;
    relevance: 'high' | 'medium' | 'low';
};

export type GroundingInfo = {
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
};

export type EnhancedToolResult = {
    sources: EnhancedGroundingSource[];
    grounding_info: GroundingInfo;
};

export type GroundingFile = {
    id: string;
    name: string;
    content: string;
};

export type HistoryItem = {
    id: string;
    transcript: string;
    groundingFiles: GroundingFile[];
    enhancedGrounding?: EnhancedToolResult; // Add enhanced grounding support
};

export type SessionUpdateCommand = {
    type: "session.update";
    session: {
        turn_detection?: {
            type: "server_vad" | "none";
        };
        input_audio_transcription?: {
            model: "whisper-1";
        };
    };
};

export type InputAudioBufferAppendCommand = {
    type: "input_audio_buffer.append";
    audio: string;
};

export type InputAudioBufferClearCommand = {
    type: "input_audio_buffer.clear";
};

export type Message = {
    type: string;
};

export type ResponseAudioDelta = {
    type: "response.audio.delta";
    delta: string;
};

export type ResponseAudioTranscriptDelta = {
    type: "response.audio_transcript.delta";
    delta: string;
};

export type ResponseInputAudioTranscriptionCompleted = {
    type: "conversation.item.input_audio_transcription.completed";
    event_id: string;
    item_id: string;
    content_index: number;
    transcript: string;
};

export type ResponseDone = {
    type: "response.done";
    event_id: string;
    response: {
        id: string;
        output: { id: string; content?: { transcript: string; type: string }[] }[];
    };
};

export type ExtensionMiddleTierToolResponse = {
    type: "extension.middle_tier_tool.response";
    previous_item_id: string;
    tool_name: string;
    tool_result: string; // JSON string that needs to be parsed into ToolResult
};

export type ToolResult = {
    sources?: { chunk_id: string; title: string; chunk: string }[];
    grounding_info?: GroundingInfo; // Support enhanced grounding info
} | EnhancedToolResult; // Support both old and new formats

export type CallHistoryItem = {
    date: string;
    type: string;
    reason: string;
    outcome: string;
    agent?: string;
    duration?: string;
    notes?: string;
};

export type CustomerInfo = {
    name: string;
    first_name?: string;
    last_name?: string;
    policy_number?: string;
    customer_id?: string;
};

export type CallHistoryMetadata = {
    customer: CustomerInfo;
    call_history: CallHistoryItem[];
};

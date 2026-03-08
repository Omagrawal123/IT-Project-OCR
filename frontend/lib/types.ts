export interface FieldData {
    value: string | number | null;
    confidence: number;
    source: string;
}

export interface ExtraField {
    key: string;
    value: string | number | null;
    confidence: number;
}

export interface ExtractionResult {
    fields: Record<string, FieldData>;
    extra?: ExtraField[];
    confidence: number;
    route: string;
    complexity_score?: any;
    warnings?: string[];
    raw?: any;
}

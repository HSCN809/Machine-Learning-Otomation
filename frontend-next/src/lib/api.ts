// API client for ML Automation Backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Base fetch wrapper with error handling
 */
async function fetchAPI<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const defaultHeaders: HeadersInit = {
        'Content-Type': 'application/json',
    };

    const response = await fetch(url, {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || `API Error: ${response.status}`);
    }

    return response.json();
}

/**
 * API client methods
 */
export const api = {
    // Health check
    health: () => fetchAPI<{ status: string }>('/health'),

    // Data upload
    uploadData: async (file: File) => {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE_URL}/api/data/upload`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        return response.json();
    },

    // Data summary
    getDataSummary: () => fetchAPI<DataSummary>('/api/data/summary'),

    // EDA
    getEDAAnalysis: () => fetchAPI<EDAResult>('/api/eda/analyze'),

    // Preprocessing
    applyPreprocessing: (config: PreprocessingConfig) =>
        fetchAPI<PreprocessingResult>('/api/preprocessing/apply', {
            method: 'POST',
            body: JSON.stringify(config),
        }),

    // Model
    trainModel: (config: ModelConfig) =>
        fetchAPI<ModelResult>('/api/model/train', {
            method: 'POST',
            body: JSON.stringify(config),
        }),
};

// Type definitions
export interface DataSummary {
    rows: number;
    columns: number;
    missingValues: number;
    numericColumns: string[];
    categoricalColumns: string[];
}

export interface EDAResult {
    statistics: Record<string, unknown>;
    correlations: Record<string, unknown>;
}

export interface PreprocessingConfig {
    steps: Array<{
        type: string;
        method: string;
        columns: string[];
    }>;
}

export interface PreprocessingResult {
    success: boolean;
    appliedSteps: number;
}

export interface ModelConfig {
    targetColumn: string;
    problemType: 'classification' | 'regression';
    modelType: string;
}

export interface ModelResult {
    accuracy?: number;
    r2Score?: number;
    modelPath: string;
}

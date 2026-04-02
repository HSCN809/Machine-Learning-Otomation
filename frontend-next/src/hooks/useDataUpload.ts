'use client';

import {
    useDataUploadContext,
    SAMPLE_DATASETS as CONTEXT_SAMPLE_DATASETS
} from '@/context/DataUploadContext';
import {
    UploadedFile,
    DataSummary,
    ValidationReport,
    UploadStatus,
    SampleDataset
} from '@/types/data-upload';

// Re-export SAMPLE_DATASETS for compatibility
export const SAMPLE_DATASETS = CONTEXT_SAMPLE_DATASETS;

interface UseDataUploadReturn {
    // State
    status: UploadStatus;
    progress: number;
    error: string | null;
    uploadedFile: UploadedFile | null;
    dataSummary: DataSummary | null;
    validationReport: ValidationReport | null;
    isInitializing: boolean;
    setValidationReport: React.Dispatch<React.SetStateAction<ValidationReport | null>>;

    // Actions
    uploadFile: (file: File) => Promise<void>;
    loadSampleDataset: (datasetId: string) => Promise<void>;
    hydrateSession: () => Promise<void>;
    reset: () => Promise<void>;
}

export function useDataUpload(): UseDataUploadReturn {
    const context = useDataUploadContext();
    return context;
}


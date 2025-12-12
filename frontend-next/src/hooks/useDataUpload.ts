'use client';

import { useState, useCallback } from 'react';
import {
    UploadedFile,
    DataSummary,
    ValidationReport,
    UploadStatus,
    SampleDataset
} from '@/types/data-upload';

// Sample datasets available
export const SAMPLE_DATASETS: SampleDataset[] = [
    { id: 'tips', name: 'Tips', description: 'Restoran bahşiş verileri', emoji: '🍽️', rows: 244, columns: 7 },
    { id: 'titanic', name: 'Titanic', description: 'Titanic yolcu verileri', emoji: '🚢', rows: 891, columns: 12 },
    { id: 'iris', name: 'Iris', description: 'Çiçek türleri verileri', emoji: '🌸', rows: 150, columns: 5 },
    { id: 'diamonds', name: 'Diamonds', description: 'Elmas özellikleri', emoji: '💎', rows: 53940, columns: 10 },
    { id: 'penguins', name: 'Penguins', description: 'Penguen türleri', emoji: '🐧', rows: 344, columns: 7 },
];

interface UseDataUploadReturn {
    // State
    status: UploadStatus;
    progress: number;
    error: string | null;
    uploadedFile: UploadedFile | null;
    dataSummary: DataSummary | null;
    validationReport: ValidationReport | null;

    // Actions
    uploadFile: (file: File) => Promise<void>;
    loadSampleDataset: (datasetId: string) => Promise<void>;
    reset: () => void;
}

export function useDataUpload(): UseDataUploadReturn {
    const [status, setStatus] = useState<UploadStatus>('idle');
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
    const [dataSummary, setDataSummary] = useState<DataSummary | null>(null);
    const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);

    const reset = useCallback(() => {
        setStatus('idle');
        setProgress(0);
        setError(null);
        setUploadedFile(null);
        setDataSummary(null);
        setValidationReport(null);
    }, []);

    const uploadFile = useCallback(async (file: File) => {
        try {
            reset();
            setStatus('uploading');

            // Validate file type
            const validTypes = ['.csv', '.xlsx', '.xls'];
            const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
            if (!validTypes.includes(fileExt)) {
                throw new Error(`Desteklenmeyen dosya formatı: ${fileExt}. Desteklenen: CSV, Excel`);
            }

            // Validate file size (max 200MB)
            const maxSize = 200 * 1024 * 1024;
            if (file.size > maxSize) {
                throw new Error(`Dosya boyutu çok büyük: ${(file.size / 1024 / 1024).toFixed(2)}MB. Maksimum: 200MB`);
            }

            setUploadedFile({
                file,
                name: file.name,
                size: file.size,
                type: file.type,
            });

            // Simulate upload progress
            for (let i = 0; i <= 100; i += 10) {
                setProgress(i);
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            setStatus('validating');

            // TODO: Replace with actual API call
            // const response = await api.uploadData(file);

            // Mock validation for now
            await new Promise(resolve => setTimeout(resolve, 500));

            // Mock data summary
            setDataSummary({
                shape: { rows: 1000, columns: 10 },
                columns: [],
                missingValues: { total: 50, percentage: 0.5 },
                duplicateRows: 5,
                preview: [],
            });

            setValidationReport({
                isValid: true,
                totalIssues: 2,
                issuesBySeverity: {
                    critical: [],
                    warning: [
                        {
                            id: '1',
                            severity: 'warning',
                            type: 'missing_values',
                            column: 'age',
                            description: 'age sütununda %5 eksik değer var',
                            suggestion: 'Ortalama veya medyan ile doldurulabilir',
                        },
                    ],
                    info: [
                        {
                            id: '2',
                            severity: 'info',
                            type: 'duplicate_rows',
                            description: '5 tekrarlayan satır tespit edildi',
                            suggestion: 'Tekrarlayan satırları kaldırabilirsiniz',
                        },
                    ],
                },
            });

            setStatus('success');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Yükleme sırasında hata oluştu');
            setStatus('error');
        }
    }, [reset]);

    const loadSampleDataset = useCallback(async (datasetId: string) => {
        try {
            reset();
            setStatus('uploading');

            const dataset = SAMPLE_DATASETS.find(d => d.id === datasetId);
            if (!dataset) {
                throw new Error(`Veri seti bulunamadı: ${datasetId}`);
            }

            // Simulate loading
            for (let i = 0; i <= 100; i += 20) {
                setProgress(i);
                await new Promise(resolve => setTimeout(resolve, 100));
            }

            setStatus('validating');

            // TODO: Replace with actual API call
            // const response = await api.loadSampleDataset(datasetId);

            await new Promise(resolve => setTimeout(resolve, 300));

            setDataSummary({
                shape: { rows: dataset.rows, columns: dataset.columns },
                columns: [],
                missingValues: { total: 0, percentage: 0 },
                duplicateRows: 0,
                preview: [],
            });

            setValidationReport({
                isValid: true,
                totalIssues: 0,
                issuesBySeverity: {
                    critical: [],
                    warning: [],
                    info: [],
                },
            });

            setStatus('success');
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Veri seti yüklenirken hata oluştu');
            setStatus('error');
        }
    }, [reset]);

    return {
        status,
        progress,
        error,
        uploadedFile,
        dataSummary,
        validationReport,
        uploadFile,
        loadSampleDataset,
        reset,
    };
}

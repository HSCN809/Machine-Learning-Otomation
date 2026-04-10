'use client';

import React, { createContext, useCallback, useContext, useState, ReactNode } from 'react';
import {
    UploadedFile,
    DataSummary,
    ValidationReport,
    ValidationIssue,
    UploadStatus,
    SampleDataset,
} from '@/types/data-upload';
import * as api from '@/lib/api';

export const SAMPLE_DATASETS: SampleDataset[] = [
    { id: 'titanic', name: 'Titanic', description: 'Titanic yolcu verileri', emoji: '🚢', rows: 891, columns: 12 },
    { id: 'iris', name: 'Iris', description: 'Cicek turleri verileri', emoji: '🌸', rows: 150, columns: 6 },
    { id: 'diamonds', name: 'Diamonds', description: 'Elmas ozellikleri', emoji: '💎', rows: 53940, columns: 10 },
    { id: 'planets', name: 'Planets', description: 'Gezegen verileri', emoji: '🪐', rows: 1000, columns: 6 },
];

interface DataUploadContextType {
    status: UploadStatus;
    progress: number;
    error: string | null;
    uploadedFile: UploadedFile | null;
    dataSummary: DataSummary | null;
    validationReport: ValidationReport | null;
    isInitializing: boolean;
    setValidationReport: React.Dispatch<React.SetStateAction<ValidationReport | null>>;
    uploadFile: (file: File) => Promise<void>;
    loadSampleDataset: (datasetId: string) => Promise<void>;
    hydrateSession: () => Promise<void>;
    reset: () => Promise<void>;
}

const DataUploadContext = createContext<DataUploadContextType | undefined>(undefined);

export function DataUploadProvider({ children }: { children: ReactNode }) {
    const [status, setStatus] = useState<UploadStatus>('idle');
    const [progress, setProgress] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [uploadedFile, setUploadedFile] = useState<UploadedFile | null>(null);
    const [dataSummary, setDataSummary] = useState<DataSummary | null>(null);
    const [validationReport, setValidationReport] = useState<ValidationReport | null>(null);
    const [isInitializing, setIsInitializing] = useState(false);

    const buildDataSummary = useCallback(
        (summary: api.DataSummary, preview: Record<string, unknown>[]): DataSummary => ({
            shape: { rows: summary.rows, columns: summary.columns },
            columns: summary.column_info.map((col) => ({
                name: col.name,
                type: (summary.numeric_columns.includes(col.name) ? 'numeric' : 'categorical') as
                    | 'numeric'
                    | 'categorical'
                    | 'datetime'
                    | 'text',
                dtype: col.dtype,
                missingCount: col.missing_count,
                missingPercentage: col.missing_percentage,
                uniqueCount: col.unique_count,
            })),
            missingValues: {
                total: summary.missing_total,
                percentage:
                    summary.rows > 0 ? (summary.missing_total / (summary.rows * summary.columns)) * 100 : 0,
            },
            duplicateRows: summary.duplicate_rows,
            preview,
        }),
        []
    );

    const buildValidationReport = useCallback((validation: api.ValidationResponse): ValidationReport => {
        const issues: ValidationReport['issuesBySeverity'] = {
            critical: [],
            warning: [],
            info: [],
        };

        validation.issues.forEach((issue) => {
            const validationIssue: ValidationIssue = {
                id: issue.id,
                severity: issue.severity,
                type: issue.type as ValidationIssue['type'],
                column: issue.column,
                description: issue.description,
                suggestion: issue.suggestion,
                llmSuggestion: issue.llmSuggestion,
                priority: issue.priority as ValidationIssue['priority'],
            };

            if (issue.severity === 'critical') {
                issues.critical.push(validationIssue);
            } else if (issue.severity === 'warning') {
                issues.warning.push(validationIssue);
            } else {
                issues.info.push(validationIssue);
            }
        });

        return {
            isValid: validation.is_valid,
            totalIssues: validation.issues.length,
            issuesBySeverity: issues,
        };
    }, []);

    const reset = useCallback(async () => {
        try {
            await api.resetUpload();
        } catch (err) {
            console.log('Reset session:', err);
        }

        setStatus('idle');
        setProgress(0);
        setError(null);
        setUploadedFile(null);
        setDataSummary(null);
        setValidationReport(null);
        setIsInitializing(false);
    }, []);

    const uploadFile = useCallback(
        async (file: File) => {
            try {
                setStatus('uploading');
                setProgress(0);
                setError(null);
                setDataSummary(null);
                setValidationReport(null);
                setIsInitializing(false);

                const validTypes = ['.csv', '.xlsx', '.xls', '.json'];
                const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
                if (!validTypes.includes(fileExt)) {
                    throw new Error(`Desteklenmeyen dosya formati: ${fileExt}. Desteklenen: CSV, Excel, JSON`);
                }

                const maxSize = 200 * 1024 * 1024;
                if (file.size > maxSize) {
                    throw new Error(`Dosya boyutu cok buyuk: ${(file.size / 1024 / 1024).toFixed(2)}MB. Maksimum: 200MB`);
                }

                setUploadedFile({
                    file,
                    name: file.name,
                    size: file.size,
                    type: file.type,
                });

                setProgress(30);
                await api.uploadFile(file);
                setProgress(60);
                setStatus('validating');

                const [summary, preview, validation] = await Promise.all([
                    api.getDataSummary(),
                    api.getDataPreview(5),
                    api.getDataValidation(),
                ]);

                setProgress(100);
                setDataSummary(buildDataSummary(summary, preview.data));
                setValidationReport(buildValidationReport(validation));
                setStatus('success');
            } catch (err) {
                console.error('Upload error:', err);
                setError(err instanceof Error ? err.message : 'Yukleme sirasinda hata olustu');
                setStatus('error');
            }
        },
        [buildDataSummary, buildValidationReport]
    );

    const loadSampleDataset = useCallback(
        async (datasetId: string) => {
            try {
                setStatus('uploading');
                setProgress(0);
                setError(null);
                setUploadedFile(null);
                setDataSummary(null);
                setValidationReport(null);
                setIsInitializing(false);

                const dataset = SAMPLE_DATASETS.find((item) => item.id === datasetId);
                if (!dataset) {
                    throw new Error(`Veri seti bulunamadi: ${datasetId}`);
                }

                setUploadedFile({
                    name: dataset.name,
                    size: 0,
                    type: 'sample',
                } as UploadedFile);

                setProgress(30);
                await api.loadSampleDataset(datasetId);
                setProgress(60);
                setStatus('validating');

                const [summary, validation] = await Promise.all([api.getDataSummary(), api.getDataValidation()]);

                setProgress(100);
                setDataSummary(buildDataSummary(summary, []));
                setValidationReport(buildValidationReport(validation));
                setStatus('success');
            } catch (err) {
                console.error('Sample dataset error:', err);
                setError(err instanceof Error ? err.message : 'Veri seti yuklenirken hata olustu');
                setStatus('error');
            }
        },
        [buildDataSummary, buildValidationReport]
    );

    const hydrateSession = useCallback(async () => {
        try {
            setIsInitializing(true);
            setError(null);

            const [summary, preview, validation] = await Promise.all([
                api.getDataSummary(),
                api.getDataPreview(5),
                api.getDataValidation(),
            ]);

            setDataSummary(buildDataSummary(summary, preview.data));
            setValidationReport(buildValidationReport(validation));
            setStatus('success');
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setError(null);
                setUploadedFile(null);
                setDataSummary(null);
                setValidationReport(null);
                setStatus('idle');
            } else {
                console.error('Session hydration error:', err);
                setError(err instanceof Error ? err.message : 'Oturum verisi yuklenirken hata olustu');
                setStatus('error');
            }
        } finally {
            setIsInitializing(false);
        }
    }, [buildDataSummary, buildValidationReport]);

    return (
        <DataUploadContext.Provider
            value={{
                status,
                progress,
                error,
                uploadedFile,
                dataSummary,
                validationReport,
                isInitializing,
                setValidationReport,
                uploadFile,
                loadSampleDataset,
                hydrateSession,
                reset,
            }}
        >
            {children}
        </DataUploadContext.Provider>
    );
}

export function useDataUploadContext() {
    const context = useContext(DataUploadContext);
    if (context === undefined) {
        throw new Error('useDataUploadContext must be used within a DataUploadProvider');
    }
    return context;
}

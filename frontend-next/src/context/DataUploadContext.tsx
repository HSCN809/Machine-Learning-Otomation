'use client';

import React, { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import {
    UploadedFile,
    DataSummary,
    ValidationReport,
    ValidationIssue,
    UploadStatus,
    SampleDataset
} from '@/types/data-upload';
import * as api from '@/lib/api';

// Sample datasets available (matches backend)
export const SAMPLE_DATASETS: SampleDataset[] = [
    { id: 'titanic', name: 'Titanic', description: 'Titanic yolcu verileri', emoji: '🚢', rows: 891, columns: 12 },
    { id: 'iris', name: 'Iris', description: 'Çiçek türleri verileri', emoji: '🌸', rows: 150, columns: 6 },
    { id: 'diamonds', name: 'Diamonds', description: 'Elmas özellikleri', emoji: '💎', rows: 53940, columns: 10 },
    { id: 'planets', name: 'Planets', description: 'Gezegen verileri', emoji: '🪐', rows: 1000, columns: 6 },
];

interface DataUploadContextType {
    // State
    status: UploadStatus;
    progress: number;
    error: string | null;
    uploadedFile: UploadedFile | null;
    dataSummary: DataSummary | null;
    validationReport: ValidationReport | null;
    setValidationReport: React.Dispatch<React.SetStateAction<ValidationReport | null>>;

    // Actions
    uploadFile: (file: File) => Promise<void>;
    loadSampleDataset: (datasetId: string) => Promise<void>;
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

    const reset = useCallback(async () => {
        // Clear backend session
        try {
            await api.resetUpload();
        } catch (err) {
            // Ignore errors when clearing - session may not exist
            console.log('Reset session:', err);
        }

        // Clear frontend state
        setStatus('idle');
        setProgress(0);
        setError(null);
        setUploadedFile(null);
        setDataSummary(null);
        setValidationReport(null);
    }, []);

    const uploadFile = useCallback(async (file: File) => {
        try {
            // Do not call full reset here to keep UI stable if needed, but usually we want to clear previous data
            // We'll mimic the hook logic which calls reset() first, but we need to handle async correctly if we want fully clean state
            // However, resetting state is synchronous.

            // Clear frontend state implicitly by setting new status
            setStatus('uploading');
            setProgress(0);
            setError(null);
            setDataSummary(null);
            setValidationReport(null);

            // Validate file type
            const validTypes = ['.csv', '.xlsx', '.xls', '.json'];
            const fileExt = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
            if (!validTypes.includes(fileExt)) {
                throw new Error(`Desteklenmeyen dosya formatı: ${fileExt}. Desteklenen: CSV, Excel, JSON`);
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

            // Upload to API
            setProgress(30);
            const uploadResponse = await api.uploadFile(file);
            setProgress(60);

            setStatus('validating');

            // Get summary, preview, and validation from backend
            const [summary, preview, validation] = await Promise.all([
                api.getDataSummary(),
                api.getDataPreview(5),
                api.getDataValidation(),
            ]);
            setProgress(100);

            // Transform to DataSummary
            setDataSummary({
                shape: { rows: summary.rows, columns: summary.columns },
                columns: summary.column_info.map(col => ({
                    name: col.name,
                    type: (summary.numeric_columns.includes(col.name) ? 'numeric' : 'categorical') as 'numeric' | 'categorical' | 'datetime' | 'text',
                    dtype: col.dtype,
                    missingCount: col.missing_count,
                    missingPercentage: col.missing_percentage,
                    uniqueCount: col.unique_count,
                })),
                missingValues: {
                    total: summary.missing_total,
                    percentage: summary.rows > 0 ? (summary.missing_total / (summary.rows * summary.columns)) * 100 : 0,
                },
                duplicateRows: summary.duplicate_rows,
                preview: preview.data,
            });

            // Build validation report from backend response
            const issues: ValidationReport['issuesBySeverity'] = {
                critical: [],
                warning: [],
                info: [],
            };

            // Categorize issues by severity
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

            setValidationReport({
                isValid: validation.is_valid,
                totalIssues: validation.issues.length,
                issuesBySeverity: issues,
            });

            setStatus('success');
        } catch (err) {
            console.error('Upload error:', err);
            setError(err instanceof Error ? err.message : 'Yükleme sırasında hata oluştu');
            setStatus('error');
        }
    }, []);

    const loadSampleDataset = useCallback(async (datasetId: string) => {
        try {
            // Reset frontend state
            setStatus('uploading');
            setProgress(0);
            setError(null);
            setUploadedFile(null); // Technically it's not a file upload, but we might want to represent it
            setDataSummary(null);
            setValidationReport(null);

            const dataset = SAMPLE_DATASETS.find(d => d.id === datasetId);
            if (!dataset) {
                throw new Error(`Veri seti bulunamadı: ${datasetId}`);
            }

            // Set uploaded file "mock" for UI display
            setUploadedFile({
                name: dataset.name,
                size: 0,
                type: 'sample',
            } as UploadedFile);

            setProgress(30);

            // Call backend API to load sample dataset
            const loadResponse = await api.loadSampleDataset(datasetId);
            setProgress(60);

            setStatus('validating');

            // Get summary and validation from backend
            const [summary, validation] = await Promise.all([
                api.getDataSummary(),
                api.getDataValidation(),
            ]);
            setProgress(100);

            // Transform to DataSummary
            setDataSummary({
                shape: { rows: summary.rows, columns: summary.columns },
                columns: summary.column_info.map(col => ({
                    name: col.name,
                    type: (summary.numeric_columns.includes(col.name) ? 'numeric' : 'categorical') as 'numeric' | 'categorical' | 'datetime' | 'text',
                    dtype: col.dtype,
                    missingCount: col.missing_count,
                    missingPercentage: col.missing_percentage,
                    uniqueCount: col.unique_count,
                })),
                missingValues: {
                    total: summary.missing_total,
                    percentage: summary.rows > 0 ? (summary.missing_total / (summary.rows * summary.columns)) * 100 : 0,
                },
                duplicateRows: summary.duplicate_rows,
                preview: [],
            });

            // Build validation report from backend response
            const issues: ValidationReport['issuesBySeverity'] = {
                critical: [],
                warning: [],
                info: [],
            };

            // Categorize issues by severity
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

            setValidationReport({
                isValid: validation.is_valid,
                totalIssues: validation.issues.length,
                issuesBySeverity: issues,
            });

            setStatus('success');
        } catch (err) {
            console.error('Sample dataset error:', err);
            setError(err instanceof Error ? err.message : 'Veri seti yüklenirken hata oluştu');
            setStatus('error');
        }
    }, []);

    return (
        <DataUploadContext.Provider
            value={{
                status,
                progress,
                error,
                uploadedFile,
                dataSummary,
                validationReport,
                setValidationReport,
                uploadFile,
                loadSampleDataset,
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

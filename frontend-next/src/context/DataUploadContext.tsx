'use client';

import React, { createContext, useCallback, useContext, useEffect, useState, ReactNode } from 'react';
import {
    UploadedFile,
    DataSummary,
    ValidationReport,
    ValidationIssue,
    UploadStatus,
    PersistedDatasetSummary,
    SampleDataset,
} from '@/types/data-upload';
import * as api from '@/lib/api';
import { logger } from '@/lib/logger';
import { getErrorMessage, notify } from '@/lib/notify';

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
    savedDatasets: PersistedDatasetSummary[];
    activeDatasetId: string | null;
    isSavedDatasetsLoading: boolean;
    uploadFile: (file: File) => Promise<void>;
    loadSampleDataset: (datasetId: string) => Promise<void>;
    loadSavedDataset: (datasetId: string) => Promise<void>;
    renameSavedDataset: (datasetId: string, name: string) => Promise<void>;
    deleteSavedDataset: (datasetId: string) => Promise<void>;
    hydrateSession: () => Promise<void>;
    refreshSavedDatasets: () => Promise<void>;
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
    const [savedDatasets, setSavedDatasets] = useState<PersistedDatasetSummary[]>([]);
    const [activeDatasetId, setActiveDatasetId] = useState<string | null>(api.getStoredSessionId());
    const [isSavedDatasetsLoading, setIsSavedDatasetsLoading] = useState(false);

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

    useEffect(() => {
        return api.subscribeToStoredSession(() => {
            setActiveDatasetId(api.getStoredSessionId());
        });
    }, []);

    const clearLoadedState = useCallback((nextStatus: UploadStatus = 'idle') => {
        setStatus(nextStatus);
        setProgress(0);
        setError(null);
        setUploadedFile(null);
        setDataSummary(null);
        setValidationReport(null);
        setIsInitializing(false);
    }, []);

    const refreshSavedDatasets = useCallback(async () => {
        try {
            setIsSavedDatasetsLoading(true);
            setSavedDatasets(await api.getSavedDatasets());
        } catch (err) {
            logger.error('Saved dataset list load failed', err);
        } finally {
            setIsSavedDatasetsLoading(false);
        }
    }, []);

    const reset = useCallback(async () => {
        try {
            await api.resetUpload();
        } catch (err) {
            const message = getErrorMessage(err, 'Oturum verisi temizlenirken hata oluştu');
            logger.error('Reset session failed', err);
            setError(message);
            setStatus('error');
            notify.error(err, 'Oturum verisi temizlenirken hata oluştu');
            return;
        }

        clearLoadedState('idle');
        await refreshSavedDatasets();
    }, [clearLoadedState, refreshSavedDatasets]);

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
                await refreshSavedDatasets();
                notify.success('Dosya yüklendi');
            } catch (err) {
                const message = getErrorMessage(err, 'Yükleme sırasında hata oluştu');
                logger.error('Upload failed', err);
                setError(message);
                setStatus('error');
                notify.error(err, 'Yükleme sırasında hata oluştu');
            }
        },
        [buildDataSummary, buildValidationReport, refreshSavedDatasets]
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
                await refreshSavedDatasets();
                notify.success('Örnek veri seti yüklendi');
            } catch (err) {
                const message = getErrorMessage(err, 'Veri seti yüklenirken hata oluştu');
                logger.error('Sample dataset load failed', err);
                setError(message);
                setStatus('error');
                notify.error(err, 'Veri seti yüklenirken hata oluştu');
            }
        },
        [buildDataSummary, buildValidationReport, refreshSavedDatasets]
    );

    const hydrateSession = useCallback(async () => {
        try {
            setIsInitializing(true);
            setError(null);

            const [summary, preview] = await Promise.all([
                api.getDataSummary(),
                api.getDataPreview(5),
            ]);

            setDataSummary(buildDataSummary(summary, preview.data));
            setValidationReport(null);
            setStatus('success');
            const currentDatasetId = api.getStoredSessionId();
            const activeSavedDataset = savedDatasets.find((dataset) => dataset.id === currentDatasetId);
            if (activeSavedDataset) {
                setUploadedFile({
                    name: activeSavedDataset.name,
                    size: 0,
                    type: 'saved',
                } as UploadedFile);
            }

            await refreshSavedDatasets();
            void api.getDataValidation()
                .then((validation) => setValidationReport(buildValidationReport(validation)))
                .catch((validationError) => {
                    if (!api.isSessionRequiredError(validationError)) {
                        logger.error('Session validation hydration failed', validationError);
                    }
                });
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                clearLoadedState('idle');
            } else {
                logger.error('Session hydration failed', err);
                setError(getErrorMessage(err, 'Oturum verisi yüklenirken hata oluştu'));
                setStatus('error');
            }
        } finally {
            setIsInitializing(false);
        }
    }, [
        buildDataSummary,
        buildValidationReport,
        clearLoadedState,
        refreshSavedDatasets,
        savedDatasets,
    ]);

    const loadSavedDataset = useCallback(
        async (datasetId: string) => {
            try {
                setIsInitializing(true);
                setError(null);
                await api.loadSavedDataset(datasetId);
                await hydrateSession();
                notify.success('Kayıtlı veri seti yüklendi');
            } catch (err) {
                const message = getErrorMessage(err, 'Kayıtlı veri seti yüklenemedi');
                logger.error('Saved dataset load failed', err, { datasetId });
                setError(message);
                notify.error(err, 'Kayıtlı veri seti yüklenemedi');
            } finally {
                setIsInitializing(false);
            }
        },
        [hydrateSession]
    );

    const renameSavedDataset = useCallback(
        async (datasetId: string, name: string) => {
            try {
                setError(null);
                const trimmedName = name.trim();
                if (!trimmedName) {
                    throw new Error('Veri seti adı boş bırakılamaz');
                }

                await api.renameSavedDataset(datasetId, trimmedName);
                if (activeDatasetId === datasetId && uploadedFile) {
                    setUploadedFile({
                        ...uploadedFile,
                        name: trimmedName,
                    });
                }

                await refreshSavedDatasets();
                notify.success('Veri seti adı güncellendi');
            } catch (err) {
                const message = getErrorMessage(err, 'Veri seti adı güncellenemedi');
                logger.error('Saved dataset rename failed', err, { datasetId });
                setError(message);
                notify.error(err, 'Veri seti adı güncellenemedi');
            }
        },
        [activeDatasetId, refreshSavedDatasets, uploadedFile]
    );

    const deleteSavedDataset = useCallback(
        async (datasetId: string) => {
            try {
                setError(null);
                await api.deleteSavedDataset(datasetId);

                if (activeDatasetId === datasetId) {
                    api.clearStoredSession();
                    clearLoadedState('idle');
                }

                await refreshSavedDatasets();
                notify.success('Veri seti silindi');
            } catch (err) {
                const message = getErrorMessage(err, 'Veri seti silinemedi');
                logger.error('Saved dataset delete failed', err, { datasetId });
                setError(message);
                notify.error(err, 'Veri seti silinemedi');
            }
        },
        [activeDatasetId, clearLoadedState, refreshSavedDatasets]
    );

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
                savedDatasets,
                activeDatasetId,
                isSavedDatasetsLoading,
                uploadFile,
                loadSampleDataset,
                loadSavedDataset,
                renameSavedDataset,
                deleteSavedDataset,
                hydrateSession,
                refreshSavedDatasets,
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

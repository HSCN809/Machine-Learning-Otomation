'use client';

import { useState, useCallback, useMemo } from 'react';
import {
    PreprocessingStep,
    ProcessingHistory,
    ColumnInfo,
    MissingValueConfig,
    OutlierConfig,
    EncodingConfig,
    ScalingConfig,
    FeatureConfig,
} from '@/types/preprocessing';
import * as api from '@/lib/api';

type ApiHistoryEntry = {
    step?: string;
    action?: string;
    columns?: string[];
    source_columns?: string[];
    new_columns?: string[];
    params?: Record<string, unknown>;
    affected_rows?: number;
    timestamp?: string;
};

const HISTORY_ACTION_BY_STEP: Record<string, string> = {
    missing_values: 'fill_missing',
    outliers: 'handle_outliers',
    encoding: 'encode_categorical',
    scaling: 'scale_numeric',
    feature_engineering: 'create_feature',
};

function mapColumns(columnTypes: Awaited<ReturnType<typeof api.getColumnTypes>>['columns']): ColumnInfo[] {
    return columnTypes.map(col => ({
        name: col.name,
        type: col.type,
        dtype: col.dtype,
        missingCount: col.null_count,
        missingPercentage: col.null_percentage,
        uniqueCount: col.unique_count,
    }));
}

function mapHistoryEntry(entry: unknown, index: number): ProcessingHistory | null {
    if (!entry || typeof entry !== 'object') {
        return null;
    }

    const rawEntry = entry as ApiHistoryEntry;
    const stepKey = rawEntry.step;
    const method = rawEntry.action;

    if (!stepKey || !method) {
        return null;
    }

    const parsedTimestamp = rawEntry.timestamp ? new Date(rawEntry.timestamp) : new Date();
    const timestamp = Number.isNaN(parsedTimestamp.getTime()) ? new Date() : parsedTimestamp;

    return {
        id: `${stepKey}-${rawEntry.timestamp ?? index}-${index}`,
        historyIndex: index,
        stepKey,
        action: HISTORY_ACTION_BY_STEP[stepKey] || method,
        columns: rawEntry.columns ?? rawEntry.source_columns ?? [],
        newColumns: rawEntry.new_columns,
        method,
        params: rawEntry.params,
        timestamp,
        affectedRows: rawEntry.affected_rows,
    };
}

// Preprocessing steps definition
export const PREPROCESSING_STEPS: PreprocessingStep[] = [
    { id: '1', name: 'Missing Values', icon: '❓', key: 'missing_values', description: 'Eksik değerleri işle' },
    { id: '2', name: 'Outliers', icon: '📊', key: 'outliers', description: 'Aykırı değerleri tespit et ve işle' },
    { id: '3', name: 'Feature Engineering', icon: '🛠️', key: 'feature_engineering', description: 'Yeni özellikler oluştur' },
    { id: '4', name: 'Encoding', icon: '🔤', key: 'encoding', description: 'Kategorik değişkenleri kodla' },
    { id: '5', name: 'Scaling', icon: '📏', key: 'scaling', description: 'Sayısal değişkenleri ölçeklendir' },
    { id: '6', name: 'Summary', icon: '📋', key: 'summary', description: 'İşlemleri gözden geçir' },
];

interface UsePreprocessingReturn {
    // State
    currentStep: number;
    completedSteps: number[];
    skippedSteps: number[];
    history: ProcessingHistory[];
    columns: ColumnInfo[];
    isLoading: boolean;
    error: string | null; /*

            setError(err instanceof Error ? err.message : 'İşlem geçmişi yüklenirken hata oluştu');

    /*
    /*
    const loadInitialData = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);

            const [columnTypes, historyResponse] = await Promise.all([
                api.getColumnTypes(),
                api.getPreprocessingHistory(),
            ]);

            setColumns(mapColumns(columnTypes.columns));
            const nextHistory = historyResponse.history
                .map((entry, index) => mapHistoryEntry(entry, index))
                .filter((entry): entry is ProcessingHistory => entry !== null);
            setHistory(nextHistory);
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setColumns([]);
                setHistory([]);
                setError(null);
                return;
            }
            console.error('Load preprocessing data error:', err);
            setError(err instanceof Error ? err.message : 'Ön işleme verileri yüklenirken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, []);

    */
    // Navigation
    goToStep: (step: number) => void;
    nextStep: () => void;
    skipStep: () => void;
    prevStep: () => void;
    canGoNext: boolean;
    canGoPrev: boolean;

    // Actions
    loadInitialData: () => Promise<void>;
    loadColumns: () => Promise<void>;
    loadHistory: () => Promise<void>;
    applyMissingValues: (config: MissingValueConfig) => Promise<void>;
    applyOutliers: (config: OutlierConfig) => Promise<void>;
    applyEncoding: (config: EncodingConfig) => Promise<void>;
    applyScaling: (config: ScalingConfig) => Promise<void>;
    applyFeatureEngineering: (config: FeatureConfig) => Promise<void>;
    undoLastAction: () => Promise<void>;
    undoToHistoryItem: (historyIndex: number) => Promise<void>;
    resetAll: () => Promise<void>;

    // Helpers
    numericColumns: ColumnInfo[];
    categoricalColumns: ColumnInfo[];
    columnsWithMissing: ColumnInfo[];
}

export function usePreprocessing(): UsePreprocessingReturn {
    const [currentStep, setCurrentStep] = useState(0);
    const [completedSteps, setCompletedSteps] = useState<number[]>([]);
    const [skippedSteps, setSkippedSteps] = useState<number[]>([]);
    const [history, setHistory] = useState<ProcessingHistory[]>([]);
    const [columns, setColumns] = useState<ColumnInfo[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Load columns from API
    const loadColumns = useCallback(async () => {
        try {
            setIsLoading(true);
            const columnTypes = await api.getColumnTypes();

            const cols: ColumnInfo[] = columnTypes.columns.map(col => ({
                name: col.name,
                type: col.type,
                dtype: col.dtype,
                missingCount: col.null_count,
                missingPercentage: col.null_percentage,
                uniqueCount: col.unique_count,
            }));

            setColumns(cols);
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setColumns([]);
                setError(null);
                return;
            }
            console.error('Load columns error:', err);
            setError(err instanceof Error ? err.message : 'Sütunlar yüklenirken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const loadHistory = useCallback(async () => {
        try {
            setIsLoading(true);
            const historyResponse = await api.getPreprocessingHistory();
            const nextHistory = historyResponse.history
                .map((entry, index) => mapHistoryEntry(entry, index))
                .filter((entry): entry is ProcessingHistory => entry !== null);
            setHistory(nextHistory);
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setHistory([]);
                setError(null);
                return;
            }
            console.error('Load history error:', err);
            setError(err instanceof Error ? err.message : 'İşlem geçmişi yüklenirken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const loadInitialData = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);

            const [columnTypes, historyResponse] = await Promise.all([
                api.getColumnTypes(),
                api.getPreprocessingHistory(),
            ]);

            setColumns(mapColumns(columnTypes.columns));
            const nextHistory = historyResponse.history
                .map((entry, index) => mapHistoryEntry(entry, index))
                .filter((entry): entry is ProcessingHistory => entry !== null);
            setHistory(nextHistory);
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setColumns([]);
                setHistory([]);
                setError(null);
                return;
            }
            console.error('Load preprocessing data error:', err);
            setError(err instanceof Error ? err.message : 'Ön işleme verileri yüklenirken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Navigation
    const goToStep = useCallback((step: number) => {
        if (step >= 0 && step < PREPROCESSING_STEPS.length) {
            setCurrentStep(step);
        }
    }, []);

    const nextStep = useCallback(() => {
        if (currentStep < PREPROCESSING_STEPS.length - 1) {
            setSkippedSteps((prev) => prev.filter((step) => step !== currentStep));
            if (!completedSteps.includes(currentStep)) {
                setCompletedSteps(prev => [...prev, currentStep]);
            }
            setCurrentStep(prev => prev + 1);
        }
    }, [currentStep, completedSteps]);

    const skipStep = useCallback(() => {
        if (currentStep < PREPROCESSING_STEPS.length - 1) {
            setCompletedSteps((prev) => prev.filter((step) => step !== currentStep));
            if (!skippedSteps.includes(currentStep)) {
                setSkippedSteps((prev) => [...prev, currentStep]);
            }
            setCurrentStep((prev) => prev + 1);
        }
    }, [currentStep, skippedSteps]);

    const prevStep = useCallback(() => {
        if (currentStep > 0) {
            setCurrentStep(prev => prev - 1);
        }
    }, [currentStep]);

    const canGoNext = currentStep < PREPROCESSING_STEPS.length - 1;
    const canGoPrev = currentStep > 0;

    const refreshColumnsAndHistory = useCallback(async () => {
        const [columnTypes, historyResponse] = await Promise.all([
            api.getColumnTypes(),
            api.getPreprocessingHistory(),
        ]);

        setColumns(mapColumns(columnTypes.columns));
        const nextHistory = historyResponse.history
            .map((entry, index) => mapHistoryEntry(entry, index))
            .filter((entry): entry is ProcessingHistory => entry !== null);
        setHistory(nextHistory);
    }, []);

    // Actions - connected to API
    const applyMissingValues = useCallback(async (config: MissingValueConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyMissingValues(config.method, config.columns);

            await refreshColumnsAndHistory();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [refreshColumnsAndHistory]);

    const applyOutliers = useCallback(async (config: OutlierConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyOutliers(
                config.method,
                config.columns,
                config.threshold,
                config.winsorizePercent
            );

            await refreshColumnsAndHistory();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [refreshColumnsAndHistory]);

    const applyEncoding = useCallback(async (config: EncodingConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyEncoding(
                config.method,
                config.columns,
                config.dropFirst
            );

            await refreshColumnsAndHistory();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [refreshColumnsAndHistory]);

    const applyScaling = useCallback(async (config: ScalingConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyScaling(config.method, config.columns);

            await refreshColumnsAndHistory();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [refreshColumnsAndHistory]);

    const applyFeatureEngineering = useCallback(async (config: FeatureConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyFeatureEngineering(config);

            await refreshColumnsAndHistory();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [refreshColumnsAndHistory]);

    const undoLastAction = useCallback(async () => {
        if (history.length === 0) {
            return;
        }

        try {
            setIsLoading(true);
            setError(null);
            await api.undoPreprocessing();
            await refreshColumnsAndHistory();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Geri alma sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [history.length, refreshColumnsAndHistory]);

    const undoToHistoryItem = useCallback(async (historyIndex: number) => {
        try {
            setIsLoading(true);
            setError(null);
            await api.undoPreprocessingTo(historyIndex);
            await refreshColumnsAndHistory();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Seçili işlem geri alınırken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [refreshColumnsAndHistory]);

    const resetAll = useCallback(async () => {
        try {
            setIsLoading(true);
            await api.resetPreprocessing();
            setHistory([]);
            setCompletedSteps([]);
            setSkippedSteps([]);
            setCurrentStep(0);
            await loadColumns();
            setError(null);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Sıfırlama sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [loadColumns]);

    // Memoized column filters
    const numericColumns = useMemo(() =>
        columns.filter(col => col.type === 'numeric'), [columns]);

    const categoricalColumns = useMemo(() =>
        columns.filter(col => col.type === 'categorical'), [columns]);

    const columnsWithMissing = useMemo(() =>
        columns.filter(col => col.missingCount > 0), [columns]);

    return {
        currentStep,
        completedSteps,
        skippedSteps,
        history,
        columns,
        isLoading,
        error,
        goToStep,
        nextStep,
        skipStep,
        prevStep,
        canGoNext,
        canGoPrev,
        loadInitialData,
        loadColumns,
        loadHistory,
        applyMissingValues,
        applyOutliers,
        applyEncoding,
        applyScaling,
        applyFeatureEngineering,
        undoLastAction,
        undoToHistoryItem,
        resetAll,
        numericColumns,
        categoricalColumns,
        columnsWithMissing,
    };
}

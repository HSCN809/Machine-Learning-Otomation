'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
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

// Preprocessing steps definition
export const PREPROCESSING_STEPS: PreprocessingStep[] = [
    { id: '1', name: 'Feature Engineering', icon: '🛠️', key: 'feature_engineering', description: 'Yeni özellikler oluştur' },
    { id: '2', name: 'Missing Values', icon: '❓', key: 'missing_values', description: 'Eksik değerleri işle' },
    { id: '3', name: 'Outliers', icon: '📊', key: 'outliers', description: 'Aykırı değerleri tespit et ve işle' },
    { id: '4', name: 'Encoding', icon: '🔤', key: 'encoding', description: 'Kategorik değişkenleri kodla' },
    { id: '5', name: 'Scaling', icon: '📏', key: 'scaling', description: 'Sayısal değişkenleri ölçeklendir' },
    { id: '6', name: 'Summary', icon: '📋', key: 'summary', description: 'İşlemleri gözden geçir' },
];

interface UsePreprocessingReturn {
    // State
    currentStep: number;
    completedSteps: number[];
    history: ProcessingHistory[];
    columns: ColumnInfo[];
    isLoading: boolean;
    error: string | null;

    // Navigation
    goToStep: (step: number) => void;
    nextStep: () => void;
    prevStep: () => void;
    canGoNext: boolean;
    canGoPrev: boolean;

    // Actions
    loadColumns: () => Promise<void>;
    applyMissingValues: (config: MissingValueConfig) => Promise<void>;
    applyOutliers: (config: OutlierConfig) => Promise<void>;
    applyEncoding: (config: EncodingConfig) => Promise<void>;
    applyScaling: (config: ScalingConfig) => Promise<void>;
    applyFeatureEngineering: (config: FeatureConfig) => Promise<void>;
    undoLastAction: () => void;
    resetAll: () => Promise<void>;

    // Helpers
    numericColumns: ColumnInfo[];
    categoricalColumns: ColumnInfo[];
    columnsWithMissing: ColumnInfo[];
}

export function usePreprocessing(): UsePreprocessingReturn {
    const [currentStep, setCurrentStep] = useState(0);
    const [completedSteps, setCompletedSteps] = useState<number[]>([]);
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
                type: col.type === 'numeric' ? 'numeric' : 'categorical',
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

    // Navigation
    const goToStep = useCallback((step: number) => {
        if (step >= 0 && step < PREPROCESSING_STEPS.length) {
            setCurrentStep(step);
        }
    }, []);

    const nextStep = useCallback(() => {
        if (currentStep < PREPROCESSING_STEPS.length - 1) {
            if (!completedSteps.includes(currentStep)) {
                setCompletedSteps(prev => [...prev, currentStep]);
            }
            setCurrentStep(prev => prev + 1);
        }
    }, [currentStep, completedSteps]);

    const prevStep = useCallback(() => {
        if (currentStep > 0) {
            setCurrentStep(prev => prev - 1);
        }
    }, [currentStep]);

    const canGoNext = currentStep < PREPROCESSING_STEPS.length - 1;
    const canGoPrev = currentStep > 0;

    // Add to history helper
    const addToHistory = useCallback((entry: Omit<ProcessingHistory, 'id' | 'timestamp'>) => {
        const newEntry: ProcessingHistory = {
            ...entry,
            id: `${Date.now()}`,
            timestamp: new Date(),
        };
        setHistory(prev => [...prev, newEntry]);
    }, []);

    // Actions - connected to API
    const applyMissingValues = useCallback(async (config: MissingValueConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            const result = await api.applyMissingValues(
                config.method,
                config.columns,
                config.fillValue !== undefined ? String(config.fillValue) : undefined
            );

            addToHistory({
                stepKey: 'missing_values',
                action: 'fill_missing',
                columns: config.columns,
                method: config.method,
                params: config.fillValue ? { fillValue: config.fillValue } : undefined,
                affectedRows: result.affected_rows || 0,
            });

            // Refresh columns
            await loadColumns();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory, loadColumns]);

    const applyOutliers = useCallback(async (config: OutlierConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            const result = await api.applyOutliers(
                config.method,
                config.columns,
                config.threshold
            );

            addToHistory({
                stepKey: 'outliers',
                action: 'handle_outliers',
                columns: config.columns,
                method: config.method,
                params: config.threshold ? { threshold: config.threshold } : undefined,
                affectedRows: result.affected_rows || 0,
            });

            await loadColumns();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory, loadColumns]);

    const applyEncoding = useCallback(async (config: EncodingConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            const result = await api.applyEncoding(
                config.method,
                config.columns,
                config.dropFirst
            );

            addToHistory({
                stepKey: 'encoding',
                action: 'encode_categorical',
                columns: config.columns,
                method: config.method,
                params: { dropFirst: config.dropFirst },
            });

            await loadColumns();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory, loadColumns]);

    const applyScaling = useCallback(async (config: ScalingConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyScaling(config.method, config.columns);

            addToHistory({
                stepKey: 'scaling',
                action: 'scale_numeric',
                columns: config.columns,
                method: config.method,
                params: config.featureRange ? { featureRange: config.featureRange } : undefined,
            });

            await loadColumns();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory, loadColumns]);

    const applyFeatureEngineering = useCallback(async (config: FeatureConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            // For now, just add to history - API doesn't have full feature engineering yet
            addToHistory({
                stepKey: 'feature_engineering',
                action: 'create_feature',
                column: config.newColumnName,
                columns: config.sourceColumns,
                method: config.operation,
                params: { expression: config.expression },
            });

            await loadColumns();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory, loadColumns]);

    const undoLastAction = useCallback(() => {
        if (history.length > 0) {
            setHistory(prev => prev.slice(0, -1));
        }
    }, [history]);

    const resetAll = useCallback(async () => {
        try {
            setIsLoading(true);
            await api.resetPreprocessing();
            setHistory([]);
            setCompletedSteps([]);
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
        history,
        columns,
        isLoading,
        error,
        goToStep,
        nextStep,
        prevStep,
        canGoNext,
        canGoPrev,
        loadColumns,
        applyMissingValues,
        applyOutliers,
        applyEncoding,
        applyScaling,
        applyFeatureEngineering,
        undoLastAction,
        resetAll,
        numericColumns,
        categoricalColumns,
        columnsWithMissing,
    };
}

'use client';

import { useState, useCallback, useMemo } from 'react';
import {
    PreprocessingStep,
    ProcessingHistory,
    PreprocessingState,
    ColumnInfo,
    MissingValueConfig,
    OutlierConfig,
    EncodingConfig,
    ScalingConfig,
    FeatureConfig,
} from '@/types/preprocessing';

// Preprocessing steps definition
export const PREPROCESSING_STEPS: PreprocessingStep[] = [
    { id: '1', name: 'Feature Engineering', icon: '🛠️', key: 'feature_engineering', description: 'Yeni özellikler oluştur' },
    { id: '2', name: 'Missing Values', icon: '❓', key: 'missing_values', description: 'Eksik değerleri işle' },
    { id: '3', name: 'Outliers', icon: '📊', key: 'outliers', description: 'Aykırı değerleri tespit et ve işle' },
    { id: '4', name: 'Encoding', icon: '🔤', key: 'encoding', description: 'Kategorik değişkenleri kodla' },
    { id: '5', name: 'Scaling', icon: '📏', key: 'scaling', description: 'Sayısal değişkenleri ölçeklendir' },
    { id: '6', name: 'Summary', icon: '📋', key: 'summary', description: 'İşlemleri gözden geçir' },
];

// Mock column info generator
function generateMockColumnInfo(): ColumnInfo[] {
    return [
        { name: 'age', type: 'numeric', dtype: 'int64', missingCount: 50, missingPercentage: 5, uniqueCount: 80 },
        { name: 'salary', type: 'numeric', dtype: 'float64', missingCount: 20, missingPercentage: 2, uniqueCount: 500 },
        { name: 'experience', type: 'numeric', dtype: 'int64', missingCount: 0, missingPercentage: 0, uniqueCount: 30 },
        { name: 'department', type: 'categorical', dtype: 'object', missingCount: 5, missingPercentage: 0.5, uniqueCount: 8 },
        { name: 'gender', type: 'categorical', dtype: 'object', missingCount: 0, missingPercentage: 0, uniqueCount: 2 },
        { name: 'status', type: 'categorical', dtype: 'object', missingCount: 10, missingPercentage: 1, uniqueCount: 4 },
    ];
}

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
    applyMissingValues: (config: MissingValueConfig) => Promise<void>;
    applyOutliers: (config: OutlierConfig) => Promise<void>;
    applyEncoding: (config: EncodingConfig) => Promise<void>;
    applyScaling: (config: ScalingConfig) => Promise<void>;
    applyFeatureEngineering: (config: FeatureConfig) => Promise<void>;
    undoLastAction: () => void;
    resetAll: () => void;

    // Helpers
    numericColumns: ColumnInfo[];
    categoricalColumns: ColumnInfo[];
    columnsWithMissing: ColumnInfo[];
}

export function usePreprocessing(): UsePreprocessingReturn {
    const [currentStep, setCurrentStep] = useState(0);
    const [completedSteps, setCompletedSteps] = useState<number[]>([]);
    const [history, setHistory] = useState<ProcessingHistory[]>([]);
    const [columns, setColumns] = useState<ColumnInfo[]>(generateMockColumnInfo());
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

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

    // Actions
    const applyMissingValues = useCallback(async (config: MissingValueConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 500));

            addToHistory({
                stepKey: 'missing_values',
                action: 'fill_missing',
                columns: config.columns,
                method: config.method,
                params: config.fillValue ? { fillValue: config.fillValue } : undefined,
                affectedRows: Math.floor(Math.random() * 100) + 10,
            });

            // Update columns to reflect changes
            setColumns(prev => prev.map(col =>
                config.columns.includes(col.name)
                    ? { ...col, missingCount: 0, missingPercentage: 0 }
                    : col
            ));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory]);

    const applyOutliers = useCallback(async (config: OutlierConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await new Promise(resolve => setTimeout(resolve, 500));

            addToHistory({
                stepKey: 'outliers',
                action: 'handle_outliers',
                columns: config.columns,
                method: config.method,
                params: config.threshold ? { threshold: config.threshold } : undefined,
                affectedRows: Math.floor(Math.random() * 50) + 5,
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory]);

    const applyEncoding = useCallback(async (config: EncodingConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await new Promise(resolve => setTimeout(resolve, 500));

            addToHistory({
                stepKey: 'encoding',
                action: 'encode_categorical',
                columns: config.columns,
                method: config.method,
                params: { dropFirst: config.dropFirst },
            });

            // Update column types after encoding
            setColumns(prev => prev.map(col =>
                config.columns.includes(col.name)
                    ? { ...col, type: 'numeric' as const, dtype: 'int64' }
                    : col
            ));
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory]);

    const applyScaling = useCallback(async (config: ScalingConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await new Promise(resolve => setTimeout(resolve, 500));

            addToHistory({
                stepKey: 'scaling',
                action: 'scale_numeric',
                columns: config.columns,
                method: config.method,
                params: config.featureRange ? { featureRange: config.featureRange } : undefined,
            });
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory]);

    const applyFeatureEngineering = useCallback(async (config: FeatureConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await new Promise(resolve => setTimeout(resolve, 500));

            addToHistory({
                stepKey: 'feature_engineering',
                action: 'create_feature',
                column: config.newColumnName,
                columns: config.sourceColumns,
                method: config.operation,
                params: { expression: config.expression },
            });

            // Add new column
            setColumns(prev => [...prev, {
                name: config.newColumnName,
                type: 'numeric',
                dtype: 'float64',
                missingCount: 0,
                missingPercentage: 0,
                uniqueCount: 100,
            }]);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [addToHistory]);

    const undoLastAction = useCallback(() => {
        if (history.length > 0) {
            setHistory(prev => prev.slice(0, -1));
            // In real implementation, would also revert data changes
        }
    }, [history]);

    const resetAll = useCallback(() => {
        setHistory([]);
        setCompletedSteps([]);
        setCurrentStep(0);
        setColumns(generateMockColumnInfo());
        setError(null);
    }, []);

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

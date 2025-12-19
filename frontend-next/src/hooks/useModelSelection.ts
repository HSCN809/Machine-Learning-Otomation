'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import {
    ProblemType,
    ModelInfo,
    TrainingResult,
    ModelMetrics,
    FeatureImportance,
    CLASSIFICATION_MODELS,
    REGRESSION_MODELS,
} from '@/types/model-selection';
import * as api from '@/lib/api';

interface ColumnInfo {
    name: string;
    type: 'numeric' | 'categorical';
    uniqueValues: number;
}

interface UseModelSelectionReturn {
    // State
    currentStep: number;
    targetColumn: string | null;
    problemType: ProblemType | null;
    selectedModels: string[];
    modelParams: Record<string, Record<string, unknown>>;
    trainingResults: TrainingResult[];
    isTraining: boolean;
    error: string | null;
    columns: ColumnInfo[];

    // Available models based on problem type
    availableModels: ModelInfo[];

    // Navigation
    goToStep: (step: number) => void;
    nextStep: () => void;
    prevStep: () => void;
    canGoNext: boolean;
    canGoPrev: boolean;

    // Actions
    loadColumns: () => Promise<void>;
    setTargetColumn: (column: string) => void;
    toggleModelSelection: (modelId: string) => void;
    updateModelParams: (modelId: string, params: Record<string, unknown>) => void;
    trainModels: () => Promise<void>;
    resetAll: () => void;
}

export function useModelSelection(): UseModelSelectionReturn {
    const [currentStep, setCurrentStep] = useState(0);
    const [targetColumn, setTargetColumnState] = useState<string | null>(null);
    const [problemType, setProblemType] = useState<ProblemType | null>(null);
    const [selectedModels, setSelectedModels] = useState<string[]>([]);
    const [modelParams, setModelParams] = useState<Record<string, Record<string, unknown>>>({});
    const [trainingResults, setTrainingResults] = useState<TrainingResult[]>([]);
    const [isTraining, setIsTraining] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [columns, setColumns] = useState<ColumnInfo[]>([]);

    // Load columns from API
    const loadColumns = useCallback(async () => {
        try {
            const columnTypes = await api.getColumnTypes();

            const cols: ColumnInfo[] = columnTypes.columns.map(col => ({
                name: col.name,
                type: col.type === 'numeric' ? 'numeric' : 'categorical',
                uniqueValues: col.unique_count,
            }));

            setColumns(cols);
        } catch (err) {
            console.error('Load columns error:', err);
            setError(err instanceof Error ? err.message : 'Sütunlar yüklenirken hata oluştu');
        }
    }, []);

    // Available models based on problem type
    const availableModels = useMemo(() => {
        if (problemType === 'classification') return CLASSIFICATION_MODELS;
        if (problemType === 'regression') return REGRESSION_MODELS;
        return [];
    }, [problemType]);

    // Navigation
    const goToStep = useCallback((step: number) => {
        if (step >= 0 && step <= 4) {
            setCurrentStep(step);
        }
    }, []);

    const nextStep = useCallback(() => {
        if (currentStep < 4) {
            setCurrentStep(prev => prev + 1);
        }
    }, [currentStep]);

    const prevStep = useCallback(() => {
        if (currentStep > 0) {
            setCurrentStep(prev => prev - 1);
        }
    }, [currentStep]);

    // Can proceed validation
    const canGoNext = useMemo(() => {
        switch (currentStep) {
            case 0: return !!targetColumn && !!problemType;
            case 1: return selectedModels.length > 0;
            case 2: return true; // Params are optional
            case 3: return trainingResults.length > 0;
            default: return false;
        }
    }, [currentStep, targetColumn, problemType, selectedModels, trainingResults]);

    const canGoPrev = currentStep > 0;

    // Set target column and detect problem type via API
    const setTargetColumn = useCallback(async (column: string) => {
        setTargetColumnState(column);
        setError(null);

        try {
            // Use API to detect problem type
            const result = await api.detectProblemType(column);
            setProblemType(result.problem_type);
        } catch (err) {
            // Fallback to local detection
            const col = columns.find(c => c.name === column);
            if (col) {
                if (col.type === 'categorical' || col.uniqueValues <= 10) {
                    setProblemType('classification');
                } else {
                    setProblemType('regression');
                }
            }
        }

        // Reset selections when target changes
        setSelectedModels([]);
        setModelParams({});
        setTrainingResults([]);
    }, [columns]);

    // Toggle model selection
    const toggleModelSelection = useCallback((modelId: string) => {
        setSelectedModels(prev => {
            if (prev.includes(modelId)) {
                return prev.filter(id => id !== modelId);
            }
            return [...prev, modelId];
        });
    }, []);

    // Update model parameters
    const updateModelParams = useCallback((modelId: string, params: Record<string, unknown>) => {
        setModelParams(prev => ({
            ...prev,
            [modelId]: { ...prev[modelId], ...params },
        }));
    }, []);

    // Train models via API
    const trainModels = useCallback(async () => {
        if (selectedModels.length === 0 || !targetColumn) return;

        try {
            setIsTraining(true);
            setError(null);

            // Call API to train models
            const response = await api.trainModels(
                targetColumn,
                selectedModels,
                0.2,
                modelParams
            );

            // Transform API response to TrainingResult format
            const results: TrainingResult[] = response.results.map(result => {
                const metrics: ModelMetrics = response.problem_type === 'classification'
                    ? {
                        accuracy: result.metrics.accuracy || 0,
                        precision: result.metrics.precision || 0,
                        recall: result.metrics.recall || 0,
                        f1Score: result.metrics.f1_score || 0,
                        auc: result.metrics.auc,
                    }
                    : {
                        mse: result.metrics.mse || 0,
                        rmse: result.metrics.rmse || 0,
                        mae: result.metrics.mae || 0,
                        r2: result.metrics.r2 || 0,
                    };

                const featureImportance: FeatureImportance[] = result.feature_importance.map(fi => ({
                    feature: fi.feature,
                    importance: fi.importance,
                }));

                return {
                    modelId: result.model_id,
                    modelName: result.model_name,
                    metrics,
                    featureImportance,
                    confusionMatrix: result.confusion_matrix || undefined,
                    trainingTime: result.training_time,
                    timestamp: new Date(),
                };
            });

            setTrainingResults(results);
            nextStep(); // Go to results step
        } catch (err) {
            console.error('Training error:', err);
            setError(err instanceof Error ? err.message : 'Eğitim sırasında hata oluştu');
        } finally {
            setIsTraining(false);
        }
    }, [selectedModels, targetColumn, modelParams, nextStep]);

    // Reset all
    const resetAll = useCallback(() => {
        setCurrentStep(0);
        setTargetColumnState(null);
        setProblemType(null);
        setSelectedModels([]);
        setModelParams({});
        setTrainingResults([]);
        setError(null);
    }, []);

    return {
        currentStep,
        targetColumn,
        problemType,
        selectedModels,
        modelParams,
        trainingResults,
        isTraining,
        error,
        columns,
        availableModels,
        goToStep,
        nextStep,
        prevStep,
        canGoNext,
        canGoPrev,
        loadColumns,
        setTargetColumn,
        toggleModelSelection,
        updateModelParams,
        trainModels,
        resetAll,
    };
}

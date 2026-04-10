'use client';

import { useState, useCallback, useMemo } from 'react';
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
    currentStep: number;
    targetColumn: string | null;
    problemType: ProblemType | null;
    selectedModels: string[];
    modelParams: Record<string, Record<string, unknown>>;
    trainingResults: TrainingResult[];
    isLoading: boolean;
    isTraining: boolean;
    error: string | null;
    columns: ColumnInfo[];
    availableModels: ModelInfo[];
    goToStep: (step: number) => void;
    nextStep: () => void;
    prevStep: () => void;
    canGoNext: boolean;
    canGoPrev: boolean;
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
    const [isLoading, setIsLoading] = useState(false);
    const [isTraining, setIsTraining] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [columns, setColumns] = useState<ColumnInfo[]>([]);

    const loadColumns = useCallback(async () => {
        try {
            setIsLoading(true);
            const columnTypes = await api.getColumnTypes();

            const cols: ColumnInfo[] = columnTypes.columns.map((col) => ({
                name: col.name,
                type: col.type === 'numeric' ? 'numeric' : 'categorical',
                uniqueValues: col.unique_count,
            }));

            setColumns(cols);
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setColumns([]);
                setError(null);
                return;
            }

            console.error('Load columns error:', err);
            setError(err instanceof Error ? err.message : 'Sutunlar yuklenirken hata olustu');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const availableModels = useMemo(() => {
        if (problemType === 'classification') return CLASSIFICATION_MODELS;
        if (problemType === 'regression') return REGRESSION_MODELS;
        return [];
    }, [problemType]);

    const goToStep = useCallback((step: number) => {
        if (step >= 0 && step <= 4) {
            setCurrentStep(step);
        }
    }, []);

    const nextStep = useCallback(() => {
        if (currentStep < 4) {
            setCurrentStep((prev) => prev + 1);
        }
    }, [currentStep]);

    const prevStep = useCallback(() => {
        if (currentStep > 0) {
            setCurrentStep((prev) => prev - 1);
        }
    }, [currentStep]);

    const canGoNext = useMemo(() => {
        switch (currentStep) {
            case 0:
                return !!targetColumn && !!problemType;
            case 1:
                return selectedModels.length > 0;
            case 2:
                return true;
            case 3:
                return trainingResults.length > 0;
            default:
                return false;
        }
    }, [currentStep, problemType, selectedModels, targetColumn, trainingResults]);

    const canGoPrev = currentStep > 0;

    const setTargetColumn = useCallback(
        async (column: string) => {
            setTargetColumnState(column);
            setError(null);

            try {
                const result = await api.detectProblemType(column);
                setProblemType(result.problem_type);
            } catch {
                const col = columns.find((item) => item.name === column);
                if (col) {
                    if (col.type === 'categorical' || col.uniqueValues <= 10) {
                        setProblemType('classification');
                    } else {
                        setProblemType('regression');
                    }
                }
            }

            setSelectedModels([]);
            setModelParams({});
            setTrainingResults([]);
        },
        [columns]
    );

    const toggleModelSelection = useCallback((modelId: string) => {
        setSelectedModels((prev) => {
            if (prev.includes(modelId)) {
                return prev.filter((id) => id !== modelId);
            }
            return [...prev, modelId];
        });
    }, []);

    const updateModelParams = useCallback((modelId: string, params: Record<string, unknown>) => {
        setModelParams((prev) => ({
            ...prev,
            [modelId]: { ...prev[modelId], ...params },
        }));
    }, []);

    const trainModels = useCallback(async () => {
        if (selectedModels.length === 0 || !targetColumn) return;

        try {
            setIsTraining(true);
            setError(null);

            const response = await api.trainModels(targetColumn, selectedModels, 0.2, modelParams);

            const results: TrainingResult[] = response.results.map((result) => {
                const metrics: ModelMetrics =
                    response.problem_type === 'classification'
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

                const featureImportance: FeatureImportance[] = result.feature_importance.map((fi) => ({
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
            nextStep();
        } catch (err) {
            console.error('Training error:', err);
            setError(err instanceof Error ? err.message : 'Egitim sirasinda hata olustu');
        } finally {
            setIsTraining(false);
        }
    }, [modelParams, nextStep, selectedModels, targetColumn]);

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
        isLoading,
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

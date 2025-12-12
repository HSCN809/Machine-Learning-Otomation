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

// Mock column info
const MOCK_COLUMNS = [
    { name: 'target', type: 'categorical' as const, uniqueValues: 2 },
    { name: 'age', type: 'numeric' as const, uniqueValues: 80 },
    { name: 'salary', type: 'numeric' as const, uniqueValues: 500 },
    { name: 'department', type: 'categorical' as const, uniqueValues: 8 },
];

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
    columns: typeof MOCK_COLUMNS;

    // Available models based on problem type
    availableModels: ModelInfo[];

    // Navigation
    goToStep: (step: number) => void;
    nextStep: () => void;
    prevStep: () => void;
    canGoNext: boolean;
    canGoPrev: boolean;

    // Actions
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

    const columns = MOCK_COLUMNS;

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

    // Set target column and detect problem type
    const setTargetColumn = useCallback((column: string) => {
        setTargetColumnState(column);

        // Auto-detect problem type based on column
        const col = columns.find(c => c.name === column);
        if (col) {
            if (col.type === 'categorical' || col.uniqueValues <= 10) {
                setProblemType('classification');
            } else {
                setProblemType('regression');
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

    // Train models (mock implementation)
    const trainModels = useCallback(async () => {
        if (selectedModels.length === 0) return;

        try {
            setIsTraining(true);
            setError(null);

            const results: TrainingResult[] = [];

            for (const modelId of selectedModels) {
                // Simulate training delay
                await new Promise(resolve => setTimeout(resolve, 800));

                const model = availableModels.find(m => m.id === modelId);
                if (!model) continue;

                // Generate mock metrics
                const metrics: ModelMetrics = problemType === 'classification'
                    ? {
                        accuracy: 0.75 + Math.random() * 0.2,
                        precision: 0.7 + Math.random() * 0.25,
                        recall: 0.7 + Math.random() * 0.25,
                        f1Score: 0.72 + Math.random() * 0.22,
                        auc: 0.8 + Math.random() * 0.15,
                    }
                    : {
                        mse: Math.random() * 100,
                        rmse: Math.random() * 10,
                        mae: Math.random() * 8,
                        r2: 0.6 + Math.random() * 0.35,
                    };

                // Generate mock feature importance
                const featureImportance: FeatureImportance[] = columns
                    .filter(c => c.name !== targetColumn)
                    .map(c => ({
                        feature: c.name,
                        importance: Math.random(),
                    }))
                    .sort((a, b) => b.importance - a.importance);

                // Generate mock confusion matrix for classification
                const confusionMatrix = problemType === 'classification'
                    ? [
                        [Math.floor(Math.random() * 100) + 50, Math.floor(Math.random() * 30)],
                        [Math.floor(Math.random() * 30), Math.floor(Math.random() * 100) + 50],
                    ]
                    : undefined;

                results.push({
                    modelId,
                    modelName: model.name,
                    metrics,
                    featureImportance,
                    confusionMatrix,
                    trainingTime: Math.random() * 5 + 0.5,
                    timestamp: new Date(),
                });
            }

            setTrainingResults(results);
            nextStep(); // Go to results step
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Eğitim sırasında hata oluştu');
        } finally {
            setIsTraining(false);
        }
    }, [selectedModels, availableModels, problemType, targetColumn, columns, nextStep]);

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
        setTargetColumn,
        toggleModelSelection,
        updateModelParams,
        trainModels,
        resetAll,
    };
}

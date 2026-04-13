'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
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
    completedSteps: number[];
    skippedSteps: number[];
    targetColumn: string | null;
    problemType: ProblemType | null;
    selectedModels: string[];
    modelParams: Record<string, Record<string, unknown>>;
    trainingResults: TrainingResult[];
    isLoading: boolean;
    isTraining: boolean;
    trainingStatus: 'idle' | 'queued' | 'running' | 'stopping' | 'completed' | 'failed' | 'stopped';
    currentTrainingModel: string | null;
    completedTrainingModels: number;
    totalTrainingModels: number;
    error: string | null;
    columns: ColumnInfo[];
    availableModels: ModelInfo[];
    goToStep: (step: number) => void;
    nextStep: () => void;
    skipStep: () => void;
    prevStep: () => void;
    canGoNext: boolean;
    canGoPrev: boolean;
    loadColumns: () => Promise<void>;
    setTargetColumn: (column: string) => void;
    setProblemType: (problemType: ProblemType) => void;
    toggleModelSelection: (modelId: string) => void;
    updateModelParams: (modelId: string, params: Record<string, unknown>) => void;
    trainModels: () => Promise<void>;
    stopTraining: () => Promise<void>;
    resetAll: () => void;
}

function getStaticModels(problemType: ProblemType | null): ModelInfo[] {
    if (problemType === 'classification') return CLASSIFICATION_MODELS;
    if (problemType === 'regression') return REGRESSION_MODELS;
    return [];
}

function mergeAvailableModels(
    problemType: ProblemType | null,
    apiModels?: Awaited<ReturnType<typeof api.getAvailableModels>>['models']
): ModelInfo[] {
    const catalog = getStaticModels(problemType);
    if (!apiModels || apiModels.length === 0) {
        return catalog;
    }

    const apiModelIds = new Set(apiModels.map((model) => model.id));
    return catalog.filter((model) => apiModelIds.has(model.id));
}

function mapTrainingResults(
    problemType: ProblemType | null,
    results: api.TrainingResult[]
): TrainingResult[] {
    return results.map((result) => {
        const metrics: ModelMetrics =
            problemType === 'classification'
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
            confusionLabels: result.confusion_labels || undefined,
            trainingTime: result.training_time,
            timestamp: new Date(),
        };
    });
}

export function useModelSelection(): UseModelSelectionReturn {
    const [currentStep, setCurrentStep] = useState(0);
    const [completedSteps, setCompletedSteps] = useState<number[]>([]);
    const [skippedSteps, setSkippedSteps] = useState<number[]>([]);
    const [targetColumn, setTargetColumnState] = useState<string | null>(null);
    const [problemType, setProblemTypeState] = useState<ProblemType | null>(null);
    const [selectedModels, setSelectedModels] = useState<string[]>([]);
    const [modelParams, setModelParams] = useState<Record<string, Record<string, unknown>>>({});
    const [trainingResults, setTrainingResults] = useState<TrainingResult[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [isTraining, setIsTraining] = useState(false);
    const [trainingStatus, setTrainingStatus] = useState<'idle' | 'queued' | 'running' | 'stopping' | 'completed' | 'failed' | 'stopped'>('idle');
    const [currentTrainingModel, setCurrentTrainingModel] = useState<string | null>(null);
    const [completedTrainingModels, setCompletedTrainingModels] = useState(0);
    const [totalTrainingModels, setTotalTrainingModels] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [columns, setColumns] = useState<ColumnInfo[]>([]);
    const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
    const [trainingJobId, setTrainingJobId] = useState<string | null>(null);
    const eventSourceRef = useRef<EventSource | null>(null);
    const trainingStatusRef = useRef<'idle' | 'queued' | 'running' | 'stopping' | 'completed' | 'failed' | 'stopped'>('idle');

    useEffect(() => {
        trainingStatusRef.current = trainingStatus;
    }, [trainingStatus]);

    const closeTrainingStream = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
    }, []);

    const loadAvailableModels = useCallback(async (nextProblemType: ProblemType | null) => {
        if (!nextProblemType) {
            setAvailableModels([]);
            return;
        }

        try {
            const response = await api.getAvailableModels(nextProblemType);
            const merged = mergeAvailableModels(nextProblemType, response.models);
            setAvailableModels(merged.length > 0 ? merged : getStaticModels(nextProblemType));
        } catch (err) {
            console.error('Load available models error:', err);
            setAvailableModels(getStaticModels(nextProblemType));
        }
    }, []);

    const applyTrainingSnapshot = useCallback((snapshot: api.TrainingJobSnapshot) => {
        const nextProblemType =
            snapshot.problem_type === 'classification' || snapshot.problem_type === 'regression'
                ? snapshot.problem_type
                : null;

        setTrainingJobId(snapshot.job_id);
        setTrainingStatus(snapshot.status);
        setIsTraining(snapshot.status === 'queued' || snapshot.status === 'running' || snapshot.status === 'stopping');
        setCurrentTrainingModel(snapshot.current_model);
        setCompletedTrainingModels(snapshot.completed_models);
        setTotalTrainingModels(snapshot.total_models);
        setTargetColumnState(snapshot.target_column);
        if (nextProblemType) {
            setProblemTypeState(nextProblemType);
            void loadAvailableModels(nextProblemType);
            setTrainingResults(mapTrainingResults(nextProblemType, snapshot.results));
        } else {
            setTrainingResults([]);
        }

        if (snapshot.status === 'completed') {
            setError(null);
            setCurrentStep(4);
            setCompletedSteps((prev) => (prev.includes(3) ? prev : [...prev, 3]));
            closeTrainingStream();
            return;
        }

        if (snapshot.status === 'failed') {
            setError(snapshot.error ?? 'Egitim sirasinda hata olustu');
            setCurrentStep(3);
            closeTrainingStream();
            return;
        }

        if (snapshot.status === 'stopped') {
            setError('Egitim durduruldu');
            setCurrentStep(3);
            closeTrainingStream();
            return;
        }

        setError(null);
        setCurrentStep(3);
    }, [closeTrainingStream, loadAvailableModels]);

    const connectToTrainingStream = useCallback((jobId: string) => {
        closeTrainingStream();

        const stream = new EventSource(api.getModelTrainingStreamUrl(jobId));
        eventSourceRef.current = stream;

        stream.onmessage = (event) => {
            try {
                const snapshot = JSON.parse(event.data) as api.TrainingJobSnapshot;
                applyTrainingSnapshot(snapshot);
            } catch (err) {
                console.error('Training stream parse error:', err);
            }
        };

        stream.onerror = () => {
            const terminalStatuses = new Set(['completed', 'failed', 'stopped']);
            if (!terminalStatuses.has(trainingStatusRef.current)) {
                setError((prev) => prev ?? 'Egitim akisi baglantisi koptu');
            }
            closeTrainingStream();
        };
    }, [applyTrainingSnapshot, closeTrainingStream]);

    const loadColumns = useCallback(async () => {
        try {
            setIsLoading(true);
            const [columnTypes, trainingState] = await Promise.all([
                api.getColumnTypes(),
                api.getTrainingResults(),
            ]);

            const cols: ColumnInfo[] = columnTypes.columns.map((col) => ({
                name: col.name,
                type: col.type === 'numeric' ? 'numeric' : 'categorical',
                uniqueValues: col.unique_count,
            }));

            setColumns(cols);

            const hydratedProblemType =
                trainingState.problem_type === 'classification' || trainingState.problem_type === 'regression'
                    ? trainingState.problem_type
                    : null;
            setProblemTypeState(hydratedProblemType);
            setTargetColumnState(trainingState.target_column ?? null);
            await loadAvailableModels(hydratedProblemType);

            if (trainingState.job) {
                applyTrainingSnapshot(trainingState.job);
                if (trainingState.job.status === 'queued' || trainingState.job.status === 'running' || trainingState.job.status === 'stopping') {
                    connectToTrainingStream(trainingState.job.job_id);
                }
            } else if (hydratedProblemType && trainingState.results.length > 0) {
                const comparisonState = await api.getModelComparison().catch(() => null);
                const hydratedResults =
                    comparisonState?.comparison && comparisonState.comparison.length > 0
                        ? comparisonState.comparison
                        : trainingState.results;

                setTrainingStatus('completed');
                setTrainingResults(mapTrainingResults(hydratedProblemType, hydratedResults));
                setCompletedTrainingModels(hydratedResults.length);
                setTotalTrainingModels(hydratedResults.length);
                setCurrentStep(4);
            }
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setColumns([]);
                setAvailableModels([]);
                setError(null);
                return;
            }

            console.error('Load columns error:', err);
            setError(err instanceof Error ? err.message : 'Sutunlar yuklenirken hata olustu');
        } finally {
            setIsLoading(false);
        }
    }, [applyTrainingSnapshot, connectToTrainingStream, loadAvailableModels]);

    const goToStep = useCallback((step: number) => {
        if (step >= 0 && step <= 4) {
            setCurrentStep(step);
        }
    }, []);

    const nextStep = useCallback(() => {
        if (currentStep < 4) {
            setSkippedSteps((prev) => prev.filter((step) => step !== currentStep));
            if (!completedSteps.includes(currentStep)) {
                setCompletedSteps((prev) => [...prev, currentStep]);
            }
            setCurrentStep((prev) => prev + 1);
        }
    }, [completedSteps, currentStep]);

    const skipStep = useCallback(() => {
        if (currentStep < 4) {
            setCompletedSteps((prev) => prev.filter((step) => step !== currentStep));
            if (!skippedSteps.includes(currentStep)) {
                setSkippedSteps((prev) => [...prev, currentStep]);
            }
            setCurrentStep((prev) => prev + 1);
        }
    }, [currentStep, skippedSteps]);

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
        (column: string) => {
            setTargetColumnState(column);
            setError(null);

            closeTrainingStream();
            setTrainingJobId(null);
            setTrainingStatus('idle');
            setIsTraining(false);
            setCurrentTrainingModel(null);
            setCompletedTrainingModels(0);
            setTotalTrainingModels(0);
            setProblemTypeState(null);
            setAvailableModels([]);
            setSelectedModels([]);
            setModelParams({});
            setTrainingResults([]);
        },
        [closeTrainingStream]
    );

    const setProblemType = useCallback(
        (nextProblemType: ProblemType) => {
            setProblemTypeState(nextProblemType);
            setError(null);
            void loadAvailableModels(nextProblemType);
            setSelectedModels([]);
            setModelParams({});
            setTrainingResults([]);
            setTrainingJobId(null);
            setTrainingStatus('idle');
            setIsTraining(false);
            setCurrentTrainingModel(null);
            setCompletedTrainingModels(0);
            setTotalTrainingModels(0);
            closeTrainingStream();
        },
        [closeTrainingStream, loadAvailableModels]
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
        if (selectedModels.length === 0 || !targetColumn || !problemType) return;

        try {
            setIsTraining(true);
            setError(null);
            setTrainingStatus('queued');
            setCurrentTrainingModel(null);
            setCompletedTrainingModels(0);
            setTotalTrainingModels(selectedModels.length);
            setTrainingResults([]);
            setCurrentStep(3);

            const response = await api.startModelTraining(targetColumn, problemType, selectedModels, 0.2, modelParams);
            setTrainingJobId(response.job_id);
            connectToTrainingStream(response.job_id);
        } catch (err) {
            console.error('Training error:', err);
            setError(err instanceof Error ? err.message : 'Egitim sirasinda hata olustu');
            setIsTraining(false);
            setTrainingStatus('failed');
        }
    }, [connectToTrainingStream, modelParams, problemType, selectedModels, targetColumn]);

    const stopTraining = useCallback(async () => {
        if (!trainingJobId) {
            return;
        }

        try {
            setError(null);
            await api.stopModelTraining(trainingJobId);
            setTrainingStatus('stopping');
        } catch (err) {
            console.error('Stop training error:', err);
            setError(err instanceof Error ? err.message : 'Egitim durdurulamadi');
        }
    }, [trainingJobId]);

    const resetAll = useCallback(() => {
        closeTrainingStream();
        setCurrentStep(0);
        setCompletedSteps([]);
        setSkippedSteps([]);
        setTargetColumnState(null);
        setProblemTypeState(null);
        setAvailableModels([]);
        setSelectedModels([]);
        setModelParams({});
        setTrainingResults([]);
        setTrainingJobId(null);
        setTrainingStatus('idle');
        setIsTraining(false);
        setCurrentTrainingModel(null);
        setCompletedTrainingModels(0);
        setTotalTrainingModels(0);
        setError(null);
    }, [closeTrainingStream]);

    useEffect(() => {
        return () => {
            closeTrainingStream();
        };
    }, [closeTrainingStream]);

    return {
        currentStep,
        completedSteps,
        skippedSteps,
        targetColumn,
        problemType,
        selectedModels,
        modelParams,
        trainingResults,
        isLoading,
        isTraining,
        trainingStatus,
        currentTrainingModel,
        completedTrainingModels,
        totalTrainingModels,
        error,
        columns,
        availableModels,
        goToStep,
        nextStep,
        skipStep,
        prevStep,
        canGoNext,
        canGoPrev,
        loadColumns,
        setTargetColumn,
        setProblemType,
        toggleModelSelection,
        updateModelParams,
        trainModels,
        stopTraining,
        resetAll,
    };
}

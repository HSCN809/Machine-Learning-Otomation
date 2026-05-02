'use client';

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import {
    ProblemType,
    ModelInfo,
    TrainingResult,
    SavedModelSummary,
    ModelMetrics,
    FeatureImportance,
    CLASSIFICATION_MODELS,
    REGRESSION_MODELS,
} from '@/types/model-selection';
import * as api from '@/lib/api';
import { logger } from '@/lib/logger';
import { notify } from '@/lib/notify';

interface ColumnInfo {
    name: string;
    type: 'numeric' | 'categorical';
    uniqueValues: number;
}

function resolveModelSelectionColumnType(column: Awaited<ReturnType<typeof api.getColumnTypes>>['columns'][number]): ColumnInfo['type'] {
    return column.type === 'numeric' ? 'numeric' : 'categorical';
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
    columns: ColumnInfo[];
    availableModels: ModelInfo[];
    savedModels: SavedModelSummary[];
    isSavedModelsLoading: boolean;
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
    selectSavedModel: (savedModelId: string) => Promise<void>;
    renameSavedModel: (savedModelId: string, modelName: string) => Promise<void>;
    deleteSavedModel: (savedModelId: string) => Promise<void>;
    startNewTraining: () => void;
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

function mapSavedModelSummary(result: api.SavedModelSummaryResponse): SavedModelSummary {
    const metrics: ModelMetrics =
        result.problem_type === 'classification'
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

    return {
        id: result.id,
        modelId: result.model_id,
        modelName: result.model_name,
        targetColumn: result.target_column,
        problemType: result.problem_type,
        metrics,
        trainingTime: result.training_time,
        createdAt: result.created_at,
    };
}

export function useModelSelection(): UseModelSelectionReturn {
    const queryClient = useQueryClient();
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
    const [columns, setColumns] = useState<ColumnInfo[]>([]);
    const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);
    const [savedModels, setSavedModels] = useState<SavedModelSummary[]>([]);
    const [isSavedModelsLoading, setIsSavedModelsLoading] = useState(false);
    const [trainingJobId, setTrainingJobId] = useState<string | null>(null);
    const eventSourceRef = useRef<EventSource | null>(null);
    const timelineRefreshTimeoutRef = useRef<number | null>(null);
    const workflowPersistTimeoutRef = useRef<number | null>(null);
    const workflowHydratedRef = useRef(false);
    const trainingStatusRef = useRef<'idle' | 'queued' | 'running' | 'stopping' | 'completed' | 'failed' | 'stopped'>('idle');
    const loggedStepPayloadsRef = useRef<Record<string, string>>({});

    useEffect(() => {
        trainingStatusRef.current = trainingStatus;
    }, [trainingStatus]);

    const closeTrainingStream = useCallback(() => {
        if (eventSourceRef.current) {
            eventSourceRef.current.close();
            eventSourceRef.current = null;
        }
    }, []);

    const refreshTimeline = useCallback(async () => {
        await queryClient.invalidateQueries({
            queryKey: ['dataset-timeline'],
        });
    }, [queryClient]);

    const scheduleTimelineRefresh = useCallback((delayMs: number = 0) => {
        if (timelineRefreshTimeoutRef.current !== null) {
            window.clearTimeout(timelineRefreshTimeoutRef.current);
        }

        timelineRefreshTimeoutRef.current = window.setTimeout(() => {
            timelineRefreshTimeoutRef.current = null;
            void refreshTimeline();
        }, delayMs);
    }, [refreshTimeline]);

    const notifyDatasetMutation = useCallback(() => {
        const currentSessionId = api.getStoredSessionId();
        if (currentSessionId) {
            api.setStoredSessionId(currentSessionId);
        }
    }, []);

    const loadSavedModels = useCallback(async () => {
        try {
            setIsSavedModelsLoading(true);
            const response = await api.getSavedModels();
            setSavedModels(response.models.map(mapSavedModelSummary));
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setSavedModels([]);
                return;
            }

            logger.error('Saved models load failed', err);
            notify.error(err, 'Kayitli modeller yuklenemedi');
        } finally {
            setIsSavedModelsLoading(false);
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
            logger.error('Available models load failed', err, { problemType: nextProblemType });
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
            setCurrentStep(4);
            setCompletedSteps((prev) => (prev.includes(3) ? prev : [...prev, 3]));
            closeTrainingStream();
            notifyDatasetMutation();
            scheduleTimelineRefresh(150);
            void loadSavedModels();
            notify.success('Model eğitimi tamamlandı');
            return;
        }

        if (snapshot.status === 'failed') {
            setCurrentStep(3);
            closeTrainingStream();
            notifyDatasetMutation();
            scheduleTimelineRefresh(150);
            notify.error(snapshot.error ?? new Error('Eğitim sırasında hata oluştu'), 'Eğitim sırasında hata oluştu');
            return;
        }

        if (snapshot.status === 'stopped') {
            setCurrentStep(3);
            closeTrainingStream();
            notifyDatasetMutation();
            scheduleTimelineRefresh(150);
            notify.info('Eğitim durduruldu');
            return;
        }

        setCurrentStep(3);
    }, [closeTrainingStream, loadAvailableModels, loadSavedModels, notifyDatasetMutation, scheduleTimelineRefresh]);

    const connectToTrainingStream = useCallback((jobId: string) => {
        closeTrainingStream();

        const stream = new EventSource(api.getModelTrainingStreamUrl(jobId));
        eventSourceRef.current = stream;

        stream.onmessage = (event) => {
            try {
                const snapshot = JSON.parse(event.data) as api.TrainingJobSnapshot;
                applyTrainingSnapshot(snapshot);
            } catch (err) {
                logger.error('Training stream parse failed', err);
            }
        };

        stream.onerror = () => {
            const terminalStatuses = new Set(['completed', 'failed', 'stopped']);
            if (!terminalStatuses.has(trainingStatusRef.current)) {
                const message = 'Eğitim akışı bağlantısı koptu';
                logger.warn('Training stream connection lost', {
                    jobId,
                    status: trainingStatusRef.current,
                });
                notify.error(new Error(message), message);
            }
            closeTrainingStream();
        };
    }, [applyTrainingSnapshot, closeTrainingStream]);

    const loadColumns = useCallback(async () => {
        try {
            setIsLoading(true);
            const [columnTypes, trainingState, savedModelState, workflowState] = await Promise.all([
                api.getColumnTypes(),
                api.getTrainingResults(),
                api.getSavedModels().catch(() => ({ models: [] })),
                api.getModelWorkflowState().catch(() => null),
            ]);

            const cols: ColumnInfo[] = columnTypes.columns.map((col) => ({
                name: col.name,
                type: resolveModelSelectionColumnType(col),
                uniqueValues: col.unique_count,
            }));

            setColumns(cols);
            setSavedModels(savedModelState.models.map(mapSavedModelSummary));
            const initialTargetColumn = trainingState.target_column ?? cols[0]?.name ?? null;

            const hydratedProblemType =
                trainingState.problem_type === 'classification' || trainingState.problem_type === 'regression'
                    ? trainingState.problem_type
                    : null;
            const workflowProblemType =
                workflowState?.problem_type === 'classification' || workflowState?.problem_type === 'regression'
                    ? workflowState.problem_type
                    : null;
            const nextTargetColumn = workflowState?.target_column ?? initialTargetColumn;
            const nextProblemType = workflowProblemType ?? hydratedProblemType;

            setTargetColumnState(nextTargetColumn);
            setProblemTypeState(nextProblemType);
            setCurrentStep(workflowState?.current_step ?? 0);
            setCompletedSteps(workflowState?.completed_steps ?? []);
            setSkippedSteps(workflowState?.skipped_steps ?? []);
            setSelectedModels(workflowState?.selected_models ?? []);
            setModelParams(workflowState?.model_params ?? {});
            await loadAvailableModels(nextProblemType);
            workflowHydratedRef.current = true;

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
                setCompletedSteps([0, 1, 2, 3]);
                setSkippedSteps([]);
            }
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setColumns([]);
                setAvailableModels([]);
                setSavedModels([]);
                workflowHydratedRef.current = false;
                return;
            }

            logger.error('Model selection columns load failed', err);
            notify.error(err, 'Sütunlar yüklenirken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [applyTrainingSnapshot, connectToTrainingStream, loadAvailableModels]);

    const goToStep = useCallback((step: number) => {
        if (step >= 0 && step <= 4) {
            setCurrentStep(step);
        }
    }, []);

    const logStepEvent = useCallback((key: string, request: {
        category: string;
        action: string;
        title: string;
        description: string;
        metadata: Record<string, unknown>;
        payload: Record<string, unknown>;
        step?: string;
    }) => {
        if (request.category === 'model') {
            return;
        }

        const payloadSignature = JSON.stringify(request.payload);
        if (loggedStepPayloadsRef.current[key] === payloadSignature) {
            return;
        }

        loggedStepPayloadsRef.current[key] = payloadSignature;
        void api.appendTimelineEvent({
            category: request.category,
            action: request.action,
            title: request.title,
            description: request.description,
            metadata: request.metadata,
            payload: request.payload,
            step: request.step,
        })
            .then(() => {
                notifyDatasetMutation();
                return refreshTimeline();
            })
            .catch((err) => {
                logger.error('Model selection timeline event append failed', err, { key });
            });
    }, [notifyDatasetMutation, refreshTimeline]);

    const nextStep = useCallback(() => {
        if (currentStep === 0 && targetColumn && problemType) {
            logStepEvent('step-0', {
                category: 'model',
                action: 'selection_target_confirmed',
                title: 'Model hedefi secildi',
                description: 'Target kolon ve problem tipi secimi tamamlandi.',
                metadata: {
                    targetColumn,
                    problemType,
                },
                payload: {
                    targetColumn,
                    problemType,
                },
                step: 'target_selection',
            });
        }

        if (currentStep === 1 && selectedModels.length > 0) {
            logStepEvent('step-1', {
                category: 'model',
                action: 'selection_models_confirmed',
                title: 'Modeller secildi',
                description: `${selectedModels.length} model egitim icin secildi.`,
                metadata: {
                    models: selectedModels,
                },
                payload: {
                    models: selectedModels,
                },
                step: 'model_selection',
            });
        }

        if (currentStep === 2 && selectedModels.length > 0) {
            logStepEvent('step-2', {
                category: 'model',
                action: 'selection_params_confirmed',
                title: 'Hiperparametreler kaydedildi',
                description: 'Model hiperparametre secimleri egitim oncesi kaydedildi.',
                metadata: {
                    selectedModels,
                    modelParams,
                },
                payload: {
                    selectedModels,
                    modelParams,
                },
                step: 'hyperparameters',
            });
        }

        if (currentStep < 4) {
            setSkippedSteps((prev) => prev.filter((step) => step !== currentStep));
            if (!completedSteps.includes(currentStep)) {
                setCompletedSteps((prev) => [...prev, currentStep]);
            }
            setCurrentStep((prev) => prev + 1);
        }
    }, [completedSteps, currentStep, logStepEvent, modelParams, problemType, selectedModels, targetColumn]);

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

    useEffect(() => {
        if (!workflowHydratedRef.current) {
            return;
        }

        if (workflowPersistTimeoutRef.current !== null) {
            window.clearTimeout(workflowPersistTimeoutRef.current);
        }

        workflowPersistTimeoutRef.current = window.setTimeout(() => {
            workflowPersistTimeoutRef.current = null;
            void api.updateModelWorkflowState({
                current_step: currentStep,
                completed_steps: completedSteps,
                skipped_steps: skippedSteps,
                target_column: targetColumn,
                problem_type: problemType,
                selected_models: selectedModels,
                model_params: modelParams,
            }).catch((err) => {
                logger.error('Model workflow state persist failed', err);
            });
        }, 150);

        return () => {
            if (workflowPersistTimeoutRef.current !== null) {
                window.clearTimeout(workflowPersistTimeoutRef.current);
                workflowPersistTimeoutRef.current = null;
            }
        };
    }, [completedSteps, currentStep, modelParams, problemType, selectedModels, skippedSteps, targetColumn]);

    const setTargetColumn = useCallback(
        (column: string) => {
            setTargetColumnState(column);
            loggedStepPayloadsRef.current = {};

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
            loggedStepPayloadsRef.current = {};
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

    const selectSavedModel = useCallback(async (savedModelId: string) => {
        const selectedSavedModel = savedModels.find((model) => model.id === savedModelId);
        if (!selectedSavedModel) {
            return;
        }

        const relatedModels = savedModels
            .filter(
                (model) =>
                    model.targetColumn === selectedSavedModel.targetColumn &&
                    model.problemType === selectedSavedModel.problemType
            )
            .sort((left, right) => {
                if (left.id === selectedSavedModel.id) return -1;
                if (right.id === selectedSavedModel.id) return 1;

                const leftDate = left.createdAt ? new Date(left.createdAt).getTime() : 0;
                const rightDate = right.createdAt ? new Date(right.createdAt).getTime() : 0;
                return rightDate - leftDate;
            });

        closeTrainingStream();
        loggedStepPayloadsRef.current = {};
        setTargetColumnState(selectedSavedModel.targetColumn);
        setProblemTypeState(selectedSavedModel.problemType);
        await loadAvailableModels(selectedSavedModel.problemType);
        setSelectedModels(relatedModels.map((model) => model.modelId));
        setModelParams({});
        setTrainingResults(
            relatedModels.map((model) => ({
                modelId: model.modelId,
                modelName: model.modelName,
                metrics: model.metrics,
                featureImportance: [],
                trainingTime: model.trainingTime ?? 0,
                timestamp: model.createdAt ? new Date(model.createdAt) : new Date(),
            }))
        );
        setTrainingJobId(null);
        setTrainingStatus('completed');
        setIsTraining(false);
        setCurrentTrainingModel(null);
        setCompletedTrainingModels(relatedModels.length);
        setTotalTrainingModels(relatedModels.length);
        setCompletedSteps([0, 1, 2, 3]);
        setSkippedSteps([]);
        setCurrentStep(4);
    }, [closeTrainingStream, loadAvailableModels, savedModels]);

    const renameSavedModel = useCallback(async (savedModelId: string, modelName: string) => {
        const nextModelName = modelName.trim();
        if (!nextModelName) {
            throw new Error('Model adı boş bırakılamaz');
        }

        try {
            await api.renameSavedModel(savedModelId, nextModelName);
            await loadSavedModels();
            notify.success('Model adı güncellendi');
        } catch (err) {
            logger.error('Saved model rename failed', err, { savedModelId });
            notify.error(err, 'Model adı güncellenemedi');
            throw err;
        }
    }, [loadSavedModels]);

    const deleteSavedModel = useCallback(async (savedModelId: string) => {
        try {
            await api.deleteSavedModel(savedModelId);
            await loadSavedModels();
            notify.success('Model silindi');
        } catch (err) {
            logger.error('Saved model delete failed', err, { savedModelId });
            notify.error(err, 'Model silinemedi');
            throw err;
        }
    }, [loadSavedModels]);

    const startNewTraining = useCallback(() => {
        closeTrainingStream();
        loggedStepPayloadsRef.current = {};
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
    }, [closeTrainingStream]);

    const trainModels = useCallback(async () => {
        if (selectedModels.length === 0 || !targetColumn || !problemType) return;

        try {
            setIsTraining(true);
            setTrainingStatus('queued');
            setCurrentTrainingModel(null);
            setCompletedTrainingModels(0);
            setTotalTrainingModels(selectedModels.length);
            setTrainingResults([]);
            setCurrentStep(3);

            const response = await api.startModelTraining(targetColumn, problemType, selectedModels, 0.2, modelParams);
            setTrainingJobId(response.job_id);
            connectToTrainingStream(response.job_id);
            notifyDatasetMutation();
            await refreshTimeline();
            notify.info('Model eğitimi başlatıldı');
        } catch (err) {
            logger.error('Model training failed to start', err);
            setIsTraining(false);
            setTrainingStatus('failed');
            notify.error(err, 'Eğitim sırasında hata oluştu');
        }
    }, [connectToTrainingStream, modelParams, notifyDatasetMutation, problemType, refreshTimeline, selectedModels, targetColumn]);

    const stopTraining = useCallback(async () => {
        if (!trainingJobId) {
            return;
        }

        try {
            await api.stopModelTraining(trainingJobId);
            setTrainingStatus('stopping');
            notify.info('Eğitim durduruluyor');
        } catch (err) {
            logger.error('Model training stop failed', err, { trainingJobId });
            notify.error(err, 'Eğitim durdurulamadı');
        }
    }, [trainingJobId]);

    const resetAll = useCallback(() => {
        closeTrainingStream();
        loggedStepPayloadsRef.current = {};
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
    }, [closeTrainingStream]);

    useEffect(() => {
        return () => {
            if (workflowPersistTimeoutRef.current !== null) {
                window.clearTimeout(workflowPersistTimeoutRef.current);
            }
            if (timelineRefreshTimeoutRef.current !== null) {
                window.clearTimeout(timelineRefreshTimeoutRef.current);
            }
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
        columns,
        availableModels,
        savedModels,
        isSavedModelsLoading,
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
        selectSavedModel,
        renameSavedModel,
        deleteSavedModel,
        startNewTraining,
        trainModels,
        stopTraining,
        resetAll,
    };
}

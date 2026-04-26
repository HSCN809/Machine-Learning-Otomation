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
    DropColumnConfig,
} from '@/types/preprocessing';
import * as api from '@/lib/api';
import { logger } from '@/lib/logger';
import { getErrorMessage, notify } from '@/lib/notify';

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

function mapHistoryEntry(
    entry: Awaited<ReturnType<typeof api.getTimeline>>['events'][number],
    index: number
): ProcessingHistory | null {
    const payload = entry.payload;
    const stepKey = typeof payload.step === 'string' ? payload.step : entry.step ?? undefined;
    const method = typeof payload.action === 'string' ? payload.action : entry.action ?? undefined;

    if (!stepKey || !method) {
        return null;
    }

    const columns = Array.isArray(payload.columns)
        ? payload.columns.filter((value): value is string => typeof value === 'string')
        : Array.isArray(payload.source_columns)
            ? payload.source_columns.filter((value): value is string => typeof value === 'string')
            : [];
    const newColumns = Array.isArray(payload.new_columns)
        ? payload.new_columns.filter((value): value is string => typeof value === 'string')
        : [];
    const params =
        payload.params && typeof payload.params === 'object'
            ? payload.params as Record<string, unknown>
            : undefined;
    const affectedRows = typeof payload.affected_rows === 'number' ? payload.affected_rows : undefined;

    return {
        id: entry.id || `${stepKey}-${index}`,
        historyIndex: index,
        stepKey,
        action: method === 'drop_columns' ? 'drop_columns' : HISTORY_ACTION_BY_STEP[stepKey] || method,
        columns,
        newColumns,
        method,
        params,
        timestamp: entry.createdAt,
        affectedRows,
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

            const [columnTypes, timelineResponse] = await Promise.all([
                api.getColumnTypes(),
                api.getTimeline(),
            ]);

            setColumns(mapColumns(columnTypes.columns));
            const nextHistory = timelineResponse.events
                .filter((event) => event.category === 'preprocessing')
                .map((entry, index) => mapHistoryEntry(entry, index))
                .filter((entry): entry is ProcessingHistory => entry !== null);
            setHistory(nextHistory);
            return true;
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setColumns([]);
                setHistory([]);
                setError(null);
                return false;
            }
            logger.error('Preprocessing data load failed', err);
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
    loadInitialData: () => Promise<unknown>;
    loadColumns: () => Promise<unknown>;
    loadHistory: () => Promise<unknown>;
    applyMissingValues: (config: MissingValueConfig) => Promise<void>;
    applyOutliers: (config: OutlierConfig) => Promise<void>;
applyEncoding: (config: EncodingConfig) => Promise<void>;
    applyScaling: (config: ScalingConfig) => Promise<void>;
    applyFeatureEngineering: (config: FeatureConfig) => Promise<void>;
    dropColumns: (config: DropColumnConfig) => Promise<void>;
    undoLastAction: () => Promise<void>;
    undoToHistoryItem: (historyIndex: number) => Promise<void>;
    resetAll: () => Promise<void>;

    // Helpers
    numericColumns: ColumnInfo[];
    scalingColumns: ColumnInfo[];
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
    const loadColumns = useCallback(async (): Promise<unknown> => {
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
            return true;
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setColumns([]);
                setError(null);
                return false;
            }
            logger.error('Preprocessing columns load failed', err);
            setError(getErrorMessage(err, 'Sütunlar yüklenirken hata oluştu'));
        } finally {
            setIsLoading(false);
        }
    }, []);

    const loadHistory = useCallback(async (): Promise<unknown> => {
        try {
            setIsLoading(true);
            const timelineResponse = await api.getTimeline();
            const nextHistory = timelineResponse.events
                .filter((event) => event.category === 'preprocessing')
                .map((entry, index) => mapHistoryEntry(entry, index))
                .filter((entry): entry is ProcessingHistory => entry !== null);
            setHistory(nextHistory);
            return true;
        } catch (err) {
            if (api.isSessionRequiredError(err)) {
                setHistory([]);
                setError(null);
                return false;
            }
            logger.error('Preprocessing history load failed', err);
            setError(getErrorMessage(err, 'İşlem geçmişi yüklenirken hata oluştu'));
        } finally {
            setIsLoading(false);
        }
    }, []);

    const loadInitialData = useCallback(async (): Promise<unknown> => {
        try {
            setIsLoading(true);
            setError(null);

            const [columnTypes, timelineResponse] = await Promise.all([
                api.getColumnTypes(),
                api.getTimeline(),
            ]);

            setColumns(mapColumns(columnTypes.columns));
            const nextHistory = timelineResponse.events
                .filter((event) => event.category === 'preprocessing')
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
            logger.error('Preprocessing data load failed', err);
            setError(getErrorMessage(err, 'Ön işleme verileri yüklenirken hata oluştu'));
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
        const [columnTypes, timelineResponse] = await Promise.all([
            api.getColumnTypes(),
            api.getTimeline(),
        ]);

        setColumns(mapColumns(columnTypes.columns));
        const nextHistory = timelineResponse.events
            .filter((event) => event.category === 'preprocessing')
            .map((entry, index) => mapHistoryEntry(entry, index))
            .filter((entry): entry is ProcessingHistory => entry !== null);
        setHistory(nextHistory);
    }, []);

    const notifyDatasetMutation = useCallback(() => {
        const currentSessionId = api.getStoredSessionId();
        if (currentSessionId) {
            api.setStoredSessionId(currentSessionId);
        }
    }, []);

    // Actions - connected to API
    const applyMissingValues = useCallback(async (config: MissingValueConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyMissingValues(config.method, config.columns);

            await refreshColumnsAndHistory();
            notifyDatasetMutation();
            notify.success('Eksik değer işlemi uygulandı');
        } catch (err) {
            const message = getErrorMessage(err, 'İşlem sırasında hata oluştu');
            logger.error('Missing values preprocessing failed', err, { method: config.method });
            setError(message);
            notify.error(err, 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [notifyDatasetMutation, refreshColumnsAndHistory]);

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
            notifyDatasetMutation();
            notify.success('Aykırı değer işlemi uygulandı');
        } catch (err) {
            const message = getErrorMessage(err, 'İşlem sırasında hata oluştu');
            logger.error('Outlier preprocessing failed', err, { method: config.method });
            setError(message);
            notify.error(err, 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [notifyDatasetMutation, refreshColumnsAndHistory]);

    const applyEncoding = useCallback(async (config: EncodingConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyEncoding(
                config.method,
                config.columns,
                config.dropFirst,
                config.ordinalMapping
            );

            await refreshColumnsAndHistory();
            notifyDatasetMutation();
            notify.success('Kodlama işlemi uygulandı');
        } catch (err) {
            const message = getErrorMessage(err, 'İşlem sırasında hata oluştu');
            logger.error('Encoding preprocessing failed', err, { method: config.method });
            setError(message);
            notify.error(err, 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [notifyDatasetMutation, refreshColumnsAndHistory]);

    const applyScaling = useCallback(async (config: ScalingConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyScaling(config.method, config.columns, config.featureRange);

            await refreshColumnsAndHistory();
            notifyDatasetMutation();
            notify.success('Ölçeklendirme işlemi uygulandı');
        } catch (err) {
            const message = getErrorMessage(err, 'İşlem sırasında hata oluştu');
            logger.error('Scaling preprocessing failed', err, { method: config.method });
            setError(message);
            notify.error(err, 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [notifyDatasetMutation, refreshColumnsAndHistory]);

    const applyFeatureEngineering = useCallback(async (config: FeatureConfig) => {
        try {
            setIsLoading(true);
            setError(null);

            await api.applyFeatureEngineering(config);

            await refreshColumnsAndHistory();
            notifyDatasetMutation();
            notify.success('Özellik mühendisliği işlemi uygulandı');
        } catch (err) {
            const message = getErrorMessage(err, 'İşlem sırasında hata oluştu');
            logger.error('Feature engineering preprocessing failed', err, { operation: config.operation });
            setError(message);
            notify.error(err, 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
}, [notifyDatasetMutation, refreshColumnsAndHistory]);

    const dropColumns = useCallback(async (config: DropColumnConfig) => {
        try {
            setIsLoading(true);
            setError(null);
            await api.dropColumns(config.columns, config.reason);
            await refreshColumnsAndHistory();
            notifyDatasetMutation();
            notify.success('Sütunlar silindi');
        } catch (err) {
            const message = getErrorMessage(err, 'İşlem sırasında hata oluştu');
            logger.error('Drop columns failed', err, { columns: config.columns });
            setError(message);
            notify.error(err, 'İşlem sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [notifyDatasetMutation, refreshColumnsAndHistory]);

    const undoLastAction = useCallback(async () => {
        if (history.length === 0) {
            return;
        }

        try {
            setIsLoading(true);
            setError(null);
            await api.undoLastTimelineEvent();
            await refreshColumnsAndHistory();
            notifyDatasetMutation();
            notify.success('Son işlem geri alındı');
        } catch (err) {
            const message = getErrorMessage(err, 'Geri alma sırasında hata oluştu');
            logger.error('Undo preprocessing failed', err);
            setError(message);
            notify.error(err, 'Geri alma sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [history.length, notifyDatasetMutation, refreshColumnsAndHistory]);

    const undoToHistoryItem = useCallback(async (historyIndex: number) => {
        try {
            setIsLoading(true);
            setError(null);
            await api.undoPreprocessingTo(historyIndex);
            await refreshColumnsAndHistory();
            notifyDatasetMutation();
            notify.success('Seçili işleme geri dönüldü');
        } catch (err) {
            const message = getErrorMessage(err, 'Seçili işlem geri alınırken hata oluştu');
            logger.error('Undo preprocessing to history item failed', err, { historyIndex });
            setError(message);
            notify.error(err, 'Seçili işlem geri alınırken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [notifyDatasetMutation, refreshColumnsAndHistory]);

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
            notifyDatasetMutation();
            notify.success('Ön işleme adımları sıfırlandı');
        } catch (err) {
            const message = getErrorMessage(err, 'Sıfırlama sırasında hata oluştu');
            logger.error('Reset preprocessing failed', err);
            setError(message);
            notify.error(err, 'Sıfırlama sırasında hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, [loadColumns, notifyDatasetMutation]);

    const semanticCategoricalColumnNames = useMemo(() => {
        const currentColumnNames = new Set(columns.map((column) => column.name));
        const semanticColumns = new Set<string>();

        for (const item of history) {
            if (item.stepKey !== 'encoding') {
                continue;
            }

            item.columns?.forEach((column) => {
                if (currentColumnNames.has(column)) {
                    semanticColumns.add(column);
                }
            });

            item.newColumns?.forEach((column) => {
                if (currentColumnNames.has(column)) {
                    semanticColumns.add(column);
                }
            });
        }

        return semanticColumns;
    }, [columns, history]);

    // Memoized column filters
    const numericColumns = useMemo(
        () => columns.filter((col) => col.type === 'numeric' && !semanticCategoricalColumnNames.has(col.name)),
        [columns, semanticCategoricalColumnNames]
    );

    const scalingColumns = useMemo(() => {
        const scaledColumnNames = new Set<string>();

        for (const item of history) {
            if (item.stepKey === 'scaling') {
                item.columns?.forEach((column) => scaledColumnNames.add(column));
            }
        }

        return numericColumns.filter((column) => !scaledColumnNames.has(column.name));
    }, [history, numericColumns]);

    const categoricalColumns = useMemo(
        () => columns.filter(
            (col) =>
                (col.type === 'categorical' || col.type === 'text') &&
                !semanticCategoricalColumnNames.has(col.name)
        ),
        [columns, semanticCategoricalColumnNames]
    );

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
        dropColumns,
        undoLastAction,
        undoToHistoryItem,
        resetAll,
        numericColumns,
        scalingColumns,
        categoricalColumns,
        columnsWithMissing,
    };
}

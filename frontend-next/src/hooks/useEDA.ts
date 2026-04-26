'use client';

import { useState, useCallback, useEffect, useSyncExternalStore } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import {
    EDAData,
    HistogramData,
    BoxPlotData,
    CategoryData,
} from '@/types/eda';
import * as api from '@/lib/api';
import { logger } from '@/lib/logger';
import { getErrorMessage, notify } from '@/lib/notify';
import { clearDatasetQueries, datasetQueryKeys, invalidateDatasetQueries } from '@/lib/query-cache';

interface UseEDAReturn {
    edaData: EDAData | null;
    isLoading: boolean;
    error: string | null;
    selectedNumericColumn: string | null;
    selectedCategoricalColumn: string | null;
    setSelectedNumericColumn: (col: string) => void;
    setSelectedCategoricalColumn: (col: string) => void;
    loadEDAData: () => Promise<boolean>;
    histogramData: HistogramData[];
    boxPlotData: BoxPlotData | null;
    categoryData: CategoryData[];
    scatterData: { x: number; y: number }[];
    scatterXColumn: string | null;
    scatterYColumn: string | null;
    setScatterColumns: (x: string, y: string) => void;
}

export function useEDA(): UseEDAReturn {
    const queryClient = useQueryClient();
    const sessionId = useSyncExternalStore(api.subscribeToStoredSession, api.getStoredSessionId, () => null);
    const [selectedNumericColumn, setSelectedNumericColumn] = useState<string | null>(null);
    const [selectedCategoricalColumn, setSelectedCategoricalColumn] = useState<string | null>(null);
    const [scatterXColumn, setScatterXColumn] = useState<string | null>(null);
    const [scatterYColumn, setScatterYColumn] = useState<string | null>(null);

    const {
        data: edaData = null,
        isLoading: isEdaLoading,
        error: edaError,
        refetch: refetchEda,
    } = useQuery({
        queryKey: datasetQueryKeys.edaSummary(sessionId),
        queryFn: async () => {
            const [summary, columnTypes, numericStats, categoricalStats, correlation] = await Promise.all([
                api.getEDASummary(),
                api.getColumnTypes(),
                api.getNumericStats(),
                api.getCategoricalStats(),
                api.getCorrelation(),
            ]);

            const VARIANCE_THRESHOLD = 0.001;
            const NULL_PERCENTAGE_THRESHOLD = 50;
            const MIN_CARDINALITY = 2;
            const MAX_CARDINALITY = 50;

            const filteredNumericColumns = numericStats.stats
                .filter(stat =>
                    stat.variance > VARIANCE_THRESHOLD &&
                    stat.null_percentage < NULL_PERCENTAGE_THRESHOLD &&
                    stat.unique_count < stat.count
                )
                .map(stat => stat.column);

            const filteredCategoricalColumns = categoricalStats.stats
                .filter(stat =>
                    stat.unique >= MIN_CARDINALITY &&
                    stat.unique <= MAX_CARDINALITY &&
                    stat.null_percentage < NULL_PERCENTAGE_THRESHOLD
                )
                .map(stat => stat.column);

            const data: EDAData = {
                numericStats: numericStats.stats.map(stat => ({
                    column: stat.column,
                    count: stat.count,
                    mean: stat.mean,
                    std: stat.std,
                    min: stat.min,
                    q25: stat.q25,
                    median: stat.median,
                    q75: stat.q75,
                    max: stat.max,
                })),
                categoricalStats: categoricalStats.stats.map(stat => ({
                    column: stat.column,
                    count: stat.count,
                    unique: stat.unique,
                    top: stat.top || '',
                    frequency: stat.frequency,
                })),
                columnTypes: columnTypes.columns.map(col => ({
                    name: col.name,
                    dtype: col.dtype,
                    type: col.type,
                    nullCount: col.null_count,
                    nullPercentage: col.null_percentage,
                })),
                correlationMatrix: correlation.correlation.map(item => ({
                    x: item.x,
                    y: item.y,
                    value: item.value,
                })),
                numericColumns: filteredNumericColumns,
                categoricalColumns: filteredCategoricalColumns,
                duplicateRows: summary.duplicate_rows,
            };

            return data;
        },
        enabled: Boolean(sessionId),
        retry: false,
        staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    });

    const numericColumns = edaData?.numericColumns ?? [];
    const categoricalColumns = edaData?.categoricalColumns ?? [];
    const defaultScatterXColumn = numericColumns[0] ?? null;
    const defaultScatterYColumn = numericColumns.find((column) => column !== defaultScatterXColumn) ?? null;

    const resolvedSelectedNumericColumn =
        selectedNumericColumn && numericColumns.includes(selectedNumericColumn)
            ? selectedNumericColumn
            : numericColumns[0] ?? null;

    const resolvedSelectedCategoricalColumn =
        selectedCategoricalColumn && categoricalColumns.includes(selectedCategoricalColumn)
            ? selectedCategoricalColumn
            : categoricalColumns[0] ?? null;

    const resolvedScatterXColumn =
        scatterXColumn && numericColumns.includes(scatterXColumn)
            ? scatterXColumn
            : defaultScatterXColumn;

    const scatterYFallback =
        scatterYColumn && numericColumns.includes(scatterYColumn)
            ? scatterYColumn
            : defaultScatterYColumn;

    const resolvedScatterYColumn =
        scatterYFallback && scatterYFallback !== resolvedScatterXColumn
            ? scatterYFallback
            : numericColumns.find((column) => column !== resolvedScatterXColumn) ?? null;

    const { data: histogramData = [] } = useQuery({
        queryKey: datasetQueryKeys.edaHistogram(sessionId, resolvedSelectedNumericColumn),
        queryFn: async () => {
            if (!resolvedSelectedNumericColumn) return [];
            const result = await api.getHistogram(resolvedSelectedNumericColumn);
            return result.data.map(d => ({
                bin: d.bin,
                count: d.count,
                percentage: d.percentage,
            }));
        },
        enabled: Boolean(sessionId && resolvedSelectedNumericColumn),
        retry: false,
        staleTime: 5 * 60 * 1000,
    });

    const { data: boxPlotData = null } = useQuery({
        queryKey: datasetQueryKeys.edaBoxplot(sessionId, resolvedSelectedNumericColumn),
        queryFn: async () => {
            if (!resolvedSelectedNumericColumn) return null;
            return await api.getBoxPlot(resolvedSelectedNumericColumn);
        },
        enabled: Boolean(sessionId && resolvedSelectedNumericColumn),
        retry: false,
        staleTime: 5 * 60 * 1000,
    });

    const { data: categoryData = [] } = useQuery({
        queryKey: datasetQueryKeys.edaCategory(sessionId, resolvedSelectedCategoricalColumn),
        queryFn: async () => {
            if (!resolvedSelectedCategoricalColumn) return [];
            const result = await api.getCategoryDistribution(resolvedSelectedCategoricalColumn);
            return result.data.map(d => ({
                name: d.name,
                value: d.value,
                percentage: d.percentage,
            }));
        },
        enabled: Boolean(sessionId && resolvedSelectedCategoricalColumn),
        retry: false,
        staleTime: 5 * 60 * 1000,
    });

    const { data: scatterData = [] } = useQuery({
        queryKey: datasetQueryKeys.edaScatter(sessionId, resolvedScatterXColumn, resolvedScatterYColumn),
        queryFn: async () => {
            if (!resolvedScatterXColumn || !resolvedScatterYColumn || resolvedScatterXColumn === resolvedScatterYColumn) {
                return [];
            }
            const result = await api.getScatterData(resolvedScatterXColumn, resolvedScatterYColumn);
            return result.data;
        },
        enabled: Boolean(
            sessionId &&
            resolvedScatterXColumn &&
            resolvedScatterYColumn &&
            resolvedScatterXColumn !== resolvedScatterYColumn
        ),
        retry: false,
        staleTime: 5 * 60 * 1000,
    });

    const loadEDAData = useCallback(async (): Promise<boolean> => {
        if (!sessionId) {
            return false;
        }
        const result = await refetchEda();
        if (result.isError) {
            if (!api.isSessionRequiredError(result.error)) {
                notify.error(result.error, 'EDA verisi yüklenirken hata oluştu');
                logger.error('EDA data load failed', result.error);
            }
            return false;
        }
        return true;
    }, [refetchEda, sessionId]);

    const setScatterColumns = useCallback((x: string, y: string) => {
        setScatterXColumn(x);
        setScatterYColumn(y);
    }, []);

    useEffect(() => {
        return api.subscribeToStoredSession(() => {
            if (api.getStoredSessionId()) {
                void invalidateDatasetQueries(queryClient);
                return;
            }
            clearDatasetQueries(queryClient);
        });
    }, [queryClient]);

    const errorMessage = edaError && !api.isSessionRequiredError(edaError) 
        ? getErrorMessage(edaError, 'EDA verisi yüklenirken hata oluştu') 
        : null;

    return {
        edaData,
        isLoading: isEdaLoading,
        error: errorMessage,
        selectedNumericColumn: resolvedSelectedNumericColumn,
        selectedCategoricalColumn: resolvedSelectedCategoricalColumn,
        setSelectedNumericColumn,
        setSelectedCategoricalColumn,
        loadEDAData,
        histogramData,
        boxPlotData,
        categoryData,
        scatterData,
        scatterXColumn: resolvedScatterXColumn,
        scatterYColumn: resolvedScatterYColumn,
        setScatterColumns,
    };
}

'use client';

import { useState, useCallback, useMemo, useEffect } from 'react';
import {
    EDAData,
    NumericStats,
    CategoricalStats,
    ColumnType,
    CorrelationData,
    HistogramData,
    BoxPlotData,
    CategoryData,
} from '@/types/eda';
import * as api from '@/lib/api';

interface UseEDAReturn {
    edaData: EDAData | null;
    isLoading: boolean;
    error: string | null;
    selectedNumericColumn: string | null;
    selectedCategoricalColumn: string | null;
    setSelectedNumericColumn: (col: string) => void;
    setSelectedCategoricalColumn: (col: string) => void;
    loadEDAData: () => Promise<void>;
    histogramData: HistogramData[];
    boxPlotData: BoxPlotData | null;
    categoryData: CategoryData[];
    scatterData: { x: number; y: number }[];
    scatterXColumn: string | null;
    scatterYColumn: string | null;
    setScatterColumns: (x: string, y: string) => void;
}

export function useEDA(): UseEDAReturn {
    const [edaData, setEdaData] = useState<EDAData | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedNumericColumn, setSelectedNumericColumn] = useState<string | null>(null);
    const [selectedCategoricalColumn, setSelectedCategoricalColumn] = useState<string | null>(null);
    const [scatterXColumn, setScatterXColumn] = useState<string | null>(null);
    const [scatterYColumn, setScatterYColumn] = useState<string | null>(null);

    // Chart data from API
    const [histogramData, setHistogramData] = useState<HistogramData[]>([]);
    const [boxPlotData, setBoxPlotData] = useState<BoxPlotData | null>(null);
    const [categoryData, setCategoryData] = useState<CategoryData[]>([]);

    const loadEDAData = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);

            // Fetch from real API
            const [summary, columnTypes, numericStats, categoricalStats, correlation] = await Promise.all([
                api.getEDASummary(),
                api.getColumnTypes(),
                api.getNumericStats(),
                api.getCategoricalStats(),
                api.getCorrelation(),
            ]);

            // Transform API response to EDAData format
            const transformedColumnTypes: ColumnType[] = columnTypes.columns.map(col => ({
                name: col.name,
                dtype: col.dtype,
                type: col.type,
                nullCount: col.null_count,
                nullPercentage: col.null_percentage,
            }));

            const transformedNumericStats: NumericStats[] = numericStats.stats.map(stat => ({
                column: stat.column,
                count: stat.count,
                mean: stat.mean,
                std: stat.std,
                min: stat.min,
                q25: stat.q25,
                median: stat.median,
                q75: stat.q75,
                max: stat.max,
            }));

            const transformedCategoricalStats: CategoricalStats[] = categoricalStats.stats.map(stat => ({
                column: stat.column,
                count: stat.count,
                unique: stat.unique,
                top: stat.top || '',
                frequency: stat.frequency,
            }));

            const transformedCorrelation: CorrelationData[] = correlation.correlation.map(item => ({
                x: item.x,
                y: item.y,
                value: item.value,
            }));

            const data: EDAData = {
                numericStats: transformedNumericStats,
                categoricalStats: transformedCategoricalStats,
                columnTypes: transformedColumnTypes,
                correlationMatrix: transformedCorrelation,
                numericColumns: summary.numeric_columns,
                categoricalColumns: summary.categorical_columns,
            };

            setEdaData(data);

            // Set default selections
            if (summary.numeric_columns.length > 0) {
                setSelectedNumericColumn(summary.numeric_columns[0]);
                if (summary.numeric_columns.length > 1) {
                    setScatterXColumn(summary.numeric_columns[0]);
                    setScatterYColumn(summary.numeric_columns[1]);
                }
            }
            if (summary.categorical_columns.length > 0) {
                setSelectedCategoricalColumn(summary.categorical_columns[0]);
            }
        } catch (err) {
            console.error('EDA Error:', err);
            setError(err instanceof Error ? err.message : 'EDA verisi yüklenirken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, []);

    // Load histogram when numeric column changes
    useEffect(() => {
        if (!selectedNumericColumn) return;

        api.getHistogram(selectedNumericColumn)
            .then(result => {
                setHistogramData(result.data.map(d => ({
                    bin: d.bin,
                    count: d.count,
                    percentage: d.percentage,
                })));
            })
            .catch(console.error);
    }, [selectedNumericColumn]);

    // Load box plot when numeric column changes
    useEffect(() => {
        if (!selectedNumericColumn) return;

        api.getBoxPlot(selectedNumericColumn)
            .then(result => setBoxPlotData(result))
            .catch(console.error);
    }, [selectedNumericColumn]);

    // Load category distribution when categorical column changes
    useEffect(() => {
        if (!selectedCategoricalColumn) return;

        api.getCategoryDistribution(selectedCategoricalColumn)
            .then(result => {
                setCategoryData(result.data.map(d => ({
                    name: d.name,
                    value: d.value,
                    percentage: d.percentage,
                })));
            })
            .catch(console.error);
    }, [selectedCategoricalColumn]);

    const setScatterColumns = useCallback((x: string, y: string) => {
        setScatterXColumn(x);
        setScatterYColumn(y);
    }, []);



    // Scatter data (mock for now - would need API endpoint)
    const scatterData = useMemo(() => {
        if (!scatterXColumn || !scatterYColumn) return [];
        return Array.from({ length: 50 }, () => ({
            x: Math.random() * 100,
            y: Math.random() * 100,
        }));
    }, [scatterXColumn, scatterYColumn]);

    return {
        edaData,
        isLoading,
        error,
        selectedNumericColumn,
        selectedCategoricalColumn,
        setSelectedNumericColumn,
        setSelectedCategoricalColumn,
        loadEDAData,
        histogramData,
        boxPlotData,
        categoryData,
        scatterData,
        scatterXColumn,
        scatterYColumn,
        setScatterColumns,
    };
}

'use client';

import { useState, useCallback, useMemo } from 'react';
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

// Mock data generator for demo
function generateMockEDAData(): EDAData {
    const numericColumns = ['age', 'salary', 'experience', 'score'];
    const categoricalColumns = ['department', 'gender', 'status'];

    const numericStats: NumericStats[] = numericColumns.map(col => ({
        column: col,
        count: 1000,
        mean: Math.random() * 100,
        std: Math.random() * 20,
        min: Math.random() * 10,
        q25: Math.random() * 30,
        median: Math.random() * 50,
        q75: Math.random() * 70,
        max: Math.random() * 100,
    }));

    const categoricalStats: CategoricalStats[] = categoricalColumns.map(col => ({
        column: col,
        count: 1000,
        unique: Math.floor(Math.random() * 10) + 2,
        top: 'Category A',
        frequency: Math.floor(Math.random() * 500) + 100,
    }));

    const columnTypes: ColumnType[] = [
        ...numericColumns.map(col => ({
            name: col,
            dtype: 'float64',
            type: 'numeric' as const,
            nullCount: Math.floor(Math.random() * 50),
            nullPercentage: Math.random() * 5,
        })),
        ...categoricalColumns.map(col => ({
            name: col,
            dtype: 'object',
            type: 'categorical' as const,
            nullCount: Math.floor(Math.random() * 20),
            nullPercentage: Math.random() * 2,
        })),
    ];

    // Generate correlation matrix
    const correlationMatrix: CorrelationData[] = [];
    numericColumns.forEach(x => {
        numericColumns.forEach(y => {
            correlationMatrix.push({
                x,
                y,
                value: x === y ? 1 : Math.random() * 2 - 1, // -1 to 1
            });
        });
    });

    return {
        numericStats,
        categoricalStats,
        columnTypes,
        correlationMatrix,
        numericColumns,
        categoricalColumns,
    };
}

// Generate histogram data for a column
export function generateHistogramData(column: string): HistogramData[] {
    const bins = ['0-10', '10-20', '20-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90-100'];
    const total = 1000;

    return bins.map(bin => {
        const count = Math.floor(Math.random() * 200) + 20;
        return {
            bin,
            count,
            percentage: (count / total) * 100,
        };
    });
}

// Generate box plot data
export function generateBoxPlotData(columns: string[]): BoxPlotData[] {
    return columns.map(column => ({
        column,
        min: Math.random() * 10,
        q1: Math.random() * 25 + 10,
        median: Math.random() * 20 + 40,
        q3: Math.random() * 20 + 60,
        max: Math.random() * 20 + 80,
        outliers: [Math.random() * 5, Math.random() * 100 + 95],
    }));
}

// Generate category distribution
export function generateCategoryData(column: string): CategoryData[] {
    const categories = ['Kategori A', 'Kategori B', 'Kategori C', 'Kategori D', 'Diğer'];
    const total = 1000;
    let remaining = total;

    return categories.map((name, index) => {
        const isLast = index === categories.length - 1;
        const value = isLast ? remaining : Math.floor(Math.random() * (remaining * 0.5)) + 50;
        remaining -= value;
        return {
            name,
            value,
            percentage: (value / total) * 100,
        };
    });
}

// Generate scatter data
export function generateScatterData(xColumn: string, yColumn: string): { x: number; y: number }[] {
    return Array.from({ length: 100 }, () => ({
        x: Math.random() * 100,
        y: Math.random() * 100,
    }));
}

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
    boxPlotData: BoxPlotData[];
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

    const loadEDAData = useCallback(async () => {
        try {
            setIsLoading(true);
            setError(null);

            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 500));

            // TODO: Replace with actual API call
            const data = generateMockEDAData();
            setEdaData(data);

            // Set default selections
            if (data.numericColumns.length > 0) {
                setSelectedNumericColumn(data.numericColumns[0]);
                if (data.numericColumns.length > 1) {
                    setScatterXColumn(data.numericColumns[0]);
                    setScatterYColumn(data.numericColumns[1]);
                }
            }
            if (data.categoricalColumns.length > 0) {
                setSelectedCategoricalColumn(data.categoricalColumns[0]);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'EDA verisi yüklenirken hata oluştu');
        } finally {
            setIsLoading(false);
        }
    }, []);

    const setScatterColumns = useCallback((x: string, y: string) => {
        setScatterXColumn(x);
        setScatterYColumn(y);
    }, []);

    // Memoized chart data
    const histogramData = useMemo(() => {
        if (!selectedNumericColumn) return [];
        return generateHistogramData(selectedNumericColumn);
    }, [selectedNumericColumn]);

    const boxPlotData = useMemo(() => {
        if (!edaData) return [];
        return generateBoxPlotData(edaData.numericColumns);
    }, [edaData]);

    const categoryData = useMemo(() => {
        if (!selectedCategoricalColumn) return [];
        return generateCategoryData(selectedCategoricalColumn);
    }, [selectedCategoricalColumn]);

    const scatterData = useMemo(() => {
        if (!scatterXColumn || !scatterYColumn) return [];
        return generateScatterData(scatterXColumn, scatterYColumn);
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

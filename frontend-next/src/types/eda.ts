// EDA types

export interface NumericStats {
    column: string;
    count: number;
    mean: number;
    std: number;
    min: number;
    q25: number;
    median: number;
    q75: number;
    max: number;
}

export interface CategoricalStats {
    column: string;
    count: number;
    unique: number;
    top: string;
    frequency: number;
}

export interface ColumnType {
    name: string;
    dtype: string;
    type: 'numeric' | 'categorical' | 'datetime' | 'text';
    nullCount: number;
    nullPercentage: number;
}

export interface CorrelationData {
    x: string;
    y: string;
    value: number;
}

export interface HistogramData {
    bin: string;
    count: number;
    percentage: number;
}

export interface BoxPlotData {
    column: string;
    min: number;
    q1: number;
    median: number;
    q3: number;
    max: number;
    outliers: number[];
}

export interface CategoryData {
    name: string;
    value: number;
    percentage: number;
}

export interface ScatterData {
    x: number;
    y: number;
    label?: string;
}

export interface EDAData {
    numericStats: NumericStats[];
    categoricalStats: CategoricalStats[];
    columnTypes: ColumnType[];
    correlationMatrix: CorrelationData[];
    numericColumns: string[];
    categoricalColumns: string[];
    duplicateRows: number;
}

export type ChartType = 'histogram' | 'boxplot' | 'scatter' | 'bar' | 'correlation';

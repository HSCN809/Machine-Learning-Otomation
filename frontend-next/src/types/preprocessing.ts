// Data Preprocessing types

export interface PreprocessingStep {
    id: string;
    name: string;
    icon: string;
    key: string;
    description: string;
}

export interface ProcessingHistory {
    id: string;
    historyIndex: number;
    stepKey: string;
    action: string;
    column?: string;
    columns?: string[];
    newColumns?: string[];
    method: string;
    params?: Record<string, unknown>;
    timestamp: Date;
    affectedRows?: number;
}

// Missing Values
export type MissingValueMethod =
    | 'drop_columns'
    | 'fill_mean'
    | 'fill_median'
    | 'fill_mode'
    | 'fill_knn'
    | 'fill_interpolation'
    | 'fill_regression'
    | 'fill_ffill'
    | 'fill_bfill';

export interface MissingValueConfig {
    method: MissingValueMethod;
    columns: string[];
}

// Outliers
export type OutlierMethod =
    | 'iqr_cap'
    | 'iqr_winsorize';

export interface OutlierConfig {
    method: OutlierMethod;
    columns: string[];
    threshold?: number;
    winsorizePercent?: number;
}

// Encoding
export type EncodingMethod =
    | 'label'
    | 'onehot'
    | 'ordinal'
    | 'binary'
    | 'frequency';

export interface EncodingConfig {
    method: EncodingMethod;
    columns: string[];
    dropFirst?: boolean;
    ordinalMapping?: Record<string, number>;
}

// Scaling
export type ScalingMethod =
    | 'standard'
    | 'minmax'
    | 'robust'
    | 'maxabs'
    | 'normalizer';

export interface ScalingConfig {
    method: ScalingMethod;
    columns: string[];
    featureRange?: [number, number];
}

// Feature Engineering
export type FeatureOperation =
    | 'create_numeric'
    | 'create_datetime'
    | 'create_categorical'
    | 'polynomial'
    | 'binning'
    | 'drop_columns';

export interface DropColumnConfig {
    columns: string[];
    reason?: string;
}

export type NumericFeatureOperation =
    | 'add'
    | 'subtract'
    | 'multiply'
    | 'divide'
    | 'custom';

export type BinningStrategy = 'equal_width' | 'quantile';

export type DatetimeFeaturePart =
    | 'year'
    | 'month'
    | 'day'
    | 'weekday'
    | 'hour'
    | 'minute'
    | 'second';

export interface FeatureParams {
    numericOperation?: NumericFeatureOperation;
    strategy?: BinningStrategy;
    binCount?: number;
    datetimePart?: DatetimeFeaturePart;
    separator?: string;
}

export interface FeatureConfig {
    operation: FeatureOperation;
    sourceColumns: string[];
    newColumnName?: string;
    expression?: string;
    params?: FeatureParams;
}

// Step status
export type StepStatus = 'pending' | 'current' | 'completed' | 'skipped';

export interface PreprocessingState {
    currentStep: number;
    completedSteps: number[];
    skippedSteps: number[];
    history: ProcessingHistory[];
    originalData: Record<string, unknown>[] | null;
    processedData: Record<string, unknown>[] | null;
}

// Column info for selectors
export interface ColumnInfo {
    name: string;
    type: 'numeric' | 'categorical' | 'datetime' | 'text';
    dtype: string;
    missingCount: number;
    missingPercentage: number;
    uniqueCount: number;
    outlierCount?: number;
    outlierPercentage?: number;
}

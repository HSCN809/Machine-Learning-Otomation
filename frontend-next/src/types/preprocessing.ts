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
    stepKey: string;
    action: string;
    column?: string;
    columns?: string[];
    method: string;
    params?: Record<string, unknown>;
    timestamp: Date;
    affectedRows?: number;
}

// Missing Values
export type MissingValueMethod =
    | 'drop_rows'
    | 'drop_columns'
    | 'fill_mean'
    | 'fill_median'
    | 'fill_mode'
    | 'fill_constant'
    | 'fill_ffill'
    | 'fill_bfill';

export interface MissingValueConfig {
    method: MissingValueMethod;
    columns: string[];
    fillValue?: string | number;
}

// Outliers
export type OutlierMethod =
    | 'iqr_remove'
    | 'iqr_cap'
    | 'zscore_remove'
    | 'zscore_cap'
    | 'isolation_forest'
    | 'lof';

export interface OutlierConfig {
    method: OutlierMethod;
    columns: string[];
    threshold?: number;
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
    | 'binning';

export interface FeatureConfig {
    operation: FeatureOperation;
    sourceColumns: string[];
    newColumnName: string;
    expression?: string;
    params?: Record<string, unknown>;
}

// Step status
export type StepStatus = 'pending' | 'current' | 'completed' | 'skipped';

export interface PreprocessingState {
    currentStep: number;
    completedSteps: number[];
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
}

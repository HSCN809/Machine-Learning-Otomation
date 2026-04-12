/**
 * API Client for FastAPI Backend
 */

import type { FeatureConfig } from '@/types/preprocessing';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const SESSION_REQUIRED_MESSAGE = 'Valid session ID required. Upload data first.';
const SESSION_ERROR_MESSAGES = new Set([SESSION_REQUIRED_MESSAGE, 'Session not found']);

// Session ID management
let sessionId: string | null = null;

function getSessionId(): string | null {
    if (typeof window !== 'undefined') {
        sessionId = sessionId || localStorage.getItem('ml_session_id');
    }
    return sessionId;
}

function setSessionId(id: string): void {
    sessionId = id;
    if (typeof window !== 'undefined') {
        localStorage.setItem('ml_session_id', id);
    }
}

export function clearStoredSession(): void {
    sessionId = null;
    if (typeof window !== 'undefined') {
        localStorage.removeItem('ml_session_id');
    }
}

export function hasStoredSession(): boolean {
    return Boolean(getSessionId());
}

export class SessionRequiredError extends Error {
    constructor(message: string = SESSION_REQUIRED_MESSAGE) {
        super(message);
        this.name = 'SessionRequiredError';
    }
}

export function isSessionRequiredError(error: unknown): error is SessionRequiredError {
    return error instanceof SessionRequiredError;
}

// Base fetch with session header
async function apiFetch<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const headers: HeadersInit = {
        ...options.headers,
    };

    const sid = getSessionId();
    if (sid) {
        (headers as Record<string, string>)['X-Session-Id'] = sid;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        const detail = typeof error.detail === 'string' ? error.detail : `HTTP ${response.status}`;

        if (SESSION_ERROR_MESSAGES.has(detail)) {
            clearStoredSession();
            throw new SessionRequiredError();
        }

        throw new Error(detail);
    }

    return response.json();
}

// ============== Upload API ==============

export interface UploadResponse {
    success: boolean;
    session_id: string;
    filename?: string;
    dataset?: string;
    rows: number;
    columns: number;
    column_names: string[];
}

export async function uploadFile(file: File): Promise<UploadResponse> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await apiFetch<UploadResponse>('/api/upload/file', {
        method: 'POST',
        body: formData,
    });

    if (response.session_id) {
        setSessionId(response.session_id);
    }

    return response;
}

export async function loadSampleDataset(datasetName: string): Promise<UploadResponse> {
    const response = await apiFetch<UploadResponse>(`/api/upload/sample/${datasetName}`, {
        method: 'POST',
    });

    if (response.session_id) {
        setSessionId(response.session_id);
    }

    return response;
}

export interface DataSummary {
    rows: number;
    columns: number;
    memory_usage: number;
    numeric_columns: string[];
    categorical_columns: string[];
    missing_total: number;
    duplicate_rows: number;
    column_info: {
        name: string;
        dtype: string;
        missing_count: number;
        missing_percentage: number;
        unique_count: number;
    }[];
}

export async function getDataSummary(): Promise<DataSummary> {
    return apiFetch<DataSummary>('/api/upload/summary');
}

export async function getDataPreview(rows: number = 10): Promise<{
    columns: string[];
    data: Record<string, unknown>[];
    total_rows: number;
}> {
    return apiFetch(`/api/upload/preview?rows=${rows}`);
}

export interface ValidationIssue {
    id: string;
    type: string;
    severity: 'critical' | 'warning' | 'info';
    column?: string;
    description: string;
    suggestion?: string;
    priority?: 'high' | 'medium' | 'low';
}

export interface ValidationResponse {
    is_valid: boolean;
    issues: ValidationIssue[];
    summary: {
        rows: number;
        columns: number;
        missing_total: number;
    };
}

export async function getDataValidation(): Promise<ValidationResponse> {
    return apiFetch<ValidationResponse>('/api/upload/validate');
}

export async function resetUpload(): Promise<{ success: boolean; message: string }> {
    return apiFetch('/api/upload/reset', { method: 'DELETE' });
}

// ============== EDA API ==============

export interface EDASummary {
    row_count: number;
    column_count: number;
    numeric_columns: string[];
    categorical_columns: string[];
    missing_count: number;
    missing_percentage: number;
    duplicate_rows: number;
    memory_mb: number;
}

export async function getEDASummary(): Promise<EDASummary> {
    return apiFetch<EDASummary>('/api/eda/summary');
}

export interface ColumnType {
    name: string;
    dtype: string;
    type: 'numeric' | 'categorical' | 'datetime' | 'text';
    null_count: number;
    null_percentage: number;
    unique_count: number;
}

export async function getColumnTypes(): Promise<{ columns: ColumnType[] }> {
    return apiFetch('/api/eda/column-types');
}

export interface NumericStat {
    column: string;
    count: number;
    unique_count: number;
    mean: number;
    std: number;
    variance: number;
    min: number;
    q25: number;
    median: number;
    q75: number;
    max: number;
    null_count: number;
    null_percentage: number;
}

export async function getNumericStats(): Promise<{ stats: NumericStat[] }> {
    return apiFetch('/api/eda/numeric-stats');
}

export interface CategoricalStat {
    column: string;
    count: number;
    unique: number;
    top: string | null;
    frequency: number;
    null_count: number;
    null_percentage: number;
}

export async function getCategoricalStats(): Promise<{ stats: CategoricalStat[] }> {
    return apiFetch('/api/eda/categorical-stats');
}

export interface CorrelationData {
    x: string;
    y: string;
    value: number;
}

export async function getCorrelation(): Promise<{
    correlation: CorrelationData[];
    columns: string[];
}> {
    return apiFetch('/api/eda/correlation');
}

export interface HistogramData {
    bin: string;
    count: number;
    percentage: number;
}

export async function getHistogram(column: string, bins: number = 20): Promise<{
    data: HistogramData[];
    column: string;
}> {
    return apiFetch(`/api/eda/histogram/${column}?bins=${bins}`);
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

export async function getBoxPlot(column: string): Promise<BoxPlotData> {
    return apiFetch(`/api/eda/boxplot/${column}`);
}

export interface CategoryData {
    name: string;
    value: number;
    percentage: number;
}

export async function getCategoryDistribution(column: string, topN: number = 10): Promise<{
    data: CategoryData[];
    column: string;
}> {
    return apiFetch(`/api/eda/category-distribution/${column}?top_n=${topN}`);
}

export interface ScatterData {
    x: number;
    y: number;
}

export async function getScatterData(xColumn: string, yColumn: string, sampleSize: number = 500): Promise<{
    data: ScatterData[];
    x_column: string;
    y_column: string;
    total_points: number;
}> {
    return apiFetch(`/api/eda/scatter?x_column=${xColumn}&y_column=${yColumn}&sample_size=${sampleSize}`);
}

// ============== Preprocessing API ==============

export interface PreprocessingResponse {
    success: boolean;
    method?: string;
    operation?: string;
    columns?: string[];
    requested_columns?: string[];
    affected_rows?: number;
    remaining_nulls?: number;
    remaining_rows?: number;
    new_columns?: string[];
    new_column?: string;
    total_columns?: number;
    winsorize_percent?: number;
}

export async function applyMissingValues(
    method: string,
    columns: string[]
): Promise<PreprocessingResponse> {
    return apiFetch('/api/preprocessing/missing-values', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, columns }),
    });
}

export async function applyOutliers(
    method: string,
    columns: string[],
    threshold?: number,
    winsorizePercent?: number
): Promise<PreprocessingResponse> {
    return apiFetch('/api/preprocessing/outliers', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method,
            columns,
            threshold,
            winsorize_percent: winsorizePercent,
        }),
    });
}

export interface OutlierColumnAnalysis {
    column: string;
    outlier_count: number;
    outlier_percentage: number;
}

export interface OutlierAnalysisResponse {
    success: boolean;
    method: string;
    detection_method: string;
    outlier_method: string;
    threshold?: number;
    detected_columns: string[];
    columns: OutlierColumnAnalysis[];
    total_outliers: number;
    total_rows: number;
    outlier_row_count: number;
    outlier_row_percentage: number;
}

export async function analyzeOutliers(
    method: string,
    columns?: string[],
    threshold?: number,
    winsorizePercent?: number
): Promise<OutlierAnalysisResponse> {
    return apiFetch('/api/preprocessing/outliers/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            method,
            columns,
            threshold,
            winsorize_percent: winsorizePercent,
        }),
    });
}

export async function applyEncoding(
    method: string,
    columns: string[],
    dropFirst?: boolean
): Promise<PreprocessingResponse> {
    return apiFetch('/api/preprocessing/encoding', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, columns, drop_first: dropFirst }),
    });
}

export async function applyScaling(
    method: string,
    columns: string[]
): Promise<PreprocessingResponse> {
    return apiFetch('/api/preprocessing/scaling', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ method, columns }),
    });
}

export async function applyFeatureEngineering(
    config: FeatureConfig
): Promise<PreprocessingResponse> {
    return apiFetch('/api/preprocessing/feature-engineering', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            operation: config.operation,
            source_columns: config.sourceColumns,
            new_column_name: config.newColumnName,
            expression: config.expression,
            params: config.params,
        }),
    });
}

export async function getPreprocessingHistory(): Promise<{ history: unknown[] }> {
    return apiFetch('/api/preprocessing/history');
}

export async function undoPreprocessing(): Promise<{ success: boolean; message: string }> {
    return apiFetch('/api/preprocessing/undo', { method: 'POST' });
}

export async function undoPreprocessingTo(historyIndex: number): Promise<{ success: boolean; message: string }> {
    return apiFetch('/api/preprocessing/undo-to', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history_index: historyIndex }),
    });
}

export async function resetPreprocessing(): Promise<{ success: boolean; message: string }> {
    return apiFetch('/api/preprocessing/reset', { method: 'POST' });
}

export interface DropColumnsResponse {
    success: boolean;
    dropped_columns: string[];
    missing_columns: string[];
    total_columns: number;
    remaining_rows: number;
}

export interface DropColumnRecommendation {
    column: string;
    unique_count: number;
    unique_ratio: number;
    missing_count: number;
    missing_percentage: number;
    reasons: string[];
}

export interface DroppableColumnsAnalysis {
    success: boolean;
    recommendations: DropColumnRecommendation[];
    recommended_columns: string[];
    all_columns: string[];
    cardinality_threshold: number;
}

export async function dropColumns(
    columns: string[],
    reason?: string
): Promise<DropColumnsResponse> {
    return apiFetch<DropColumnsResponse>('/api/preprocessing/drop-columns', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ columns, reason }),
    });
}

export async function analyzeDroppableColumns(
    cardinalityThreshold: number = 0.9
): Promise<DroppableColumnsAnalysis> {
    return apiFetch<DroppableColumnsAnalysis>(
        `/api/preprocessing/drop-columns/analyze?cardinality_threshold=${cardinalityThreshold}`
    );
}

// ============== Model API ==============

export interface ProblemTypeResponse {
    target_column: string;
    problem_type: 'classification' | 'regression';
    unique_values: number;
    dtype: string;
}

export async function detectProblemType(targetColumn: string): Promise<ProblemTypeResponse> {
    return apiFetch(`/api/model/detect-problem?target_column=${targetColumn}`);
}

export interface ModelInfo {
    id: string;
    name: string;
    category: string;
}

export async function getAvailableModels(problemType: string): Promise<{ models: ModelInfo[] }> {
    return apiFetch(`/api/model/available-models?problem_type=${problemType}`);
}

export interface TrainingResult {
    model_id: string;
    model_name: string;
    metrics: Record<string, number>;
    confusion_matrix?: number[][];
    feature_importance: { feature: string; importance: number }[];
    training_time: number;
}

export interface TrainResponse {
    success: boolean;
    problem_type: string;
    results: TrainingResult[];
}

export async function trainModels(
    targetColumn: string,
    models: string[],
    testSize: number = 0.2,
    params?: Record<string, Record<string, unknown>>
): Promise<TrainResponse> {
    return apiFetch('/api/model/train', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            target_column: targetColumn,
            models,
            test_size: testSize,
            params,
        }),
    });
}

export async function getTrainingResults(): Promise<{
    results: TrainingResult[];
    problem_type: string | null;
}> {
    return apiFetch('/api/model/results');
}

export async function getModelComparison(): Promise<{
    comparison: TrainingResult[];
    best_model: TrainingResult | null;
    primary_metric: string;
}> {
    return apiFetch('/api/model/comparison');
}

// ============== Health Check ==============

export async function healthCheck(): Promise<{ status: string }> {
    return apiFetch('/api/health');
}

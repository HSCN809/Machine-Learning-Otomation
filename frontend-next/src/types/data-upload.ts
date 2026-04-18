// Data Upload types

export interface UploadedFile {
    file: File;
    name: string;
    size: number;
    type: string;
}

export interface DatasetInfo {
    name: string;
    rows: number;
    columns: number;
    size: number;
    uploadedAt: Date;
}

export interface ColumnInfo {
    name: string;
    type: 'numeric' | 'categorical' | 'datetime' | 'text';
    dtype: string;
    uniqueCount: number;
    missingCount: number;
    missingPercentage: number;
}

export interface ValidationIssue {
    id: string;
    severity: 'critical' | 'warning' | 'info';
    type: 'missing_values' | 'constant_column' | 'high_cardinality' | 'duplicate_rows' | 'other';
    column?: string;
    description: string;
    suggestion?: string;
    priority?: 'high' | 'medium' | 'low';
}

export interface ValidationReport {
    isValid: boolean;
    totalIssues: number;
    issuesBySeverity: {
        critical: ValidationIssue[];
        warning: ValidationIssue[];
        info: ValidationIssue[];
    };
}

export interface DataSummary {
    shape: {
        rows: number;
        columns: number;
    };
    columns: ColumnInfo[];
    missingValues: {
        total: number;
        percentage: number;
    };
    duplicateRows: number;
    preview: Record<string, unknown>[];
}

export interface EditableRow {
    rowId: number;
    values: Record<string, unknown>;
}

export interface DataEditorPageResponse {
    page: number;
    pageSize: number;
    totalRows: number;
    totalPages: number;
    columns: string[];
    rows: EditableRow[];
}

export interface DataEditorCellRef {
    rowId: number;
    column: string;
}

export interface DataEditorCellUpdate extends DataEditorCellRef {
    value: string;
}

export interface DataEditorColumnRename {
    column: string;
    newName: string;
}

export interface DataEditorDraft {
    updatedCells: DataEditorCellUpdate[];
    clearedCells: DataEditorCellRef[];
    deletedRowIds: number[];
    trimColumns: string[];
    renamedColumns: DataEditorColumnRename[];
}

export interface DataEditorCommitResponse {
    success: boolean;
    rows: number;
    columns: number;
    updatedCells: number;
    clearedCells: number;
    deletedRows: number;
    trimmedColumns: number;
    renamedColumns: number;
}

export interface SampleDataset {
    id: string;
    name: string;
    description: string;
    emoji: string;
    rows: number;
    columns: number;
}

export type UploadStatus = 'idle' | 'uploading' | 'validating' | 'success' | 'error';

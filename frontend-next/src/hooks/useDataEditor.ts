'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import {
    DataEditorCellRef,
    DataEditorCellUpdate,
    DataEditorDraft,
    EditableRow,
} from '@/types/data-upload';
import * as api from '@/lib/api';
import { logger } from '@/lib/logger';
import { getErrorMessage, notify } from '@/lib/notify';

const EMPTY_DRAFT: DataEditorDraft = {
    updatedCells: [],
    clearedCells: [],
    deletedRowIds: [],
    trimColumns: [],
    renamedColumns: [],
};

function cloneDraft(draft: DataEditorDraft): DataEditorDraft {
    return {
        updatedCells: draft.updatedCells.map((cell) => ({ ...cell })),
        clearedCells: draft.clearedCells.map((cell) => ({ ...cell })),
        deletedRowIds: [...draft.deletedRowIds],
        trimColumns: [...draft.trimColumns],
        renamedColumns: draft.renamedColumns.map((column) => ({ ...column })),
    };
}

function draftsEqual(left: DataEditorDraft, right: DataEditorDraft): boolean {
    return JSON.stringify(left) === JSON.stringify(right);
}

function mergeRows(existingRows: EditableRow[], incomingRows: EditableRow[]): EditableRow[] {
    const rowMap = new Map<number, EditableRow>();

    existingRows.forEach((row) => {
        rowMap.set(row.rowId, row);
    });

    incomingRows.forEach((row) => {
        rowMap.set(row.rowId, row);
    });

    return Array.from(rowMap.values()).sort((left, right) => left.rowId - right.rowId);
}

function stringifyCellValue(value: unknown): string {
    if (value === null || value === undefined) {
        return '';
    }

    return String(value);
}

interface UseDataEditorOptions {
    onSaved?: () => Promise<void> | void;
}

interface UseDataEditorReturn {
    rows: EditableRow[];
    columns: string[];
    pageSize: number;
    totalRows: number;
    totalPages: number;
    loadedPages: number;
    hasMoreRows: boolean;
    error: string | null;
    isLoading: boolean;
    isLoadingMore: boolean;
    isSaving: boolean;
    draft: DataEditorDraft;
    isDirty: boolean;
    selectedRows: number[];
    selectedTrimColumns: string[];
    activeCell: DataEditorCellRef | null;
    setActiveCell: (cell: DataEditorCellRef | null) => void;
    loadMoreRows: () => Promise<void>;
    toggleRowSelection: (rowId: number) => void;
    replaceSelectedRows: (rowIds: number[]) => void;
    toggleAllLoadedRows: () => void;
    updateCell: (rowId: number, column: string, value: string) => void;
    updateCells: (cells: DataEditorCellUpdate[]) => void;
    renameColumn: (column: string, newName: string) => void;
    renameColumns: (renames: { column: string; newName: string }[]) => void;
    getColumnDisplayName: (column: string) => string;
    clearCells: (cells: DataEditorCellRef[]) => void;
    clearActiveCell: () => void;
    deleteSelectedRows: () => void;
    toggleTrimColumnSelection: (column: string) => void;
    applyTrimSelection: () => void;
    removeTrimColumn: (column: string) => void;
    undoLastChange: () => void;
    discardChanges: () => void;
    saveChanges: () => Promise<boolean>;
    reloadPage: () => Promise<void>;
}

export function useDataEditor({ onSaved }: UseDataEditorOptions = {}): UseDataEditorReturn {
    const [rows, setRows] = useState<EditableRow[]>([]);
    const [columns, setColumns] = useState<string[]>([]);
    const [pageSize] = useState(50);
    const [totalRows, setTotalRows] = useState(0);
    const [totalPages, setTotalPages] = useState(1);
    const [loadedPages, setLoadedPages] = useState(0);
    const [hasMoreRows, setHasMoreRows] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isLoadingMore, setIsLoadingMore] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [draft, setDraft] = useState<DataEditorDraft>(EMPTY_DRAFT);
    const [, setDraftHistory] = useState<DataEditorDraft[]>([]);
    const [selectedRows, setSelectedRows] = useState<number[]>([]);
    const [selectedTrimColumns, setSelectedTrimColumns] = useState<string[]>([]);
    const [activeCell, setActiveCell] = useState<DataEditorCellRef | null>(null);
    const loadingPagesRef = useRef(new Set<number>());

    const getColumnDisplayName = useCallback(
        (column: string) =>
            draft.renamedColumns.find((item) => item.column === column)?.newName ?? column,
        [draft.renamedColumns]
    );

    const loadPage = useCallback(
        async (nextPage: number, options?: { append?: boolean }) => {
            const shouldAppend = options?.append ?? false;

            if (loadingPagesRef.current.has(nextPage)) {
                return;
            }

            try {
                loadingPagesRef.current.add(nextPage);
                if (shouldAppend) {
                    setIsLoadingMore(true);
                } else {
                    setIsLoading(true);
                }

                setError(null);
                const response = await api.getDataEditorPage(nextPage, pageSize);

                setColumns(response.columns);
                setTotalRows(response.totalRows);
                setTotalPages(response.totalPages);
                setLoadedPages((previousLoadedPages) =>
                    shouldAppend ? Math.max(previousLoadedPages, response.page) : response.page
                );
                setHasMoreRows(response.page < response.totalPages);
                setRows((previousRows) =>
                    shouldAppend ? mergeRows(previousRows, response.rows) : response.rows
                );
            } catch (err) {
                logger.error('Data editor page load failed', err, { page: nextPage });
                setError(getErrorMessage(err, 'Veri düzenleyici yüklenemedi'));
            } finally {
                loadingPagesRef.current.delete(nextPage);
                if (shouldAppend) {
                    setIsLoadingMore(false);
                } else {
                    setIsLoading(false);
                }
            }
        },
        [pageSize]
    );

    useEffect(() => {
        void loadPage(1);
    }, [loadPage]);

    const applyDraftChange = useCallback((mutator: (draft: DataEditorDraft) => DataEditorDraft) => {
        setDraft((previousDraft) => {
            const nextDraft = mutator(cloneDraft(previousDraft));
            if (draftsEqual(previousDraft, nextDraft)) {
                return previousDraft;
            }

            setDraftHistory((previousHistory) => [...previousHistory, cloneDraft(previousDraft)]);
            return nextDraft;
        });
    }, []);

    const loadMoreRows = useCallback(async () => {
        if (isLoading || isLoadingMore || !hasMoreRows) {
            return;
        }

        await loadPage(loadedPages + 1, { append: true });
    }, [hasMoreRows, isLoading, isLoadingMore, loadPage, loadedPages]);

    const toggleRowSelection = useCallback((rowId: number) => {
        setSelectedRows((previousSelectedRows) =>
            previousSelectedRows.includes(rowId)
                ? previousSelectedRows.filter((value) => value !== rowId)
                : [...previousSelectedRows, rowId]
        );
    }, []);

    const toggleAllLoadedRows = useCallback(() => {
        const currentRowIds = rows.map((row) => row.rowId);

        if (currentRowIds.length === 0) {
            return;
        }

        setSelectedRows((previousSelectedRows) => {
            const isAllSelected = currentRowIds.every((rowId) => previousSelectedRows.includes(rowId));
            if (isAllSelected) {
                return previousSelectedRows.filter((rowId) => !currentRowIds.includes(rowId));
            }

            const nextSelectedRows = new Set(previousSelectedRows);
            currentRowIds.forEach((rowId) => nextSelectedRows.add(rowId));
            return Array.from(nextSelectedRows);
        });
    }, [rows]);

    const replaceSelectedRows = useCallback((rowIds: number[]) => {
        setSelectedRows(Array.from(new Set(rowIds)).sort((left, right) => left - right));
    }, []);

    const updateCells = useCallback(
        (cells: DataEditorCellUpdate[]) => {
            if (cells.length === 0) {
                return;
            }

            applyDraftChange((currentDraft) => {
                const nextUpdatedCells = new Map<string, DataEditorCellUpdate>();

                currentDraft.updatedCells.forEach((cell) => {
                    nextUpdatedCells.set(`${cell.rowId}:${cell.column}`, cell);
                });

                const clearedCellKeys = new Set(
                    currentDraft.clearedCells.map((cell) => `${cell.rowId}:${cell.column}`)
                );
                let hasEligibleCell = false;

                cells.forEach((cell) => {
                    if (currentDraft.deletedRowIds.includes(cell.rowId)) {
                        return;
                    }

                    const sourceRow = rows.find((row) => row.rowId === cell.rowId);
                    const originalValue = stringifyCellValue(sourceRow?.values[cell.column]);
                    hasEligibleCell = true;
                    const cellKey = `${cell.rowId}:${cell.column}`;

                    if (cell.value === originalValue) {
                        nextUpdatedCells.delete(cellKey);
                        clearedCellKeys.delete(cellKey);
                        return;
                    }

                    nextUpdatedCells.set(cellKey, cell);
                    clearedCellKeys.delete(cellKey);
                });

                if (!hasEligibleCell) {
                    return currentDraft;
                }

                currentDraft.updatedCells = Array.from(nextUpdatedCells.values());
                currentDraft.clearedCells = currentDraft.clearedCells.filter((cell) =>
                    clearedCellKeys.has(`${cell.rowId}:${cell.column}`)
                );
                return currentDraft;
            });
        },
        [applyDraftChange, rows]
    );

    const updateCell = useCallback(
        (rowId: number, column: string, value: string) => {
            updateCells([{ rowId, column, value }]);
        },
        [updateCells]
    );

    const renameColumn = useCallback(
        (column: string, newName: string) => {
            applyDraftChange((currentDraft) => {
                currentDraft.renamedColumns = currentDraft.renamedColumns.filter(
                    (item) => item.column !== column
                );

                if (newName !== column) {
                    currentDraft.renamedColumns.push({ column, newName });
                }

                return currentDraft;
            });
        },
        [applyDraftChange]
    );

    const renameColumns = useCallback(
        (renames: { column: string; newName: string }[]) => {
            if (renames.length === 0) {
                return;
            }

            applyDraftChange((currentDraft) => {
                const renameMap = new Map(renames.map((item) => [item.column, item.newName]));
                currentDraft.renamedColumns = currentDraft.renamedColumns.filter(
                    (item) => !renameMap.has(item.column)
                );

                renames.forEach(({ column, newName }) => {
                    if (newName !== column) {
                        currentDraft.renamedColumns.push({ column, newName });
                    }
                });

                return currentDraft;
            });
        },
        [applyDraftChange]
    );

    const clearCells = useCallback(
        (cells: DataEditorCellRef[]) => {
            if (cells.length === 0) {
                return;
            }

            applyDraftChange((currentDraft) => {
                const uniqueCells = new Map<string, DataEditorCellRef>();

                cells.forEach((cell) => {
                    if (currentDraft.deletedRowIds.includes(cell.rowId)) {
                        return;
                    }

                    uniqueCells.set(`${cell.rowId}:${cell.column}`, cell);
                });

                if (uniqueCells.size === 0) {
                    return currentDraft;
                }

                const selectedCellKeys = new Set(uniqueCells.keys());
                currentDraft.updatedCells = currentDraft.updatedCells.filter(
                    (cell) => !selectedCellKeys.has(`${cell.rowId}:${cell.column}`)
                );
                currentDraft.clearedCells = currentDraft.clearedCells.filter(
                    (cell) => !selectedCellKeys.has(`${cell.rowId}:${cell.column}`)
                );
                currentDraft.clearedCells.push(...uniqueCells.values());
                return currentDraft;
            });
        },
        [applyDraftChange]
    );

    const clearActiveCell = useCallback(() => {
        if (!activeCell) {
            return;
        }

        clearCells([activeCell]);
    }, [activeCell, clearCells]);

    const deleteSelectedRows = useCallback(() => {
        if (selectedRows.length === 0) {
            return;
        }

        applyDraftChange((currentDraft) => {
            const deletedRowIds = new Set([...currentDraft.deletedRowIds, ...selectedRows]);
            currentDraft.deletedRowIds = Array.from(deletedRowIds).sort((left, right) => left - right);
            currentDraft.updatedCells = currentDraft.updatedCells.filter(
                (cell) => !deletedRowIds.has(cell.rowId)
            );
            currentDraft.clearedCells = currentDraft.clearedCells.filter(
                (cell) => !deletedRowIds.has(cell.rowId)
            );
            return currentDraft;
        });

        if (activeCell && selectedRows.includes(activeCell.rowId)) {
            setActiveCell(null);
        }
        setSelectedRows([]);
    }, [activeCell, applyDraftChange, selectedRows]);

    const toggleTrimColumnSelection = useCallback((column: string) => {
        setSelectedTrimColumns((previousColumns) =>
            previousColumns.includes(column)
                ? previousColumns.filter((value) => value !== column)
                : [...previousColumns, column]
        );
    }, []);

    const applyTrimSelection = useCallback(() => {
        if (selectedTrimColumns.length === 0) {
            return;
        }

        applyDraftChange((currentDraft) => {
            const trimColumns = new Set([...currentDraft.trimColumns, ...selectedTrimColumns]);
            currentDraft.trimColumns = Array.from(trimColumns);
            return currentDraft;
        });
        setSelectedTrimColumns([]);
    }, [applyDraftChange, selectedTrimColumns]);

    const removeTrimColumn = useCallback(
        (column: string) => {
            applyDraftChange((currentDraft) => {
                currentDraft.trimColumns = currentDraft.trimColumns.filter((value) => value !== column);
                return currentDraft;
            });
        },
        [applyDraftChange]
    );

    const undoLastChange = useCallback(() => {
        setDraftHistory((previousHistory) => {
            if (previousHistory.length === 0) {
                return previousHistory;
            }

            const lastSnapshot = previousHistory[previousHistory.length - 1];
            setDraft(cloneDraft(lastSnapshot));
            return previousHistory.slice(0, -1);
        });
    }, []);

    const discardChanges = useCallback(() => {
        setDraft(cloneDraft(EMPTY_DRAFT));
        setDraftHistory([]);
        setSelectedRows([]);
        setSelectedTrimColumns([]);
        setActiveCell(null);
        setError(null);
    }, []);

    const saveChanges = useCallback(async () => {
        const isDirty =
            draft.updatedCells.length > 0 ||
            draft.clearedCells.length > 0 ||
            draft.deletedRowIds.length > 0 ||
            draft.trimColumns.length > 0 ||
            draft.renamedColumns.length > 0;

        if (!isDirty) {
            return false;
        }

        const renamedColumnNames = draft.renamedColumns.map((item) => item.newName.trim());
        const hasEmptyRenamedColumns = renamedColumnNames.some((name) => name.length === 0);

        if (hasEmptyRenamedColumns) {
            setDraft((previousDraft) => ({
                ...previousDraft,
                renamedColumns: previousDraft.renamedColumns.filter(
                    (item) => item.newName.trim().length > 0
                ),
            }));
            notify.warning('Sütun ismi boş bırakılamaz');
            return false;
        }

        const nextColumnNames = columns.map((column) => getColumnDisplayName(column).trim());
        if (new Set(nextColumnNames).size !== nextColumnNames.length) {
            notify.warning('Sütun adları kaydetmeden önce benzersiz olmalıdır');
            return false;
        }

        try {
            setIsSaving(true);
            setError(null);
            await api.commitDataEditorChanges(draft);
            await onSaved?.();
            const currentSessionId = api.getStoredSessionId();
            if (currentSessionId) {
                api.setStoredSessionId(currentSessionId);
            }
            await loadPage(1);

            setDraft(cloneDraft(EMPTY_DRAFT));
            setDraftHistory([]);
            setSelectedRows([]);
            setSelectedTrimColumns([]);
            setActiveCell(null);
            notify.success('Değişiklikler kaydedildi');
            return true;
        } catch (err) {
            const message = getErrorMessage(err, 'Veri düzenleme değişiklikleri kaydedilemedi');
            logger.error('Data editor save failed', err);
            setError(message);
            notify.error(err, 'Veri düzenleme değişiklikleri kaydedilemedi');
            return false;
        } finally {
            setIsSaving(false);
        }
    }, [columns, draft, getColumnDisplayName, loadPage, onSaved]);

    return {
        rows,
        columns,
        pageSize,
        totalRows,
        totalPages,
        loadedPages,
        hasMoreRows,
        error,
        isLoading,
        isLoadingMore,
        isSaving,
        draft,
        isDirty:
            draft.updatedCells.length > 0 ||
            draft.clearedCells.length > 0 ||
            draft.deletedRowIds.length > 0 ||
            draft.trimColumns.length > 0 ||
            draft.renamedColumns.length > 0,
        selectedRows,
        selectedTrimColumns,
        activeCell,
        setActiveCell,
        loadMoreRows,
        toggleRowSelection,
        replaceSelectedRows,
        toggleAllLoadedRows,
        updateCell,
        updateCells,
        renameColumn,
        renameColumns,
        getColumnDisplayName,
        clearCells,
        clearActiveCell,
        deleteSelectedRows,
        toggleTrimColumnSelection,
        applyTrimSelection,
        removeTrimColumn,
        undoLastChange,
        discardChanges,
        saveChanges,
        reloadPage: async () => loadPage(1),
    };
}

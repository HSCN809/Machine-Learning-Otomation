'use client';

import { useCallback, useEffect, useState } from 'react';
import {
    DataEditorCellRef,
    DataEditorDraft,
    DataEditorPageResponse,
} from '@/types/data-upload';
import * as api from '@/lib/api';

const EMPTY_DRAFT: DataEditorDraft = {
    updatedCells: [],
    clearedCells: [],
    deletedRowIds: [],
    trimColumns: [],
};

function cloneDraft(draft: DataEditorDraft): DataEditorDraft {
    return {
        updatedCells: draft.updatedCells.map((cell) => ({ ...cell })),
        clearedCells: draft.clearedCells.map((cell) => ({ ...cell })),
        deletedRowIds: [...draft.deletedRowIds],
        trimColumns: [...draft.trimColumns],
    };
}

function isSameCell(cell: DataEditorCellRef, rowId: number, column: string): boolean {
    return cell.rowId === rowId && cell.column === column;
}

function draftsEqual(left: DataEditorDraft, right: DataEditorDraft): boolean {
    return JSON.stringify(left) === JSON.stringify(right);
}

interface UseDataEditorOptions {
    onSaved?: () => Promise<void> | void;
}

interface UseDataEditorReturn {
    pageData: DataEditorPageResponse | null;
    page: number;
    pageSize: number;
    error: string | null;
    isLoading: boolean;
    isSaving: boolean;
    draft: DataEditorDraft;
    isDirty: boolean;
    selectedRows: number[];
    selectedTrimColumns: string[];
    activeCell: DataEditorCellRef | null;
    setPage: (page: number) => void;
    setActiveCell: (cell: DataEditorCellRef | null) => void;
    toggleRowSelection: (rowId: number) => void;
    toggleAllRowsOnPage: () => void;
    updateCell: (rowId: number, column: string, value: string) => void;
    clearActiveCell: () => void;
    deleteSelectedRows: () => void;
    restoreDeletedRow: (rowId: number) => void;
    toggleTrimColumnSelection: (column: string) => void;
    applyTrimSelection: () => void;
    removeTrimColumn: (column: string) => void;
    undoLastChange: () => void;
    discardChanges: () => void;
    saveChanges: () => Promise<boolean>;
    reloadPage: () => Promise<void>;
}

export function useDataEditor({ onSaved }: UseDataEditorOptions = {}): UseDataEditorReturn {
    const [pageData, setPageData] = useState<DataEditorPageResponse | null>(null);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(25);
    const [error, setError] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [isSaving, setIsSaving] = useState(false);
    const [draft, setDraft] = useState<DataEditorDraft>(EMPTY_DRAFT);
    const [, setDraftHistory] = useState<DataEditorDraft[]>([]);
    const [selectedRows, setSelectedRows] = useState<number[]>([]);
    const [selectedTrimColumns, setSelectedTrimColumns] = useState<string[]>([]);
    const [activeCell, setActiveCell] = useState<DataEditorCellRef | null>(null);

    const loadPage = useCallback(
        async (nextPage: number) => {
            try {
                setIsLoading(true);
                setError(null);
                const response = await api.getDataEditorPage(nextPage, pageSize);
                setPageData(response);
                if (response.page !== nextPage) {
                    setPage(response.page);
                }
            } catch (err) {
                console.error('Data editor page load error:', err);
                setError(err instanceof Error ? err.message : 'Veri düzenleyici yüklenemedi');
            } finally {
                setIsLoading(false);
            }
        },
        [pageSize]
    );

    useEffect(() => {
        loadPage(page);
    }, [loadPage, page]);

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

    const toggleRowSelection = useCallback((rowId: number) => {
        setSelectedRows((previousSelectedRows) =>
            previousSelectedRows.includes(rowId)
                ? previousSelectedRows.filter((value) => value !== rowId)
                : [...previousSelectedRows, rowId]
        );
    }, []);

    const toggleAllRowsOnPage = useCallback(() => {
        const currentRows = pageData?.rows ?? [];
        const currentRowIds = currentRows.map((row) => row.rowId);

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
    }, [pageData]);

    const updateCell = useCallback(
        (rowId: number, column: string, value: string) => {
            applyDraftChange((currentDraft) => {
                if (currentDraft.deletedRowIds.includes(rowId)) {
                    return currentDraft;
                }

                currentDraft.updatedCells = currentDraft.updatedCells.filter(
                    (cell) => !isSameCell(cell, rowId, column)
                );
                currentDraft.clearedCells = currentDraft.clearedCells.filter(
                    (cell) => !isSameCell(cell, rowId, column)
                );
                currentDraft.updatedCells.push({ rowId, column, value });
                return currentDraft;
            });
        },
        [applyDraftChange]
    );

    const clearActiveCell = useCallback(() => {
        if (!activeCell) {
            return;
        }

        applyDraftChange((currentDraft) => {
            if (currentDraft.deletedRowIds.includes(activeCell.rowId)) {
                return currentDraft;
            }

            currentDraft.updatedCells = currentDraft.updatedCells.filter(
                (cell) => !isSameCell(cell, activeCell.rowId, activeCell.column)
            );
            currentDraft.clearedCells = currentDraft.clearedCells.filter(
                (cell) => !isSameCell(cell, activeCell.rowId, activeCell.column)
            );
            currentDraft.clearedCells.push(activeCell);
            return currentDraft;
        });
    }, [activeCell, applyDraftChange]);

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

    const restoreDeletedRow = useCallback(
        (rowId: number) => {
            applyDraftChange((currentDraft) => {
                currentDraft.deletedRowIds = currentDraft.deletedRowIds.filter((value) => value !== rowId);
                return currentDraft;
            });
        },
        [applyDraftChange]
    );

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
            draft.trimColumns.length > 0;

        if (!isDirty) {
            return false;
        }

        try {
            setIsSaving(true);
            setError(null);
            await api.commitDataEditorChanges(draft);
            await loadPage(page);
            await onSaved?.();

            setDraft(cloneDraft(EMPTY_DRAFT));
            setDraftHistory([]);
            setSelectedRows([]);
            setSelectedTrimColumns([]);
            setActiveCell(null);
            return true;
        } catch (err) {
            console.error('Data editor save error:', err);
            setError(err instanceof Error ? err.message : 'Veri düzenleme değişiklikleri kaydedilemedi');
            return false;
        } finally {
            setIsSaving(false);
        }
    }, [draft, loadPage, onSaved, page]);

    return {
        pageData,
        page,
        pageSize,
        error,
        isLoading,
        isSaving,
        draft,
        isDirty:
            draft.updatedCells.length > 0 ||
            draft.clearedCells.length > 0 ||
            draft.deletedRowIds.length > 0 ||
            draft.trimColumns.length > 0,
        selectedRows,
        selectedTrimColumns,
        activeCell,
        setPage,
        setActiveCell,
        toggleRowSelection,
        toggleAllRowsOnPage,
        updateCell,
        clearActiveCell,
        deleteSelectedRows,
        restoreDeletedRow,
        toggleTrimColumnSelection,
        applyTrimSelection,
        removeTrimColumn,
        undoLastChange,
        discardChanges,
        saveChanges,
        reloadPage: async () => loadPage(page),
    };
}
